import json

with open("scripts/live_audit_results_42.json", "r", encoding="utf-8") as f:
    tests = json.load(f)

lines = []
lines.append("| ID | Method & Endpoint | Input Payload Preview | Expected Response | Actual Response | HTTP | Timestamp (UTC) | Verdict | Evidence |")
lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

for t in tests:
    evidence = t.get('evidence', '').replace('|', '\\|').replace('\n', ' ')
    input_prev = t.get('input_preview', '').replace('|', '\\|')
    expected = t.get('expected', '').replace('|', '\\|')
    actual = t.get('actual', '').replace('|', '\\|')
    lines.append(f"| **TEST-{t['test_id']:02d}** | `{t['method']} {t['endpoint']}` | {input_prev} | {expected} | {actual} | `{t['status_code']}` | `{t['timestamp'][:19]}Z` | **{t['verdict']}** | {evidence} |")

with open("scripts/audit_table.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Generated {len(tests)} table rows in scripts/audit_table.md")
