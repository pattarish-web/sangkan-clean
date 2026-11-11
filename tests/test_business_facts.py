import json
from pathlib import Path
import re
import unittest


class BusinessFactsTests(unittest.TestCase):
    def test_homepage_office_hours_and_legal_identity(self):
        text = Path('index.html').read_text(encoding='utf-8')
        graph = json.loads(re.search(
            r'<script type="application/ld\+json">(.*?)</script>', text, re.S
        ).group(1))['@graph']
        business = next(item for item in graph if item['@type'] == 'LocalBusiness')
        self.assertEqual(business['identifier'], '0105569168329')
        self.assertEqual(business['foundingDate'], '2026-09-06')
        self.assertEqual(len(business['openingHoursSpecification']['dayOfWeek']), 6)
        self.assertNotIn('Sunday', business['openingHoursSpecification']['dayOfWeek'])
        self.assertIn('24 ชั่วโมงตามนัดหมาย', text)

    def test_service_pages_disclose_exclusions(self):
        for name in ['index.html', 'landing-bigcleaning.html', 'landing-maid.html']:
            text = Path(name).read_text(encoding='utf-8')
            self.assertIn('ไม่รวมค่าอุปกรณ์และภาษี', text, name)
            self.assertNotIn('รวมค่าอุปกรณ์และน้ำยาทำความสะอาดแล้ว', text, name)
            self.assertEqual(len(re.findall(r'<h1\b', text)), 1, name)
            for source in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
                json.loads(source)

    def test_ai_documents_preserve_confirmed_facts(self):
        for name in ['llms.txt', 'agent/llms.txt', 'agent/llms-full.txt']:
            text = Path(name).read_text(encoding='utf-8')
            self.assertIn('0105569168329', text, name)
            self.assertIn('ไม่รวมค่าอุปกรณ์และภาษี', text, name)
            self.assertNotIn('ไม่ต้อง รวมในราคาแล้ว', text, name)


if __name__ == '__main__':
    unittest.main()
