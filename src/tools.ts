import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import {
  findMusic, suggestByVibe, getSong, getBook, listBooks, randomPick, stats,
  type ScoredSong,
} from "./search.js";
import type { FlatSong, Song } from "./library.js";

const json = (data: unknown) => ({
  content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }],
});
const err = (msg: string) => ({
  content: [{ type: "text" as const, text: msg }],
  isError: true,
});

/** Compact, actionable shape for a search hit — always includes where to find it. */
function hit(s: FlatSong, why?: string[]) {
  return {
    title: s.title,
    location: s.location,
    composer: s.composer,
    original_artist: s.original_artist || undefined,
    from: s.from || undefined,
    genre: s.genre,
    era: s.era,
    mood: s.mood_tags,
    tempo: s.tempo,
    energy: s.energy,
    difficulty: s.difficulty,
    good_for: s.good_for?.length ? s.good_for : undefined,
    confidence: s.confidence,
    ...(why?.length ? { why: why.join("; ") } : {}),
  };
}
const hits = (rs: ScoredSong[]) => rs.map((r) => hit(r.song, r.why));

export function registerTools(server: McpServer): void {
  server.registerTool(
    "find_music",
    {
      description:
        "Search the sheet-music library by any combination of mood, genre, era, composer/artist, tempo, energy, difficulty, source (film/musical/album), instrumentation, and free text. " +
        "All provided filters are combined (AND); multiple values within one filter match any (OR). " +
        "Every result tells you which book and page to pull off the shelf. Use list_vocabulary first if unsure of valid mood/genre/era/tempo/difficulty values.",
      inputSchema: {
        query: z.string().optional().describe("Free text: matches title, composer, artist, source, book, mood, occasion."),
        mood: z.union([z.string(), z.array(z.string())]).optional().describe("Controlled mood tag(s), e.g. 'melancholy', ['romantic','tender']."),
        genre: z.union([z.string(), z.array(z.string())]).optional().describe("Controlled genre, e.g. 'Jazz Standard', 'Classical'."),
        era: z.union([z.string(), z.array(z.string())]).optional().describe("Controlled era: a period (Baroque/Romantic/Impressionist/...) or decade ('1970s')."),
        composer: z.string().optional().describe("Composer or original artist (substring match)."),
        from: z.string().optional().describe("Film, musical, show, or album the piece is from."),
        tempo: z.union([z.string(), z.array(z.string())]).optional().describe("very slow | slow | medium | upbeat | fast | very fast."),
        difficulty: z.union([z.string(), z.array(z.string())]).optional().describe("beginner | easy | intermediate | advanced | virtuosic."),
        energy_min: z.number().int().min(1).max(5).optional().describe("Minimum energy 1–5."),
        energy_max: z.number().int().min(1).max(5).optional().describe("Maximum energy 1–5."),
        instrumentation: z.string().optional().describe("e.g. 'Piano Solo', 'Piano-Vocal-Guitar' (substring)."),
        limit: z.number().int().min(1).max(100).optional().describe("Max results (default 25)."),
      },
    },
    async (p) => {
      const { total, results } = findMusic(p);
      return json({ total_matches: total, showing: results.length, results: hits(results) });
    }
  );

  server.registerTool(
    "suggest_by_vibe",
    {
      description:
        "Natural-language mood/vibe search. Give a plain description of a feeling, scene, or occasion " +
        "(e.g. 'something wistful for a rainy night', 'upbeat cocktail party jazz', 'calm music to focus to', " +
        "'epic and triumphant') and get ranked picks with the book + page to play from. " +
        "Best when the user describes a feeling rather than exact filters.",
      inputSchema: {
        description: z.string().describe("Free-text vibe / mood / scene / occasion."),
        limit: z.number().int().min(1).max(50).optional().describe("Max results (default 15)."),
      },
    },
    async ({ description, limit }) => {
      const { total, results } = suggestByVibe(description, limit ?? 15);
      if (!results.length)
        return json({ total_matches: 0, results: [], hint: "No vibe match — try find_music with explicit mood/genre, or call list_vocabulary." });
      return json({ total_matches: total, showing: results.length, results: hits(results) });
    }
  );

  server.registerTool(
    "get_song",
    {
      description: "Look up a specific song by title (or song_id) and return its full details plus where to find it.",
      inputSchema: { title: z.string().describe("Song title (or exact song_id).") },
    },
    async ({ title }) => {
      const found = getSong(title);
      if (!found.length) return err(`No song matching "${title}".`);
      if (found.length === 1) return json(hit(found[0]));
      return json({ matches: found.length, results: found.map((s) => hit(s)) });
    }
  );

  server.registerTool(
    "get_book",
    {
      description: "Get a book's details and its full song list (with page numbers). Match by book id or title.",
      inputSchema: { book: z.string().describe("Book id or title (substring).") },
    },
    async ({ book }) => {
      const found = getBook(book);
      if (!found) return err(`No book matching "${book}".`);
      if (Array.isArray(found))
        return json({ matches: found.length, books: found.map((b) => ({ id: b.id, title: b.title, song_count: b.song_count })) });
      return json({
        id: found.id,
        title: found.title,
        title_confidence: found.title_confidence,
        title_suggestion: found.title_suggestion,
        composer: found.composer,
        series: found.series,
        publisher: found.publisher,
        arranger_editor: found.arranger_editor,
        instrumentation: found.instrumentation,
        is_loose_sheet: found.is_loose_sheet,
        flags: found.flags,
        song_count: found.song_count,
        songs: found.songs.map((s: Song) => ({
          title: s.title, page: s.page, composer: s.composer, from: s.from,
          mood: s.mood_tags, tempo: s.tempo, difficulty: s.difficulty,
        })),
      });
    }
  );

  server.registerTool(
    "list_books",
    {
      description: "Browse the book collection (summaries, not every song). Optionally filter by free text, genre, or composer/artist.",
      inputSchema: {
        query: z.string().optional().describe("Free text over title/series/composer."),
        genre: z.string().optional().describe("Only books containing this genre."),
        composer: z.string().optional().describe("Only books by this composer/artist."),
      },
    },
    async (f) => {
      const books = listBooks(f);
      return json({ count: books.length, books });
    }
  );

  server.registerTool(
    "random_pick",
    {
      description: "Surprise me. Returns random song(s) from the library, optionally constrained by the same filters as find_music (mood, genre, composer, difficulty, etc.).",
      inputSchema: {
        count: z.number().int().min(1).max(20).optional().describe("How many (default 3)."),
        mood: z.union([z.string(), z.array(z.string())]).optional(),
        genre: z.union([z.string(), z.array(z.string())]).optional(),
        era: z.union([z.string(), z.array(z.string())]).optional(),
        composer: z.string().optional(),
        difficulty: z.union([z.string(), z.array(z.string())]).optional(),
        energy_min: z.number().int().min(1).max(5).optional(),
        energy_max: z.number().int().min(1).max(5).optional(),
      },
    },
    async (p) => {
      const picks = randomPick(p);
      if (!picks.length) return json({ results: [], hint: "No songs match those filters." });
      return json({ results: hits(picks) });
    }
  );

  server.registerTool(
    "list_vocabulary",
    {
      description: "Return the controlled vocabulary (valid moods, genres, eras, tempos, difficulties) and overall library stats. Call this to know which exact tag values find_music accepts.",
      inputSchema: {},
    },
    async () => json(stats())
  );
}
