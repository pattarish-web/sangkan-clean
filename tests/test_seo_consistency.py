import json
import re
import unittest
from pathlib import Path

import build_blogs
import update_sitemap
from scripts.sync_bigcleaning_pricing import validate_fixed_fields


class SeoConsistencyTests(unittest.TestCase):
    def test_faq_does_not_capture_article_or_cta(self):
        body = ('<h3>อุปกรณ์ที่ต้องเตรียม</h3><p>รายการอุปกรณ์ซักพรม</p>'
                '<h2>คำถามที่พบบ่อย (FAQ)</h2><h3>ต้องเตรียมอะไรบ้าง?</h3>'
                '<p>เตรียมข้อมูลขนาดพื้นที่ก่อนจอง</p>'
                '<section class="inline-cta"><h3>สนใจบริการทำความสะอาด?</h3>'
                '<p>ติดต่อทีมงานเพื่อประเมินราคา</p></section>')
        schema = build_blogs.extract_faq_schema(body)
        self.assertNotIn('อุปกรณ์ที่ต้องเตรียม', schema)
        self.assertNotIn('สนใจบริการทำความสะอาด?', schema)
        self.assertIn('ต้องเตรียมอะไรบ้าง?', schema)

    def test_explicit_qa_without_faq_heading_is_retained(self):
        schema = build_blogs.extract_faq_schema('<p><strong>Q: มีค่าเดินทางไหม?</strong><br>A: ประเมินตามระยะทางก่อนเริ่มงาน</p>')
        self.assertIn('มีค่าเดินทางไหม?', schema)

    def test_long_question_is_not_truncated_into_schema(self):
        schema = build_blogs.extract_faq_schema('<h2>FAQ</h2><h3>' + 'ก' * 210 + '</h3><p>คำตอบตัวอย่างสำหรับการตรวจ</p>')
        self.assertEqual(schema, '')

    def test_body_h1_is_demoted(self):
        html = build_blogs.article_body_content('<h1 class="title">หัวข้อ</h1><p>เนื้อหา</p>')
        self.assertNotIn('<h1', html)
        self.assertIn('<h2 class="title">หัวข้อ</h2>', html)

    def test_stable_lastmod_registry(self):
        self.assertEqual(update_sitemap.content_lastmod('example.html', {'example.html': '2026-08-04'}, '2026-07-01'), '2026-08-04')
        self.assertEqual(update_sitemap.content_lastmod('new.html', {}, '2026-07-01'), '2026-07-01')
        self.assertIsNone(update_sitemap.content_lastmod('unknown.html', {}, None))
        self.assertEqual(update_sitemap.content_lastmod('example.html', {'example.html': '2026-08-04'}, '2026-11-01'), '2026-11-01')

    def test_area_template_uses_service_not_fictional_branch(self):
        template = Path('local_template.html').read_text(encoding='utf-8')
        self.assertIn('"@type": "Service"', template)
        self.assertIn('"provider": { "@id": "{{site_url}}/#business" }', template)
        self.assertNotIn('"@type": "LocalBusiness"', template)

    def test_pricing_structure_changes_fail_before_materializing(self):
        data = json.loads(Path('bigcleaning-pricing.json').read_text(encoding='utf-8'))
        validate_fixed_fields(data)
        data['minimum'] = 7000
        with self.assertRaises(AssertionError):
            validate_fixed_fields(data)

    def test_future_article_upgrade_beats_registry_date(self):
        post = json.loads(Path('posts.json').read_text(encoding='utf-8'))[0]
        post['dateModified'] = '2026-11-01'
        _, rendered = build_blogs.render_blog_html([post], 0, '{{date_modified}}')
        self.assertEqual(rendered, '2026-11-01')


if __name__ == '__main__':
    unittest.main()
