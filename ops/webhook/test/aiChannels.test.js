import { test } from 'node:test';
import assert from 'node:assert/strict';
import { resolveLeadChannel } from '../src/lib/leadValidation.js';
import { SheetsLeadStore } from '../src/lib/sheetsLeadStore.js';
import { memoryLeadIo } from '../src/lib/leadSheetMap.js';
import { dashboardHtml } from '../src/modules/leads/dashboardHtml.js';
import { aiChannelOf } from '../src/lib/aiChannels.js';
import { readFileSync } from 'node:fs';

test('backend reclassifies legacy generic referrals without changing Ads', () => {
  assert.equal(resolveLeadChannel({channel:'referral',referrer:'claude.ai'}), 'claude');
  assert.equal(resolveLeadChannel({channel:'direct',referrer:'perplexity.ai'}), 'perplexity');
  assert.equal(resolveLeadChannel({channel:'chatgpt.com'}), 'chatgpt');
  assert.equal(resolveLeadChannel({channel:'gpt'}), 'chatgpt');
  assert.equal(resolveLeadChannel({utm_source:'gemini'}), 'gemini');
  assert.equal(resolveLeadChannel({channel:'referral',referrer:'copilot.microsoft.com',gclid:'AD'}), 'google_ads');
  assert.equal(resolveLeadChannel({channel:'facebook',referrer:'claude.ai'}), 'facebook');
  assert.equal(resolveLeadChannel({referrer:'bing.com'}), 'referral');
  assert.equal(resolveLeadChannel({referrer:'claude.ai.evil.example'}), 'referral');
});
test('Sheets report restores saved referrer for historical classification', async () => {
  const io = memoryLeadIo();
  await io.appendRow('leads', {id:'AI-TEST', channel:'referral'});
  await io.appendRow('lead_attribution', {lead_id:'AI-TEST', referrer:'claude.ai'});
  const store = new SheetsLeadStore(io);
  assert.equal((await store.list())[0].attribution.channel, 'claude');
  assert.equal((await store.list({channel:'claude'})).length, 1);
});
test('dashboard offers canonical labels and resolves historical rows', () => {
  const html = dashboardHtml();
  for(const label of ['ChatGPT','Claude','Perplexity','Gemini','Copilot']) assert.ok(html.includes(label),label);
  assert.ok(html.includes('resolveLeadChannel(attr, lead.gclid)'));
});
test('browser and tracking fallback contain the same AI classifier as backend', () => {
  for (const path of ['../../..' + '/attribution.js', '../../..' + '/tracking.js']) {
    const text = readFileSync(new URL(path, import.meta.url), 'utf8');
    assert.ok(text.includes(aiChannelOf.toString()));
  }
});
