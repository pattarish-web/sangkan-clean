"""Materialize the single public pricing document into marketing calculators."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def validate_fixed_fields(data):
    """Stop rather than silently drifting if pricing structure changes."""
    assert data['minimum'] == 6000, 'Update calculator minimum and docs before changing minimum'
    assert data['tierUpperBounds'] == [50, 100, 200, 300, 500, 1000], 'Update calculator tier boundaries and table headings'
    assert data['siteSurveyAboveSqm'] == 1000, 'Update survey logic across calculators'
    assert data['addons'] == {'carpetPerSqm': 30, 'sofaPerSeat': 500, 'ozoneStartingPrice': 1290}, 'Update add-on inputs, calculators and docs'
    assert list(data['rates']) == ['house', 'condo', 'office', 'factory']
    assert all(len(values) == 6 and all(isinstance(v, (int, float)) and v > 0 for v in values) for values in data['rates'].values())


def sync():
    data = json.loads((ROOT / 'bigcleaning-pricing.json').read_text(encoding='utf-8'))
    validate_fixed_fields(data)
    for name in ['script.js', 'landing-bigcleaning.html']:
        path = ROOT / name
        text = path.read_text(encoding='utf-8')
        for property_type, rates in data['rates'].items():
            values = ', '.join(str(v) for v in rates)
            if name == 'script.js':
                pattern = r'(' + property_type + r':\s*)\[[\d., ]+\]'
            else:
                pattern = r'(' + property_type + r':\s*\{\s*label:\s*\x27[^\x27]+\x27,\s*rates:\s*)\[[\d., ]+\]'
            text, count = re.subn(pattern, lambda m: m[1] + '[' + values + ']', text)
            assert count == 1, f'Pricing property missing or duplicated: {name}/{property_type}'
        if name.endswith('.html'):
            table = re.search(r'<table class="pricing-table">[\s\S]*?</table>', text).group(0)
            rows = list(re.finditer(r'<tr><th scope="row">.*?</tr>', table))
            assert len(rows) == 4
            for row, rates in zip(rows, data['rates'].values()):
                it = iter(rates)
                def cell(m):
                    rate = next(it)
                    return '<td>฿' + (f'{rate:.2f}' if rate % 1 else str(rate)) + '</td>'
                new_row, count = re.subn(r'<td>฿[\d.]+</td>', cell, row.group(0))
                assert count == 6
                text = text.replace(row.group(0), new_row, 1)
        path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    sync()
