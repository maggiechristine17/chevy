"""Build content.json for the website from Chevy's saved entries.

Only entries with "Show on website" turned on are included. Links to entries that
aren't shown are dropped, and [[links]] to them in notes become plain text.
Usage: python3 make_content.py entries.json content.json
entries.json: {"projects": [...], "areas": [...], "pages": [...]} (each entry has an "id")
"""
import json, re, sys
src, dst = sys.argv[1], sys.argv[2]
data = json.load(open(src))
types = ["projects", "areas", "pages"]
shown = {t: [e for e in data.get(t, []) if e.get("public") is True] for t in types}
ids = {e["id"] for t in types for e in shown[t]}
titles = {(e.get("title") or "").strip().lower() for t in types for e in shown[t]}
wiki = re.compile(r"\[\[([^\[\]\n|]+)(?:\|([^\[\]\n]+))?\]\]")
def clean_body(body):
    def sub(m):
        title, alias = m.group(1).strip(), (m.group(2) or "").strip()
        return m.group(0) if title.lower() in titles else (alias or title)
    return wiki.sub(sub, body or "")
out = {}
for t in types:
    out[t] = []
    for e in shown[t]:
        e = dict(e)
        e["links"] = [x for x in e.get("links", []) if x in ids]
        if e.get("body"):
            e["body"] = clean_body(e["body"])
        out[t].append(e)
json.dump(out, open(dst, "w"), indent=2)
print({t: len(out[t]) for t in types})
