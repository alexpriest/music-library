#!/usr/bin/env python3
"""Merge enriched group files into the canonical data/library.json + validate.

Loads data/enriched/group-*.json, assembles the final library with stable song
IDs, validates every controlled-vocabulary field, and prints stats + violations.
"""
import json
import glob
import re
import sys
from collections import Counter, OrderedDict

MOODS = {
    "tender","romantic","intimate","sentimental","warm","longing",
    "melancholy","wistful","bittersweet","nostalgic","mournful","lonely","somber",
    "serene","peaceful","dreamy","contemplative","ethereal",
    "hopeful","uplifting","joyful","cheerful","playful","whimsical","jaunty",
    "triumphant","majestic","grand","dramatic","heroic","festive",
    "brooding","mysterious","dark","tense","haunting",
    "energetic","driving","lively","groovy","sultry",
    "spiritual","quirky","elegant","folksy","bluesy",
}
GENRES = {
    "Classical","Jazz Standard","Jazz","Ragtime","Pop","Rock","Singer-Songwriter",
    "Folk","Musical Theatre","Film/TV Score","Video Game","Children's","Holiday",
    "Great American Songbook","Latin/World","Wedding/Ceremonial","Religious",
    "New Age/Minimalist","Blues","Country","R&B/Soul",
}
ERAS = {
    "Baroque","Classical","Romantic","Impressionist","18th-Century","19th-Century",
    "20th-Century","Contemporary",
    "1900s","1910s","1920s","1930s","1940s","1950s","1960s","1970s","1980s",
    "1990s","2000s","2010s","2020s",
}
TEMPOS = {"very slow","slow","medium","upbeat","fast","very fast"}
DIFFS = {"beginner","easy","intermediate","advanced","virtuosic"}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


books = []
seen_ids = set()
for f in sorted(glob.glob("data/enriched/group-*.json")):
    data = json.load(open(f))
    for b in data["books"]:
        if b["id"] in seen_ids:
            print(f"WARN duplicate book id {b['id']} in {f}")
            continue
        seen_ids.add(b["id"])
        books.append(b)

books.sort(key=lambda b: b["title"].lower())


def _norm_title(t):
    return re.sub(r"\s+", " ", (t or "").strip().lower())


# Apply reshoot overrides (corrected/expanded song lists from rephotographed pages).
books_by_id = {b["id"]: b for b in books}
reshoot_files = sorted(glob.glob("data/reshoots/*.json"))
for f in reshoot_files:
    o = json.load(open(f))
    b = books_by_id.get(o["id"])
    if not b:
        print(f"WARN: reshoot override for unknown book id {o['id']}")
        continue
    if "songs" in o:  # title-only overrides omit "songs" and leave the list untouched
        new_songs = o["songs"]
        if o.get("mode") == "merge":
            seen = {_norm_title(s["title"]) for s in b.get("songs", [])}
            b["songs"] = b.get("songs", []) + [s for s in new_songs if _norm_title(s["title"]) not in seen]
        else:  # replace
            b["songs"] = new_songs
    for fld in ("title", "title_confidence", "identification_note", "title_suggestion"):
        if o.get(fld):
            b[fld] = o[fld]
    if o.get("title"):  # title resolved -> drop any now-stale suggestion
        b.pop("title_suggestion", None)
    if o.get("clear_flags"):
        b["flags"] = []
    b["reshot"] = True
print(f"Applied {len(reshoot_files)} reshoot override(s): {[json.load(open(f))['id'] for f in reshoot_files]}")

violations = []
mood_counter = Counter()
genre_counter = Counter()
era_counter = Counter()
total_songs = 0
song_conf = Counter()
book_conf = Counter()

for b in books:
    book_conf[b.get("title_confidence", "?")] += 1
    used_slugs = Counter()
    for s in b.get("songs", []):
        total_songs += 1
        base = slug(s.get("title", "untitled")) or "untitled"
        used_slugs[base] += 1
        sid = f"{b['id']}__{base}"
        if used_slugs[base] > 1:
            sid += f"-{used_slugs[base]}"
        s["song_id"] = sid
        # normalize pre-1900 decade eras to century buckets
        _era = s.get("era")
        if _era and re.match(r"^(17|18)\d0s$", _era):
            s["era"] = "18th-Century" if _era.startswith("17") else "19th-Century"
        # validate controlled fields
        for m in (s.get("mood_tags") or []):
            mood_counter[m] += 1
            if m not in MOODS:
                violations.append(f"{sid}: bad mood '{m}'")
        if s.get("genre") and s["genre"] not in GENRES:
            violations.append(f"{sid}: bad genre '{s['genre']}'")
        else:
            genre_counter[s.get("genre")] += 1
        if s.get("era") and s["era"] not in ERAS:
            violations.append(f"{sid}: bad era '{s['era']}'")
        else:
            era_counter[s.get("era")] += 1
        if s.get("tempo") and s["tempo"] not in TEMPOS:
            violations.append(f"{sid}: bad tempo '{s['tempo']}'")
        if s.get("difficulty") and s["difficulty"] not in DIFFS:
            violations.append(f"{sid}: bad difficulty '{s['difficulty']}'")
        e = s.get("energy")
        if e is not None and not (isinstance(e, int) and 1 <= e <= 5):
            violations.append(f"{sid}: bad energy '{e}'")
        song_conf[s.get("confidence", "?")] += 1
    b["song_count"] = len(b.get("songs", []))

library = OrderedDict()
library["title"] = "Alex's Sheet Music Library"
library["book_count"] = len(books)
library["song_count"] = total_songs
library["vocabulary"] = {
    "moods": sorted(MOODS), "genres": sorted(GENRES), "eras": sorted(ERAS),
    "tempos": sorted(TEMPOS), "difficulties": sorted(DIFFS),
}
library["books"] = books
json.dump(library, open("data/library.json", "w"), indent=2, ensure_ascii=False)

print(f"Books: {len(books)}   Songs: {total_songs}")
print(f"Vocab violations: {len(violations)}")
for v in violations[:40]:
    print("   ", v)
print(f"\nBook title confidence: {dict(book_conf)}")
print(f"Song tagging confidence: {dict(song_conf)}")
print(f"\nTop 15 moods: {mood_counter.most_common(15)}")
print(f"\nGenres: {genre_counter.most_common()}")
print(f"\nEras: {era_counter.most_common()}")
