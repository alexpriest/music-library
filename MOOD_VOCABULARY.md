# Enrichment Vocabulary & Schema

This is the **single source of truth** for how every song is tagged. Enrichment
agents MUST use only the controlled values below so that search stays consistent
across the whole library. Free-text fields are explicitly marked.

## Enriched song schema

```json
{
  "title": "As Time Goes By",            // keep the printed title verbatim
  "page": 8,                              // integer or null (keep what was captured)
  "composer": "Herman Hupfeld",           // actual composer/songwriter (real name)
  "original_artist": "Dooley Wilson",     // performer most associated; null for classical
  "from": "Casablanca",                   // film / musical / album / show; null if none
  "year": 1931,                           // approx. composition or release year; int or null
  "era": "1930s",                         // see ERA below
  "genre": "Jazz Standard",               // top-level, controlled — see GENRE
  "subgenre": "Ballad",                   // free text, optional
  "mood_tags": ["wistful", "romantic", "nostalgic"],  // 2–5 from MOOD list
  "tempo": "slow",                        // controlled — see TEMPO
  "energy": 2,                            // integer 1–5 — see ENERGY
  "difficulty": "intermediate",           // controlled — see DIFFICULTY
  "good_for": ["late night", "dinner"],   // free text, 0–4 tags, occasion/use
  "confidence": "high",                   // high | medium | low (your tagging confidence)
  "notes": null                           // only if something needs flagging
}
```

## MOOD (controlled — use ONLY these; pick 2–5 that best fit)

Tender feelings: `tender` `romantic` `intimate` `sentimental` `warm` `longing`
Sad/reflective: `melancholy` `wistful` `bittersweet` `nostalgic` `mournful` `lonely` `somber`
Calm: `serene` `peaceful` `dreamy` `contemplative` `ethereal`
Bright: `hopeful` `uplifting` `joyful` `cheerful` `playful` `whimsical` `jaunty`
Big/strong: `triumphant` `majestic` `grand` `dramatic` `heroic` `festive`
Dark/edgy: `brooding` `mysterious` `dark` `tense` `haunting`
Driving: `energetic` `driving` `lively` `groovy` `sultry`
Other: `spiritual` `quirky` `elegant` `folksy` `bluesy`

If nothing fits, pick the closest — do NOT invent new mood words.

## GENRE (controlled top-level — pick exactly one)

`Classical` `Jazz Standard` `Jazz` `Ragtime` `Pop` `Rock` `Singer-Songwriter`
`Folk` `Musical Theatre` `Film/TV Score` `Video Game` `Children's` `Holiday`
`Great American Songbook` `Latin/World` `Wedding/Ceremonial` `Religious`
`New Age/Minimalist` `Blues` `Country` `R&B/Soul`

(`subgenre` is free text: e.g. "Bossa Nova", "Nocturne", "Power Ballad", "Étude".)

## ERA (controlled)

Classical periods: `Baroque` `Classical` `Romantic` `Impressionist` `20th-Century` `Contemporary`
Popular by decade: `1900s` `1910s` `1920s` `1930s` `1940s` `1950s` `1960s`
`1970s` `1980s` `1990s` `2000s` `2010s` `2020s`

(Use the period for classical works, the decade for songs.)

## TEMPO (controlled)

`very slow` · `slow` · `medium` · `upbeat` · `fast` · `very fast`

## ENERGY (1–5)

`1` = still/meditative · `2` = gentle · `3` = moderate · `4` = lively · `5` = high-energy/intense

## DIFFICULTY (controlled — solo-piano playing difficulty)

`beginner` · `easy` · `intermediate` · `advanced` · `virtuosic`

For lead-sheet/PVG songbooks where difficulty is arrangement-dependent, estimate
for a standard intermediate arrangement and set `confidence` to `medium`.

## Rules

1. **Knowledge first, verify when unsure.** Tag well-known works from knowledge.
   Web-search anything you are not ~99% confident about (obscure titles, exact
   composer, year, "from"). Set `confidence` honestly.
2. **Keep titles verbatim.** Do not "correct" a printed title; note oddities.
3. **Canonical fill.** If a book has `fill_canonical: true`, replace its (often
   empty) song list with the complete, correct contents of that edition from
   knowledge/web — proper movement titles, opus/BWV/S-numbers, and page numbers
   only if you actually know them (else null). Then enrich each piece.
4. **Composer vs original_artist.** `composer` = who wrote it. `original_artist`
   = the performer it's identified with (pop/standards). Classical: artist null.
5. **good_for** captures occasion/vibe for retrieval: e.g. `dinner`, `late night`,
   `wedding`, `holiday`, `kids`, `focus`, `practice`, `sight-reading`,
   `cocktail party`, `rainy day`, `morning`, `romantic evening`.
