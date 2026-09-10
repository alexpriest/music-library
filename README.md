# Music Library

An MCP server over 82 physical sheet-music books, so any Claude can answer a request for a mood with a book and a page.

## Status

Shipped — 82 books and 1,567 songs, reachable from any Claude over MCP.

## License

Not licensed for reuse.

## What's in it

**82 books · 1,567 songs**, built from photos of the collection. The range:
jazz fake-books (Cocktail Jazz, Vince Guaraldi, Cowboy Bebop), a deep classical
shelf (Bach, Mozart, Chopin, Debussy, Liszt, Schumann, Schubert, Scarlatti,
Mendelssohn, Satie, Ravel, Grieg, Granados, Field, John Cage, Philip Glass,
Seymour Bernstein), Joplin ragtime, Yann Tiersen (Piano Works / EUSA / Kerber),
Villa-Lobos, pop/rock songbooks (Elton John, Eagles, Queen, Taylor Swift,
James Bond, The Shins), Disney/film/musical-theatre folios, wedding & children's
collections, and more.

Every song is tagged against a controlled vocabulary (`MOOD_VOCABULARY.md`) so
mood search stays consistent: mood tags, composer & original artist, source
(film/musical/album), genre + subgenre, era/year, tempo, energy (1–5), difficulty,
and occasion (`good_for`).

## How it's built (pipeline)

1. **Extract** — parallel agents transcribe each of the 101 photos (cover /
   contents / loose sheet) into raw per-photo JSON → `data/raw/`.
2. **Group** — `scripts/build_books.py` stitches photos into books using shelf
   order + identity, producing `data/books.json` (every photo accounted for).
3. **Enrich** — parallel agents tag every song against the controlled vocabulary,
   complete the canonical classical sets, and web-verify uncertain items →
   `data/enriched/`.
4. **Merge** — `scripts/merge_library.py` assembles `data/library.json` (the
   source of truth), assigns stable song IDs, and validates the vocabulary.
5. **Index** — `scripts/generate_index.py` writes `LIBRARY.md`, a human-readable
   QC index with flagged/low-confidence items pinned at the top.
6. **Serve** — a TypeScript MCP server (`src/`) loads `library.json` and exposes
   search tools over **stdio** (local) and **Streamable HTTP** (remote).

Regenerate the data layer at any time:
```bash
python3 scripts/build_books.py && python3 scripts/merge_library.py && python3 scripts/generate_index.py
```

## MCP server

Tools: `find_music`, `suggest_by_vibe`, `get_song`, `get_book`, `list_books`,
`random_pick`, `list_vocabulary`.

```bash
npm install
npm run build
npm test          # 12 tests against the real data
```

- **Local (stdio)** — for Claude Code and Kit: `node dist/index.js`
- **Remote (HTTP)** — for the Claude apps: `npm start` (reads `PORT` and the
  required `MCP_SECRET`). Deployed to Railway; the custom-connector URL is
  `https://<host>/mcp/<MCP_SECRET>` (unguessable secret path — see `docs/SETUP.md`).

## Current status

- ✅ Catalog complete: 82 books / 1,567 songs, validated, zero vocab violations.
- ✅ MCP server built and tested; deployed to Railway as a remote connector.
- 📷 34 books flagged in `LIBRARY.md` for a straight-on reshoot (low-res /
  rotated / partially captured contents) and 23 titles identified from their
  song lists for confirmation. Everything else is high-confidence.

## Layout

```
photos/                 source photos of the collection
data/
  raw/                  per-photo transcriptions (provenance)
  enriched/             per-group enriched books (provenance)
  books.json            grouped catalog (pre-enrichment)
  library.json          ← source of truth (served by the MCP)
scripts/                build / merge / index pipeline
src/                    MCP server (TypeScript)
tests/                  vitest suite
MOOD_VOCABULARY.md      controlled tagging vocabulary + schema
LIBRARY.md              human-readable QC index
docs/SETUP.md           how to connect each Claude surface
```
