const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const config = JSON.parse(fs.readFileSync('bigcleaning-pricing.json', 'utf8'));
const script = fs.readFileSync('script.js', 'utf8');
const literal = script.match(/const priceTiers = (\{[\s\S]*?\});/)[1];
assert.deepEqual(new Function('return (' + literal + ')')(), config.rates);
let guards = 0;
for (const f of fs.readdirSync('agent/_next/static/chunks').filter(f => f.endsWith('.js'))) {
  const code = fs.readFileSync(path.join('agent/_next/static/chunks', f), 'utf8');
  const exported = code.match(/"QuoteError",0,(\w+),"createQuote",0,(\w+)/);
  if (!exported) continue;
  const start = code.indexOf('function ' + exported[2] + '(e){');
  const prefix = code.slice(start).match(/^function \w+\(e\)\{(if\(e\.serviceId==="big-cleaning"\)throw new \w+\([^;]+;)/);
  assert.ok(prefix, 'Big Cleaning guard missing in ' + f);
  class QuoteError extends Error { constructor(message, status, code) { super(message); this.status=status; this.code=code; } }
  const guard = new Function(exported[1], 'return function(e){' + prefix[1] + '}')(QuoteError);
  assert.throws(() => guard({serviceId:'big-cleaning',areaSqm:200}), e => e.code==='property_type_required' && e.message.includes('https://www.sangkanclean.com/#calculator'));
  assert.doesNotThrow(() => guard({serviceId:'general-cleaning',areaSqm:200}));
  assert.ok(!code.includes('"big-cleaning":{base:4e3,perSqm:35,floor:5500'));
  guards++;
}
assert.equal(guards,3);
const formula=JSON.parse(fs.readFileSync('agent/api/v1/quotes.json','utf8')).formulas['big-cleaning'];
assert.deepEqual(formula.rates,config.rates);
assert.equal(formula.minimum,6000);
for(const f of ['agent/llms.txt','agent/llms-full.txt','agent/jsonld.json','agent/faq.json']){
  const txt=fs.readFileSync(f,'utf8');
  assert.ok(!txt.includes('max(฿5,500, ฿4,000'),f+' contains retired Big Cleaning formula');
}
console.log('PASS: public pricing matches marketing and AI metadata; 3 agent quote guards reject obsolete estimates and preserve other services.');
