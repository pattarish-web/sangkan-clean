"""Synchronize the static agent export with public Big Cleaning pricing.

No customer/lead endpoint is read: quotes.json is the tracked public formula
configuration. The Next source is not in this repository, so guard exported
calculators which cannot ask for a property type. Re-run after replacing the
agent export; tests must fail if upstream changes the compiled entry points.
"""
import html
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.sync_bigcleaning_pricing import validate_fixed_fields
CALCULATOR = 'https://www.sangkanclean.com/#calculator'
MESSAGE = 'Big Cleaning ต้องเลือกประเภทสถานที่ กรุณาคำนวณราคาใหม่ที่ ' + CALCULATOR + ' หรือ LINE @sangkanclean'


def sync():
    pricing = json.loads((ROOT / 'bigcleaning-pricing.json').read_text(encoding='utf-8'))
    validate_fixed_fields(pricing)
    table = '\n'.join('- ' + name + ': ' + ', '.join(str(rate) for rate in rates) + ' บาท/ตร.ม.' for name, rates in pricing['rates'].items())
    section = ('Big Cleaning: ค่าบริการ = max(6,000 บาท, พื้นที่ × อัตราตามประเภทสถานที่และช่วงพื้นที่)\n'
               'ช่วงพื้นที่: ไม่เกิน 50, 51–100, 101–200, 201–300, 301–500, 501–1,000 ตร.ม.\n'
               + table + '\nเกิน 1,000 ตร.ม. ประเมินหน้างาน ไม่เสนอราคาตายตัว\n'
               'ซักพรมเพิ่ม 30 บาท/ตร.ม.; ซักโซฟาเพิ่ม 500 บาท/ที่นั่ง; โอโซนพร้อม Big Cleaning เริ่ม 1,290 บาท\n'
               'ข้อมูลราคา: https://www.sangkanclean.com/bigcleaning-pricing.json\n'
               'เครื่องคำนวณ: ' + CALCULATOR)
    for filename in ['agent/llms.txt', 'agent/llms-full.txt']:
        path = ROOT / filename
        text = path.read_text(encoding='utf-8')
        text = re.sub(r'^- (?:Big Cleaning|big-cleaning):?\s*=?.*$', '', text, flags=re.M)
        text = text.replace('- Big Cleaning ≥ 400 ตร.ม. ต้องสำรวจหน้างาน', '- Big Cleaning เกิน 1,000 ตร.ม. ต้องประเมินหน้างาน')
        text = text.replace('สูตรราคาตรงเว็บจริง (script.js):', 'ข้อมูลบริการอื่น (ตรวจสอบกับหน้าบริการก่อนยืนยันราคา):')
        text = text.split('\n## Big Cleaning pricing — current')[0].rstrip()
        text = re.sub(r'\n## Example agent flow\n[\s\S]*?(?=\n## |\Z)', '\n## Example agent flow\n\nBig Cleaning: เปิดเครื่องคำนวณหน้าแรก เลือกประเภทสถานที่และพื้นที่ แล้วติดต่อ LINE เพื่อยืนยันราคา\n', text)
        text += '\n\n## Big Cleaning pricing — current\n\n' + section + '\n\nแบบฟอร์มเอเจนต์เดิมยังไม่รองรับประเภทสถานที่ จึงไม่ออกใบประเมิน Big Cleaning; ใช้เครื่องคำนวณข้างต้นหรือให้เจ้าหน้าที่ประเมิน\n'
        path.write_text(text, encoding='utf-8')
    markdown = '# Big Cleaning\n\nทำความสะอาดเชิงลึก จำนวนทีมและระยะเวลาประเมินตามหน้างาน\n\n' + section + '\n\nตัวอย่าง: บ้าน 200 ตร.ม. × 70 = 14,000 บาท ก่อนบริการเสริม\n\nจอง/ยืนยันราคา: LINE @sangkanclean · 092-914-9978 / 080-694-1998\n'
    (ROOT / 'agent/md/big-cleaning.md').write_text(markdown, encoding='utf-8')
    (ROOT / 'agent/md/big-cleaning/index.html').write_text('<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Big Cleaning ราคาเบื้องต้น | Sangkan Clean</title><link rel="canonical" href="https://www.sangkanclean.com/landing-bigcleaning.html"></head><body><pre>' + html.escape(markdown) + '</pre><p><a href="' + CALCULATOR + '">เลือกประเภทสถานที่และคำนวณราคา</a></p></body></html>', encoding='utf-8')
    # This tracked file is a formula document, not customer quotes.
    path = ROOT / 'agent/api/v1/quotes.json'
    config = json.loads(path.read_text(encoding='utf-8'))
    config['formulas']['big-cleaning'] = {**pricing, 'expression': 'max(minimum, areaSqm * rates[propertyType][tierIndex])', 'sourceUrl': 'https://www.sangkanclean.com/bigcleaning-pricing.json'}
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for name in ['agent/api/v1/services.json', 'agent/api/v1/services/index.json']:
        path = ROOT / name
        data = json.loads(path.read_text(encoding='utf-8'))
        for service in data['services']:
            if service['id'] == 'big-cleaning':
                service.update(startingPrice=6000, requiresSiteSurveyAboveSqm=1000, requiresPropertyType=True, calculatorUrl=CALCULATOR, bookableByAgent=False)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    guarded = 0
    for path in (ROOT / 'agent/_next/static/chunks').glob('*.js'):
        text = path.read_text(encoding='utf-8')
        exports = re.search(r'"QuoteError",0,(\w+),"createQuote",0,(\w+)', text)
        if exports:
            error, function = exports.groups()
            needle = 'function ' + function + '(e){'
            guard = 'if(e.serviceId==="big-cleaning")throw new ' + error + '(' + json.dumps(MESSAGE, ensure_ascii=False) + ',422,"property_type_required");'
            if guard not in text:
                assert text.count(needle) == 1, 'Changed compiled quote entry point: ' + str(path)
                text = text.replace(needle, needle + guard, 1)
            # Remove the retired numeric formula; the early guard owns this service.
            text = text.replace('"big-cleaning":{base:4e3,perSqm:35,floor:5500,teamSize:3,sqmPerHour:35},', '')
            guarded += 1
        text = text.replace('startingPrice:5500', 'startingPrice:6000')
        text = text.replace('requiresSiteSurveyAboveSqm:400,', 'requiresSiteSurveyAboveSqm:1000,')
        if text != path.read_text(encoding='utf-8'):
            path.write_text(text, encoding='utf-8')
    assert guarded == 3, 'Unexpected exported calculator count; review new agent export'
    # Service cards appear in HTML and React server-component snapshots.
    for path in (ROOT / 'agent').rglob('*'):
        if path.suffix not in {'.html', '.txt', '.json'} or path.name.startswith('llms') or path == ROOT / 'agent/api/v1/quotes.json':
            continue
        text = path.read_text(encoding='utf-8')
        changed = text.replace('Big Cleaning เริ่ม ฿5,500', 'Big Cleaning เริ่ม ฿6,000')
        changed = changed.replace('เริ่มต้น <!-- -->฿5,500', 'เริ่มต้น <!-- -->฿6,000')
        changed = re.sub(r'max\(฿5,500, ฿4,000 \+ ฿35(?: × ตร\.ม\.|/ตร\.ม\.)\)(?: ทีม 3 คน)?', 'ขั้นต่ำ 6,000 บาท ตามประเภทสถานที่และช่วงพื้นที่ ดู bigcleaning-pricing.json', changed)
        changed = re.sub(r'("price"\s*:\s*)5500\b', r'\g<1>6000', changed).replace('\\"price\\":5500', '\\"price\\":6000')
        changed = changed.replace('"startingPrice":5500', '"startingPrice":6000').replace('\\"startingPrice\\":5500', '\\"startingPrice\\":6000')
        changed = changed.replace('"requiresSiteSurveyAboveSqm":400', '"requiresSiteSurveyAboveSqm":1000').replace('\\"requiresSiteSurveyAboveSqm\\":400', '\\"requiresSiteSurveyAboveSqm\\":1000')
        if changed != text:
            path.write_text(changed, encoding='utf-8')
    print('Synchronized public Big Cleaning pricing and guarded 3 property-less agent calculator bundles.')


if __name__ == '__main__':
    sync()
