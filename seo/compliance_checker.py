# seo/compliance_checker.py
"""
Compliance & Ethics Checker
- Uses OpenAI Moderation API (simulated) to detect prohibited content.
- Applies PDPA regex masking for personal data patterns.
- Checks for prohibited topics defined in `compliance_rules.json`.
- Generates `seo/compliance_report.md` summarizing any violations.
- Returns exit code 0 if all clear, else non‑zero to stop CI.
"""
import json
import os
import re
import sys
from pathlib import Path

# Load rules
with open("seo/compliance_rules.json", "r", encoding="utf-8") as f:
    rules = json.load(f)

prohibited_topics = [t.lower() for t in rules.get("prohibited_topics", [])]
pdpa_patterns = [re.compile(p) for p in rules.get("pdpa", {}).get("personal_data_patterns", [])]
mask = rules.get("pdpa", {}).get("mask_placeholder", "[REDACTED]")

report_lines = []
violations = False

posts_dir = Path("posts")
for md_file in posts_dir.glob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    lowered = content.lower()
    # Topic check
    for topic in prohibited_topics:
        if topic in lowered:
            violations = True
            report_lines.append(f"- **Prohibited topic** `{topic}` found in `{md_file.name}`")
    # PDPA check – mask personal data
    for pat in pdpa_patterns:
        for match in pat.findall(content):
            violations = True
            report_lines.append(f"- **PDPA violation** personal data `{match}` in `{md_file.name}` (masked)")
            # simple masking in file
            new_content = content.replace(match, mask)
            md_file.write_text(new_content, encoding="utf-8")
    # Simulated moderation (simple keyword list)
    # In a real implementation call OpenAI Moderation API here.
    moderation_flags = []
    if "hate" in lowered:
        moderation_flags.append("hate")
    if moderation_flags:
        violations = True
        report_lines.append(f"- **Moderation flags** {', '.join(moderation_flags)} in `{md_file.name}`")

# Write report
report_path = Path("seo/compliance_report.md")
if violations:
    report_path.write_text("# Compliance Report – Issues Detected\n\n" + "\n".join(report_lines), encoding="utf-8")
    print("Compliance violations found. See seo/compliance_report.md")
    sys.exit(1)
else:
    report_path.write_text("# Compliance Report – All Clear\n\nNo violations detected.", encoding="utf-8")
    print("Compliance check passed.")
    sys.exit(0)
