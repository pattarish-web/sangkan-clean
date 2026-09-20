#!/usr/bin/env python3
"""Insert attribution.js + lead-form.js next to tracking.js without regenerating pages."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

REPLACEMENTS = [
    (
        '<script src="tracking.js"></script>',
        '<script>window.LEAD_API_URL=window.LEAD_API_URL||"https://sangkan-office-ops.onrender.com/api/leads";</script>\n'
        '    <script src="attribution.js"></script>\n'
        '    <script src="tracking.js"></script>\n'
        '    <script src="lead-form.js"></script>',
    ),
    (
        '<script src="../tracking.js"></script>',
        '<script>window.LEAD_API_URL=window.LEAD_API_URL||"https://sangkan-office-ops.onrender.com/api/leads";</script>\n'
        '    <script src="../attribution.js"></script>\n'
        '    <script src="../tracking.js"></script>\n'
        '    <script src="../lead-form.js"></script>',
    ),
]

REPLACE_RE = re.compile(
    r'location\.replace\((["\'])(https://www\.sangkanclean\.com/[^"\']+)\1\)'
)


def preserve_gclid(html: str) -> str:
    def repl(match):
        url = match.group(2)
        if "location.search" in match.group(0):
            return match.group(0)
        quote = match.group(1)
        return f"location.replace({quote}{url}{quote}+location.search+location.hash)"

    return REPLACE_RE.sub(repl, html)


def patch_file(path: Path) -> bool:
    html = path.read_text(encoding="utf-8")
    original = html
    if "attribution.js" not in html:
        for old, new in REPLACEMENTS:
            if old in html:
                html = html.replace(old, new)
                break
    html = preserve_gclid(html)
    if html != original:
        path.write_text(html, encoding="utf-8")
        return True
    return False


def main():
    changed = 0
    for path in ROOT.rglob("*.html"):
        if "node_modules" in path.parts or "ops" in path.parts:
            continue
        if patch_file(path):
            changed += 1
    print(f"updated {changed} html files")


if __name__ == "__main__":
    main()
