#!/usr/bin/env python3
"""Generate LIBRARY.md — a human-readable QC index of the catalog."""
import json
from collections import Counter, defaultdict

lib = json.load(open("data/library.json"))
books = lib["books"]

lines = []
W = lines.append

W(f"# {lib['title']}\n")
W(f"**{lib['book_count']} books · {lib['song_count']} songs** — searchable by mood, "
  "genre, era, composer, tempo, energy, and difficulty.\n")
W("Generated from photos of the physical collection. The JSON source of truth is "
  "`data/library.json`; the MCP server queries it.\n")

# --- Needs attention -------------------------------------------------------
flagged = [b for b in books if b.get("flags")]
suggested = [b for b in books if b.get("title_suggestion")]

W("\n## ⚠️ Needs a reshoot or confirmation\n")
W("These books have incomplete data or an unconfirmed title. Everything else is "
  "solid. Reshoot the noted pages straight-on (avoid glare/rotation) to fill gaps.\n")
W("| Book | Issue |")
W("|------|-------|")
for b in sorted(flagged, key=lambda b: b["title"].lower()):
    issues = "; ".join(b["flags"])
    W(f"| **{b['title']}** | {issues} |")

W("\n### Suggested title identifications\n")
W("Agents identified these from the song lists/tracklists. Confirm and I'll update "
  "the catalog titles.\n")
W("| Current title | Suggested actual edition |")
W("|------|------|")
for b in sorted(suggested, key=lambda b: b["title"].lower()):
    W(f"| {b['title']} | **{b['title_suggestion']}** |")

# --- Catalog ---------------------------------------------------------------
W("\n## Full catalog\n")
by_genre = defaultdict(list)
for b in books:
    genres = Counter(s.get("genre") for s in b["songs"] if s.get("genre"))
    top = genres.most_common(1)[0][0] if genres else "Other"
    by_genre[top].append(b)

for genre in sorted(by_genre):
    W(f"\n### {genre}\n")
    for b in sorted(by_genre[genre], key=lambda b: b["title"].lower()):
        bits = []
        if b.get("composer"):
            bits.append(b["composer"])
        if b.get("series"):
            bits.append(b["series"])
        if b.get("instrumentation"):
            bits.append(b["instrumentation"])
        meta = " · ".join(bits)
        conf = "" if b["title_confidence"] == "confident" else f" _({b['title_confidence']})_"
        loose = " 〔loose sheet〕" if b.get("is_loose_sheet") else ""
        W(f"- **{b['title']}**{conf}{loose} — {b['song_count']} songs"
          + (f"  · {meta}" if meta else ""))

W("\n---\n")
W("_Tagging confidence across all songs: "
  + ", ".join(f"{n} {c}" for c, n in
              Counter(s.get("confidence") for b in books for s in b["songs"]).most_common())
  + "._")

open("LIBRARY.md", "w").write("\n".join(lines))
print(f"Wrote LIBRARY.md — {len(flagged)} flagged books, {len(suggested)} title suggestions")
