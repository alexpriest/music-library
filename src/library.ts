import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));

export interface Song {
  song_id: string;
  title: string;
  page: number | null;
  composer: string | null;
  original_artist: string | null;
  from: string | null;
  year: number | null;
  era: string | null;
  genre: string | null;
  subgenre: string | null;
  mood_tags: string[];
  tempo: string | null;
  energy: number | null;
  difficulty: string | null;
  good_for: string[];
  confidence: string | null;
  notes: string | null;
}

export interface Book {
  id: string;
  title: string;
  title_confidence: string;
  title_suggestion?: string;
  identification_note?: string;
  composer?: string;
  series: string | null;
  volume: string | null;
  publisher: string | null;
  arranger_editor: string | null;
  instrumentation: string | null;
  isbn: string | null;
  is_loose_sheet: boolean;
  source_photos: string[];
  flags: string[];
  songs: Song[];
  song_count: number;
}

export interface Library {
  title: string;
  book_count: number;
  song_count: number;
  vocabulary: {
    moods: string[];
    genres: string[];
    eras: string[];
    tempos: string[];
    difficulties: string[];
  };
  books: Book[];
}

/** A song flattened with its book context, so every result is actionable. */
export interface FlatSong extends Song {
  book_id: string;
  book_title: string;
  book_series: string | null;
  book_instrumentation: string | null;
  is_loose_sheet: boolean;
  /** Human "where to find it" string, e.g. "Cocktail Jazz — p. 8". */
  location: string;
}

function locationOf(book: Book, song: Song): string {
  if (book.is_loose_sheet) return `${book.title} (loose sheet)`;
  if (song.page != null) return `${book.title} — p. ${song.page}`;
  return `${book.title} (page not catalogued)`;
}

// NB: not LIBRARY_PATH — that's a standard compiler/linker env var Nix sets.
const DATA_PATH =
  process.env.MUSIC_LIBRARY_PATH || join(__dirname, "..", "data", "library.json");

export const library: Library = JSON.parse(readFileSync(DATA_PATH, "utf-8"));

export const flatSongs: FlatSong[] = library.books.flatMap((book) =>
  book.songs.map((song) => ({
    ...song,
    book_id: book.id,
    book_title: book.title,
    book_series: book.series,
    book_instrumentation: book.instrumentation,
    is_loose_sheet: book.is_loose_sheet,
    location: locationOf(book, song),
  }))
);

export const booksById = new Map(library.books.map((b) => [b.id, b]));
