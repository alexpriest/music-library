#!/usr/bin/env python3
"""Group raw per-photo extractions into canonical book records.

Reads data/raw/batch-*.json (per-photo transcriptions) and applies an explicit
photo->book grouping map (built from shelf order + identity analysis) to produce
data/books.json: one record per physical book or loose sheet, with merged song
lists, confidence flags, and QC notes. Pure structuring — no enrichment here.
"""
import json
import glob
import re
from collections import OrderedDict

# --- Load raw photos -------------------------------------------------------
photos = {}
for b in sorted(glob.glob("data/raw/batch-*.json")):
    for p in json.load(open(b))["photos"]:
        photos[p["photo"]] = p


def P(n):
    return f"IMG_{n}.jpeg"


# --- The grouping map ------------------------------------------------------
# Each book: id, title, confidence, optional composer, song_photos (pull songs
# from these), photos (all source photos), flags, fill_canonical.
# confidence: "confident" | "probable" | "uncertain"
# fill_canonical: enrichment should complete/verify the full song list (used for
#   well-known classical sets whose contents page was blank/illegible).
BOOKS = [
    dict(id="cocktail-jazz", title="Cocktail Jazz", confidence="confident",
         song_photos=[5388], photos=[5387, 5388]),
    dict(id="library-of-disney-songs", title="The Library of Disney Songs", confidence="confident",
         song_photos=[5390], photos=[5389, 5390],
         flags=["Only ~7 of many songs captured — contents page low-res. Reshoot for full list."]),
    dict(id="definitive-vince-guaraldi", title="The Definitive Vince Guaraldi", confidence="confident",
         song_photos=[5391], photos=[5391]),
    dict(id="cowboy-bebop", title="Cowboy Bebop (Piano Score)", confidence="confident",
         song_photos=[5392], photos=[5392]),
    dict(id="super-mario-series-for-piano", title="Super Mario Series for Piano", confidence="confident",
         song_photos=[5393], photos=[5393],
         flags=["Only ~12 songs captured — dense two-column contents, low-res. Reshoot for full list."]),
    dict(id="field-18-nocturnes", title="Field: Eighteen Nocturnes for the Piano", confidence="confident",
         composer="John Field", song_photos=[], photos=[5394], fill_canonical=True,
         flags=["Cover only; no contents captured. Canonical 18 nocturnes to be filled in enrichment."]),
    dict(id="hoagy-carmichael", title="Hoagy Carmichael", confidence="probable",
         song_photos=[5395], photos=[5395],
         flags=["Contents shot sideways/low-res — partial song list."]),
    dict(id="encanto", title="Encanto", confidence="confident",
         song_photos=[5397], photos=[5396, 5397]),
    dict(id="yann-tiersen-piano-works", title="Yann Tiersen: Piano Works 1994–2003", confidence="confident",
         composer="Yann Tiersen", song_photos=[5399], photos=[5398, 5399]),
    dict(id="randy-newman-anthology", title="Randy Newman Anthology", confidence="confident",
         song_photos=[5580], photos=[5579, 5580],
         flags=["Back-cover song list has no page numbers."]),
    dict(id="yann-tiersen-eusa", title="Yann Tiersen: EUSA", confidence="confident",
         composer="Yann Tiersen", song_photos=[5582], photos=[5581, 5582]),
    dict(id="philip-glass-piano-collection", title="Philip Glass: The Piano Collection", confidence="confident",
         composer="Philip Glass", song_photos=[5583], photos=[5583]),
    dict(id="raffi-songbook", title="Raffi Songbook", confidence="uncertain",
         song_photos=[5584], photos=[5584],
         flags=["Title inferred from facing book (likely a Raffi collection). No page numbers. Confirm title."]),
    dict(id="queen-songbook", title="Queen (Songbook)", confidence="uncertain",
         song_photos=[5585], photos=[5585],
         flags=["Only back-cover song list seen; specific book title unknown. No page numbers."]),
    dict(id="gershwin-rhapsody-in-blue", title="Rhapsody in Blue", confidence="confident",
         composer="George Gershwin", song_photos=[5586], photos=[5586]),
    # --- Scott Joplin loose ragtime sheets ---
    dict(id="joplin-maple-leaf-rag", title="Maple Leaf Rag", confidence="confident",
         composer="Scott Joplin", song_photos=[5587], photos=[5587], loose=True),
    dict(id="joplin-easy-winners", title="The Easy Winners", confidence="confident",
         composer="Scott Joplin", song_photos=[5588], photos=[5588], loose=True),
    dict(id="joplin-entertainer", title="The Entertainer", confidence="confident",
         composer="Scott Joplin", song_photos=[5589], photos=[5589], loose=True),
    dict(id="joplin-sunflower-slow-drag", title="Sunflower Slow Drag", confidence="confident",
         composer="Scott Joplin & Scott Hayden", song_photos=[5590], photos=[5590], loose=True),
    dict(id="joplin-elite-syncopations", title="Elite Syncopations", confidence="confident",
         composer="Scott Joplin", song_photos=[5591], photos=[5591], loose=True),
    dict(id="joplin-chrysanthemum", title="The Chrysanthemum", confidence="confident",
         composer="Scott Joplin", song_photos=[5592], photos=[5592], loose=True),
    dict(id="phantom-of-the-opera", title="The Phantom of the Opera (Songbook)", confidence="probable",
         song_photos=[5593], photos=[5593],
         flags=["Identified from cover artwork; no title text on page. No page numbers."]),
    dict(id="star-wars", title="Star Wars (Trilogy Songbook)", confidence="probable",
         song_photos=[5594], photos=[5594],
         flags=["Back cover groups themes by film; specific book title not captured."]),
    dict(id="cats-memory", title="Memory (from Cats)", confidence="confident",
         song_photos=[5595], photos=[5595], loose=True),
    dict(id="elton-john-songbook", title="Elton John (Songbook)", confidence="uncertain",
         composer="Elton John", song_photos=[5596], photos=[5596, 5597],
         flags=["Only back-cover song list seen; specific book title unknown."]),
    dict(id="john-denver-songbook", title="John Denver (Songbook)", confidence="uncertain",
         composer="John Denver", song_photos=[5598], photos=[5598],
         flags=["Only back-cover song list seen; specific book title unknown."]),
    dict(id="eagles-songbook", title="Eagles (Songbook)", confidence="uncertain",
         composer="Eagles", song_photos=[5599], photos=[5599],
         flags=["Specific book title unknown; contents low-res so page numbers missing."]),
    dict(id="shins-wincing", title="The Shins: Wincing the Night Away", confidence="confident",
         composer="The Shins", song_photos=[5600], photos=[5600],
         flags=["Identified by tracklist; back-cover list, no page numbers."]),
    dict(id="rainbow-connection", title="The Rainbow Connection", confidence="confident",
         song_photos=[5601], photos=[5601], loose=True),
    dict(id="raindrops-keep-fallin", title="Raindrops Keep Fallin' on My Head", confidence="confident",
         song_photos=[5602], photos=[5602], loose=True),
    dict(id="hamilton", title="Hamilton", confidence="confident",
         song_photos=[5603], photos=[5603]),
    dict(id="disney-recital-suites", title="Disney Recital Suites (The Phillip Keveren Series)", confidence="confident",
         song_photos=[5604], photos=[5604]),
    dict(id="philip-glass-solo-piano", title="Philip Glass: Solo Piano", confidence="confident",
         composer="Philip Glass", song_photos=[5605], photos=[5605]),
    dict(id="sesame-street-songbook", title="The Sesame Street Songbook", confidence="confident",
         song_photos=[5606], photos=[5606]),
    dict(id="o-brother-where-art-thou", title="O Brother, Where Art Thou? (Soundtrack)", confidence="probable",
         song_photos=[5607], photos=[5607],
         flags=["Identified from song list; no title text on page."]),
    dict(id="disney-pixar-soul", title="Soul (Disney·Pixar)", confidence="confident",
         song_photos=[5608], photos=[5608]),
    dict(id="taylor-swift-midnights", title="Taylor Swift: Midnights", confidence="probable",
         composer="Taylor Swift", song_photos=[5609], photos=[5609],
         flags=["Identified from tracklist; no title text on page."]),
    dict(id="james-bond-songbook", title="James Bond: 26 Songs from 24 Films", confidence="probable",
         song_photos=[5610], photos=[5610],
         flags=["Back-cover header; exact book title not captured."]),
    dict(id="bach-two-part-inventions-alfred", title="J.S. Bach: Two-Part Inventions (Alfred / Palmer)", confidence="confident",
         composer="J.S. Bach", song_photos=[], photos=[5611], fill_canonical=True,
         flags=["Cover only. Canonical 15 Two-Part Inventions (BWV 772–786) to be filled in enrichment."]),
    dict(id="burgmuller-op105", title="Burgmüller: 12 Brilliant and Melodious Studies, Op. 105", confidence="confident",
         composer="Friedrich Burgmüller", song_photos=[5612], photos=[5612]),
    dict(id="grieg-album", title="Grieg: Album of Selected Piano Works", confidence="uncertain",
         composer="Edvard Grieg", song_photos=[5613], photos=[5613],
         flags=["Alphabetical-index page; exact edition/title unknown. All-Grieg (Lyric Pieces, Peer Gynt, etc.)."]),
    dict(id="bernstein-birds", title="Birds", confidence="confident",
         composer="Seymour Bernstein", song_photos=[5614], photos=[5614]),
    dict(id="bach-two-three-part-kalmus", title="J.S. Bach: Two and Three-Part Inventions (Kalmus / Bischoff)", confidence="confident",
         composer="J.S. Bach", song_photos=[], photos=[5615], fill_canonical=True,
         flags=["Cover only. Canonical 15 Inventions + 15 Sinfonias to be filled in enrichment."]),
    dict(id="bach-two-three-part-schirmer", title="Bach: Two- and Three-Part Inventions (Schirmer, Vol. 813)", confidence="confident",
         composer="J.S. Bach", song_photos=[], photos=[5616], fill_canonical=True,
         flags=["Cover only. Canonical 15 Inventions + 15 Sinfonias to be filled in enrichment."]),
    dict(id="liszt-selected-hinson", title="Franz Liszt: Selected Intermediate to Early Advanced Piano Solos", confidence="confident",
         composer="Franz Liszt", song_photos=[5617], photos=[5617],
         flags=["Contents low-res; page numbers missing."]),
    dict(id="scarlatti-selected-sonatas", title="Scarlatti: Selected Sonatas for the Piano (Alfred / Hinson)", confidence="confident",
         composer="Domenico Scarlatti", song_photos=[5619], photos=[5618, 5619]),
    dict(id="mozart-21-popular", title="Mozart: 21 of His Most Popular Pieces", confidence="confident",
         composer="W.A. Mozart", song_photos=[5620], photos=[5620]),
    dict(id="schumann-scenes-childhood", title="Schumann: Scenes from Childhood, Op. 15", confidence="confident",
         composer="Robert Schumann", song_photos=[5621], photos=[5621]),
    dict(id="chopin-19-popular", title="Chopin: 19 of His Most Popular Piano Selections", confidence="confident",
         composer="Frédéric Chopin", song_photos=[5622], photos=[5622]),
    dict(id="cage-piano-works-v3", title="John Cage: Piano Works 1935–48, Volume 3", confidence="confident",
         composer="John Cage", song_photos=[5623], photos=[5623]),
    dict(id="debussy-selected-favorites", title="Debussy: Selected Favorites for the Piano (Alfred)", confidence="confident",
         composer="Claude Debussy", song_photos=[5624], photos=[5624]),
    dict(id="debussy-childrens-corner", title="Debussy: Children's Corner (Alfred / Hinson)", confidence="confident",
         composer="Claude Debussy", song_photos=[5625], photos=[5625]),
    dict(id="satie-piano-works", title="Satie: Piano Works (Collection)", confidence="uncertain",
         composer="Erik Satie", song_photos=[5626, 5627], photos=[5626, 5627],
         flags=["Comprehensive Satie collection; exact edition/title not captured."]),
    dict(id="gershwin-complete-preludes", title="The Complete Gershwin Preludes for Piano", confidence="confident",
         composer="George Gershwin", song_photos=[5628], photos=[5628]),
    dict(id="granados-valses-poeticos", title="Granados: Valses Poéticos", confidence="confident",
         composer="Enrique Granados", song_photos=[5629], photos=[5629]),
    dict(id="schubert-moments-impromptus", title="Schubert: Moments Musicaux, Op. 94 & Impromptus, Opp. 90, 142", confidence="confident",
         composer="Franz Schubert", song_photos=[], photos=[5630], fill_canonical=True,
         flags=["Cover only. Canonical 6 Moments Musicaux + 8 Impromptus to be filled in enrichment."]),
    dict(id="ravel-piano-masterpieces", title="Ravel: Piano Masterpieces (Collection)", confidence="probable",
         composer="Maurice Ravel", song_photos=[5631], photos=[5631],
         flags=["Dover-style collection; exact title not captured. Contents low-res."]),
    dict(id="chopin-schirmer", title="Chopin: Compositions for the Piano (Schirmer's Library)", confidence="uncertain",
         composer="Frédéric Chopin", song_photos=[], photos=[5632], fill_canonical=True,
         flags=["Photographed page is the Schirmer Chopin SERIES catalog, not this volume's contents. Reshoot the actual contents."]),
    dict(id="liszt-liebestraume", title="Liszt: Liebesträume — Drei Notturnos (Henle Urtext)", confidence="confident",
         composer="Franz Liszt", song_photos=[], photos=[5633], fill_canonical=True,
         flags=["Cover only. Three Liebesträume to be filled in enrichment."]),
    dict(id="debussy-clair-de-lune", title="Debussy: Clair de Lune (Alfred / Palmer)", confidence="confident",
         composer="Claude Debussy", song_photos=[], photos=[5634], fill_canonical=True,
         flags=["Cover only. Confirm whether single piece or full Suite Bergamasque."]),
    dict(id="liszt-21-short-pieces", title="Liszt: 21 Short Piano Pieces (Dover)", confidence="confident",
         composer="Franz Liszt", song_photos=[5635], photos=[5635]),
    dict(id="mendelssohn-songs-without-words", title="Mendelssohn: Songs Without Words (Complete, Alfred / Hinson)", confidence="confident",
         composer="Felix Mendelssohn", song_photos=[], photos=[5636, 5637], fill_canonical=True,
         flags=["Cover only. Canonical 48 Songs Without Words to be filled in enrichment."]),
    dict(id="debussy-japanese-collection", title="Debussy: Piano Collection (Japanese Edition)", confidence="probable",
         composer="Claude Debussy", song_photos=[5638], photos=[5638],
         flags=["Japanese-edition Debussy collection; exact title not captured."]),
    dict(id="yann-tiersen-kerber", title="Yann Tiersen: Kerber", confidence="confident",
         composer="Yann Tiersen", song_photos=[5639], photos=[5639],
         flags=["Identified by tracklist."]),
    dict(id="philip-glass-complete-etudes", title="Philip Glass: The Complete Piano Etudes", confidence="confident",
         composer="Philip Glass", song_photos=[5641], photos=[5640, 5641]),
    dict(id="library-of-piano-favorites", title="The Library of Piano Favorites", confidence="confident",
         song_photos=[5642], photos=[5642, 5643],
         flags=["Contents shot upside-down/low-res — NO songs captured. Reshoot contents pages."]),
    dict(id="smta-mezzo-belter-v1", title="The Singer's Musical Theatre Anthology — Mezzo-Soprano/Belter, Vol. 1", confidence="probable",
         song_photos=[5644], photos=[5644]),
    dict(id="smta-mezzo-belter-v2", title="The Singer's Musical Theatre Anthology — Mezzo-Soprano/Belter, Vol. 2", confidence="probable",
         song_photos=[5645], photos=[5645]),
    dict(id="smta-volume-unconfirmed", title="The Singer's Musical Theatre Anthology — (Volume Unconfirmed)", confidence="uncertain",
         song_photos=[5646], photos=[5646],
         flags=["Contents page from an SMTA volume; which voice type/volume unconfirmed (may continue Vol. 2)."]),
    dict(id="100-all-time-popular-hits", title="100 All-Time Popular Hits", confidence="confident",
         song_photos=[5648], photos=[5647, 5648],
         flags=["Only the A–J contents column captured (~47 of 100). Reshoot remaining contents pages."]),
    dict(id="joy-of-wedding-music", title="The Joy of Wedding Music", confidence="confident",
         arranger="Denes Agay", song_photos=[5650], photos=[5649, 5650]),
    dict(id="60s-countdown", title="60s Countdown", confidence="confident",
         song_photos=[5652], photos=[5651, 5652]),
    dict(id="59-piano-solos", title="59 Piano Solos You Like to Play", confidence="confident",
         song_photos=[5654], photos=[5653, 5654]),
    dict(id="hall-of-fame-artists-hits", title="Hall of Fame: Artists & Their Hits", confidence="probable",
         song_photos=[5656], photos=[5655, 5656],
         flags=["Cover (5655) + contents/artist-index (5656) grouped as one book."]),
    dict(id="best-love-songs-ever", title="The Best Love Songs Ever", confidence="confident",
         song_photos=[5658], photos=[5657, 5658]),
    dict(id="great-big-book-childrens-songs", title="The Great Big Book of Children's Songs", confidence="confident",
         song_photos=[5660], photos=[5659, 5660]),
    dict(id="boogie-fun-for-piano", title="Boogie Fun for the Piano", confidence="confident",
         composer="Hazel Martin", song_photos=[5661], photos=[5661]),
    # --- Villa-Lobos: Guia Pratico loose sheets ---
    dict(id="villalobos-a-mare-encheu", title="A maré encheu (Nº 76)", confidence="confident",
         composer="Heitor Villa-Lobos", song_photos=[5662], photos=[5662], loose=True),
    dict(id="villalobos-acordei-de-madrugada", title="Acordei de madrugada (Nº 9)", confidence="confident",
         composer="Heitor Villa-Lobos", song_photos=[5663], photos=[5663], loose=True),
    dict(id="villalobos-a-roseira", title="A roseira (Nº 102)", confidence="confident",
         composer="Heitor Villa-Lobos", song_photos=[5664], photos=[5664], loose=True),
    dict(id="villalobos-manquinha", title="Manquinha (Nº 74)", confidence="confident",
         composer="Heitor Villa-Lobos", song_photos=[5665], photos=[5665], loose=True),
    dict(id="villalobos-na-corda-da-viola", title="Na corda da viola (Nº 43)", confidence="confident",
         composer="Heitor Villa-Lobos", song_photos=[5666], photos=[5666], loose=True),
]


def first_nonnull(book_photos, field):
    for n in book_photos:
        v = photos[P(n)].get(field)
        if v:
            return v
    return None


def norm(t):
    return re.sub(r"\s+", " ", (t or "").strip().lower())


# --- Build canonical records ----------------------------------------------
out = []
assigned = set()
for bk in BOOKS:
    pnums = bk["photos"]
    assigned.update(pnums)
    # merge songs from song_photos, dedupe by normalized title (prefer one with page)
    merged = OrderedDict()
    for n in bk.get("song_photos", []):
        for s in (photos[P(n)].get("songs") or []):
            key = norm(s.get("title"))
            if not key:
                continue
            if key not in merged:
                merged[key] = dict(title=s.get("title"), page=s.get("page"))
                if s.get("composer_printed"):
                    merged[key]["composer_printed"] = s["composer_printed"]
                if s.get("from_printed"):
                    merged[key]["from"] = s["from_printed"]
            else:
                if merged[key].get("page") is None and s.get("page") is not None:
                    merged[key]["page"] = s["page"]
    rec = OrderedDict()
    rec["id"] = bk["id"]
    rec["title"] = bk["title"]
    rec["title_confidence"] = bk["confidence"]
    if bk.get("composer"):
        rec["composer"] = bk["composer"]
    rec["series"] = first_nonnull(pnums, "series")
    rec["volume"] = first_nonnull(pnums, "volume")
    rec["publisher"] = first_nonnull(pnums, "publisher")
    rec["arranger_editor"] = bk.get("arranger") or first_nonnull(pnums, "arranger_editor")
    rec["instrumentation"] = first_nonnull(pnums, "instrumentation")
    rec["isbn"] = first_nonnull(pnums, "isbn")
    rec["is_loose_sheet"] = bool(bk.get("loose"))
    rec["fill_canonical"] = bool(bk.get("fill_canonical"))
    rec["source_photos"] = [P(n) for n in pnums]
    rec["flags"] = bk.get("flags", [])
    rec["songs"] = list(merged.values())
    rec["song_count_captured"] = len(rec["songs"])
    out.append(rec)

# --- Verify full photo coverage -------------------------------------------
all_nums = {int(fn[4:8]) for fn in photos}
missing = sorted(all_nums - assigned)
dupes = []
seen = set()
for bk in BOOKS:
    for n in bk["photos"]:
        if n in seen:
            dupes.append(n)
        seen.add(n)

library = OrderedDict()
library["generated_from"] = "data/raw/batch-*.json"
library["book_count"] = len(out)
library["total_songs_captured"] = sum(r["song_count_captured"] for r in out)
library["books"] = out
json.dump(library, open("data/books.json", "w"), indent=2, ensure_ascii=False)

print(f"Books: {len(out)}  |  Songs captured: {library['total_songs_captured']}")
print(f"Photos assigned: {len(assigned)}/{len(photos)}")
print(f"UNASSIGNED photos: {missing or 'none'}")
print(f"DUPLICATE photo assignments: {dupes or 'none'}")
print(f"\nBooks needing canonical fill (classical sets): "
      f"{sum(1 for r in out if r['fill_canonical'])}")
print(f"Books flagged for reshoot/confirm: {sum(1 for r in out if r['flags'])}")
print("\nConfidence breakdown:")
from collections import Counter
for c, n in Counter(r["title_confidence"] for r in out).most_common():
    print(f"  {n:3d}  {c}")
