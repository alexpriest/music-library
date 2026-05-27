import { flatSongs, booksById, library, type FlatSong, type Book } from "./library.js";

const lc = (s: unknown) => String(s ?? "").toLowerCase();
const arr = (v: string | string[] | undefined): string[] =>
  v == null ? [] : Array.isArray(v) ? v : [v];

/** Free-text vibe words -> controlled mood tags. Powers natural "feeling" search. */
const VIBE_TO_MOODS: Record<string, string[]> = {
  sad: ["melancholy", "mournful", "somber", "wistful"],
  melancholy: ["melancholy", "wistful", "bittersweet"],
  rainy: ["melancholy", "wistful", "contemplative", "dreamy"],
  blue: ["melancholy", "bluesy", "somber"],
  heartbreak: ["mournful", "longing", "bittersweet"],
  longing: ["longing", "wistful", "romantic"],
  nostalgic: ["nostalgic", "wistful", "sentimental"],
  reflective: ["contemplative", "wistful", "serene"],
  happy: ["joyful", "cheerful", "uplifting"],
  joyful: ["joyful", "cheerful", "festive"],
  upbeat: ["lively", "cheerful", "energetic"],
  fun: ["playful", "cheerful", "jaunty"],
  playful: ["playful", "whimsical", "jaunty"],
  chill: ["serene", "peaceful", "dreamy"],
  calm: ["serene", "peaceful", "contemplative"],
  relaxing: ["serene", "peaceful", "dreamy"],
  peaceful: ["peaceful", "serene"],
  dreamy: ["dreamy", "ethereal", "serene"],
  romantic: ["romantic", "tender", "intimate"],
  tender: ["tender", "warm", "intimate"],
  intimate: ["intimate", "tender", "sultry"],
  sexy: ["sultry", "intimate", "groovy"],
  sultry: ["sultry", "groovy"],
  energetic: ["energetic", "driving", "lively"],
  driving: ["driving", "energetic"],
  epic: ["triumphant", "majestic", "grand", "dramatic"],
  triumphant: ["triumphant", "heroic", "grand"],
  grand: ["grand", "majestic"],
  dramatic: ["dramatic", "tense"],
  dark: ["dark", "brooding", "mysterious"],
  spooky: ["dark", "haunting", "mysterious"],
  haunting: ["haunting", "ethereal", "mysterious"],
  mysterious: ["mysterious", "brooding"],
  tense: ["tense", "dramatic"],
  festive: ["festive", "joyful", "lively"],
  party: ["festive", "lively", "groovy"],
  groovy: ["groovy", "lively"],
  elegant: ["elegant", "serene"],
  pretty: ["tender", "dreamy", "elegant"],
  hopeful: ["hopeful", "uplifting", "warm"],
  uplifting: ["uplifting", "hopeful", "triumphant"],
  warm: ["warm", "tender"],
  spiritual: ["spiritual", "serene", "contemplative"],
  quirky: ["quirky", "whimsical", "playful"],
  folksy: ["folksy", "warm"],
  bluesy: ["bluesy", "sultry"],
  lonely: ["lonely", "melancholy", "somber"],
};

/** Vibe words -> good_for occasion tags. */
const VIBE_TO_OCCASION: Record<string, string[]> = {
  dinner: ["dinner"], dining: ["dinner"], cocktail: ["cocktail party", "dinner"],
  party: ["cocktail party", "celebration"], wedding: ["wedding"],
  holiday: ["holiday"], christmas: ["holiday"], kids: ["kids"], children: ["kids"],
  focus: ["focus", "study"], study: ["focus", "study"], studying: ["focus", "study"],
  practice: ["practice", "sight-reading"], sightreading: ["sight-reading"],
  morning: ["morning"], night: ["late night"], evening: ["late night", "romantic evening"],
  romantic: ["romantic evening"], rainy: ["rainy day"], background: ["dinner", "focus"],
};

/** Vibe words -> genre hints. */
const VIBE_TO_GENRE: Record<string, string[]> = {
  jazz: ["Jazz", "Jazz Standard"], classical: ["Classical"], ragtime: ["Ragtime"],
  pop: ["Pop"], rock: ["Rock"], blues: ["Blues"], folk: ["Folk"], country: ["Country"],
  musical: ["Musical Theatre"], showtune: ["Musical Theatre"], broadway: ["Musical Theatre"],
  christmas: ["Holiday"], holiday: ["Holiday"], wedding: ["Wedding/Ceremonial"],
  film: ["Film/TV Score"], movie: ["Film/TV Score"], soundtrack: ["Film/TV Score"],
  game: ["Video Game"], minimalist: ["New Age/Minimalist"], standard: ["Great American Songbook", "Jazz Standard"],
};

const STOPWORDS = new Set([
  "a", "an", "the", "for", "to", "of", "and", "or", "with", "in", "on", "at",
  "something", "some", "play", "want", "find", "me", "i", "feel", "feeling",
  "like", "song", "songs", "music", "piece", "pieces", "that", "is", "my",
  "give", "show", "looking", "need", "really", "very", "kinda", "bit", "more",
]);

function tokenize(s: string): string[] {
  return lc(s).split(/[^a-z0-9']+/).filter((t) => t && !STOPWORDS.has(t));
}

export interface FindParams {
  query?: string;
  mood?: string | string[];
  genre?: string | string[];
  era?: string | string[];
  composer?: string;
  from?: string;
  tempo?: string | string[];
  difficulty?: string | string[];
  energy_min?: number;
  energy_max?: number;
  instrumentation?: string;
  limit?: number;
}

export interface ScoredSong {
  song: FlatSong;
  score: number;
  why: string[];
}

const CONF_BONUS: Record<string, number> = { high: 0.3, medium: 0.1, low: 0 };

/** Structured + free-text search. All provided filters are AND-ed; values within a filter OR. */
export function findMusic(p: FindParams): { total: number; results: ScoredSong[] } {
  const moods = arr(p.mood).map(lc);
  const genres = arr(p.genre).map(lc);
  const eras = arr(p.era).map(lc);
  const tempos = arr(p.tempo).map(lc);
  const diffs = arr(p.difficulty).map(lc);
  const qTokens = p.query ? tokenize(p.query) : [];

  const scored: ScoredSong[] = [];
  for (const s of flatSongs) {
    const why: string[] = [];
    let ok = true;
    let score = 0;

    if (moods.length) {
      const hit = (s.mood_tags || []).filter((m) => moods.includes(lc(m)));
      if (!hit.length) ok = false;
      else { score += hit.length * 2; why.push(`mood: ${hit.join(", ")}`); }
    }
    if (ok && genres.length) {
      if (!genres.includes(lc(s.genre))) ok = false;
      else { score += 1.5; why.push(`genre: ${s.genre}`); }
    }
    if (ok && eras.length) {
      if (!eras.includes(lc(s.era))) ok = false;
      else { score += 1; why.push(`era: ${s.era}`); }
    }
    if (ok && tempos.length) {
      if (!tempos.includes(lc(s.tempo))) ok = false;
      else { score += 1; }
    }
    if (ok && diffs.length) {
      if (!diffs.includes(lc(s.difficulty))) ok = false;
      else { score += 1; }
    }
    if (ok && p.energy_min != null && (s.energy == null || s.energy < p.energy_min)) ok = false;
    if (ok && p.energy_max != null && (s.energy == null || s.energy > p.energy_max)) ok = false;
    if (ok && p.composer) {
      const c = lc(p.composer);
      if (lc(s.composer).includes(c) || lc(s.original_artist).includes(c)) {
        score += 2; why.push(`by ${s.composer || s.original_artist}`);
      } else ok = false;
    }
    if (ok && p.from) {
      if (lc(s.from).includes(lc(p.from))) { score += 2; why.push(`from ${s.from}`); }
      else ok = false;
    }
    if (ok && p.instrumentation) {
      if (!lc(s.book_instrumentation).includes(lc(p.instrumentation))) ok = false;
    }
    if (ok && qTokens.length) {
      const hay = lc([
        s.title, s.composer, s.original_artist, s.from, s.subgenre,
        s.book_title, (s.mood_tags || []).join(" "), (s.good_for || []).join(" "),
      ].join("  "));
      const hits = qTokens.filter((t) => hay.includes(t));
      if (!hits.length) ok = false;
      else {
        score += hits.length;
        if (lc(s.title).includes(qTokens.join(" "))) score += 3; // phrase in title
        why.push(`matches "${p.query}"`);
      }
    }

    if (!ok) continue;
    score += CONF_BONUS[lc(s.confidence)] ?? 0;
    scored.push({ song: s, score, why });
  }

  scored.sort((a, b) => b.score - a.score || a.song.title.localeCompare(b.song.title));
  const limit = p.limit ?? 25;
  return { total: scored.length, results: scored.slice(0, limit) };
}

/** Natural-language "vibe" search: maps everyday words to moods/occasions/genres, then ranks. */
export function suggestByVibe(description: string, limit = 15): { total: number; results: ScoredSong[] } {
  const tokens = tokenize(description);
  const moods = new Set<string>();
  const occasions = new Set<string>();
  const genres = new Set<string>();
  for (const t of tokens) {
    (VIBE_TO_MOODS[t] || []).forEach((m) => moods.add(m));
    (VIBE_TO_OCCASION[t] || []).forEach((o) => occasions.add(o));
    (VIBE_TO_GENRE[t] || []).forEach((g) => genres.add(lc(g)));
  }

  const scored: ScoredSong[] = [];
  for (const s of flatSongs) {
    const why: string[] = [];
    let score = 0;
    const moodHits = (s.mood_tags || []).filter((m) => moods.has(lc(m)));
    if (moodHits.length) { score += moodHits.length * 2; why.push(`mood: ${moodHits.join(", ")}`); }
    const occHits = (s.good_for || []).filter((g) => [...occasions].some((o) => lc(g).includes(o)));
    if (occHits.length) { score += occHits.length * 1.5; why.push(`good for ${occHits.join(", ")}`); }
    if (genres.size && genres.has(lc(s.genre))) { score += 1.5; why.push(`genre: ${s.genre}`); }
    // light free-text overlap on title/composer/from/subgenre
    const hay = lc([s.title, s.composer, s.original_artist, s.from, s.subgenre].join(" "));
    const textHits = tokens.filter((t) => t.length > 3 && hay.includes(t));
    if (textHits.length) { score += textHits.length; why.push(`text: ${textHits.join(", ")}`); }

    if (score <= 0) continue;
    score += CONF_BONUS[lc(s.confidence)] ?? 0;
    scored.push({ song: s, score, why });
  }
  scored.sort((a, b) => b.score - a.score || a.song.title.localeCompare(b.song.title));
  return {
    total: scored.length,
    results: scored.slice(0, limit),
  };
}

export function getSong(query: string): FlatSong[] {
  const q = lc(query).trim();
  const exact = flatSongs.find((s) => lc(s.song_id) === q);
  if (exact) return [exact];
  const titleExact = flatSongs.filter((s) => lc(s.title) === q);
  if (titleExact.length) return titleExact;
  return flatSongs.filter((s) => lc(s.title).includes(q)).slice(0, 25);
}

export interface BookSummary {
  id: string;
  title: string;
  title_confidence: string;
  title_suggestion?: string;
  composer?: string;
  series: string | null;
  instrumentation: string | null;
  is_loose_sheet: boolean;
  song_count: number;
  genres: string[];
  flags: string[];
}

function summarizeBook(b: Book): BookSummary {
  const genres = [...new Set(b.songs.map((s) => s.genre).filter(Boolean) as string[])];
  return {
    id: b.id, title: b.title, title_confidence: b.title_confidence,
    title_suggestion: b.title_suggestion, composer: b.composer, series: b.series,
    instrumentation: b.instrumentation, is_loose_sheet: b.is_loose_sheet,
    song_count: b.song_count, genres, flags: b.flags,
  };
}

export function listBooks(filter?: { query?: string; genre?: string; composer?: string }): BookSummary[] {
  let books = library.books;
  if (filter?.composer) {
    const c = lc(filter.composer);
    books = books.filter((b) => lc(b.composer).includes(c) ||
      b.songs.some((s) => lc(s.composer).includes(c) || lc(s.original_artist).includes(c)));
  }
  if (filter?.genre) {
    const g = lc(filter.genre);
    books = books.filter((b) => b.songs.some((s) => lc(s.genre) === g));
  }
  if (filter?.query) {
    const q = lc(filter.query);
    books = books.filter((b) =>
      lc(b.title).includes(q) || lc(b.title_suggestion).includes(q) ||
      lc(b.series).includes(q) || lc(b.composer).includes(q));
  }
  return books.map(summarizeBook).sort((a, b) => a.title.localeCompare(b.title));
}

export function getBook(query: string): Book | Book[] | null {
  const q = lc(query).trim();
  const byId = booksById.get(q);
  if (byId) return byId;
  const matches = library.books.filter(
    (b) => lc(b.title).includes(q) || lc(b.title_suggestion).includes(q)
  );
  if (matches.length === 1) return matches[0];
  return matches.length ? matches : null;
}

export function randomPick(p: FindParams & { count?: number }): ScoredSong[] {
  const pool = findMusic({ ...p, limit: 100000 }).results;
  const count = Math.min(p.count ?? 3, pool.length);
  const picks: ScoredSong[] = [];
  const used = new Set<number>();
  while (picks.length < count && used.size < pool.length) {
    const i = Math.floor(Math.random() * pool.length);
    if (used.has(i)) continue;
    used.add(i);
    picks.push(pool[i]);
  }
  return picks;
}

export function stats() {
  const byGenre: Record<string, number> = {};
  const byEra: Record<string, number> = {};
  const byMood: Record<string, number> = {};
  for (const s of flatSongs) {
    if (s.genre) byGenre[s.genre] = (byGenre[s.genre] || 0) + 1;
    if (s.era) byEra[s.era] = (byEra[s.era] || 0) + 1;
    for (const m of s.mood_tags || []) byMood[m] = (byMood[m] || 0) + 1;
  }
  return {
    title: library.title,
    book_count: library.book_count,
    song_count: library.song_count,
    by_genre: byGenre,
    by_era: byEra,
    by_mood: byMood,
    vocabulary: library.vocabulary,
  };
}
