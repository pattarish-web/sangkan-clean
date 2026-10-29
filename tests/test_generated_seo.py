import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

import build_blogs


class GeneratedSeoTests(unittest.TestCase):
    def test_all_sitemap_articles_have_one_h1_and_valid_faq(self):
        posts = {p['slug']: p for p in json.loads(Path('posts.json').read_text(encoding='utf-8'))}
        checked = 0
        for entry in ET.parse('sitemap-blog.xml').getroot():
            url = entry.find('{*}loc').text
            path = Path(unquote(urlparse(url).path).lstrip('/'))
            text = path.read_text(encoding='utf-8')
            self.assertEqual(len(re.findall(r'<h1\b', text, re.I)), 1, str(path))
            actual = []
            for block in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', text, re.I | re.S):
                data = json.loads(block)
                if data.get('@type') == 'FAQPage':
                    actual.append(data)
            expected = build_blogs.extract_faq_schema(posts[path.stem].get('content', ''))
            if expected:
                expected = json.loads(re.search(r'>(.*)</script>', expected, re.S).group(1))
                self.assertEqual(actual, [expected], str(path))
            else:
                self.assertEqual(actual, [], str(path))
            checked += 1
        self.assertEqual(checked, 313)

    def test_all_area_pages_are_service_areas(self):
        for path in Path('areas').glob('*.html'):
            text = path.read_text(encoding='utf-8')
            graph = json.loads(re.search(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', text, re.I | re.S).group(1))['@graph']
            service = graph[0]
            self.assertEqual(service['@type'], 'Service')
            self.assertEqual(service['provider']['@id'], 'https://www.sangkanclean.com/#business')
            self.assertNotIn('geo', service)

    def test_public_agent_documents_are_valid_and_current(self):
        for path in Path('agent').rglob('*.json'):
            json.loads(path.read_text(encoding='utf-8'))
        for path in Path('agent').rglob('*'):
            if path.suffix in {'.json', '.txt', '.md', '.html'}:
                self.assertNotIn('max(฿5,500, ฿4,000', path.read_text(encoding='utf-8'), str(path))


if __name__ == '__main__':
    unittest.main()
