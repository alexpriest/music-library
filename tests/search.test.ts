import { describe, it, expect } from "vitest";
import {
  findMusic, suggestByVibe, getSong, getBook, listBooks, randomPick, stats,
} from "../src/search.js";

describe("library loads", () => {
  it("has the expected scale", () => {
    const s = stats();
    expect(s.book_count).toBe(82);
    expect(s.song_count).toBeGreaterThan(1500);
    expect(s.vocabulary.moods).toContain("melancholy");
  });
});

describe("findMusic", () => {
  it("filters by mood and every result actually has that mood", () => {
    const { total, results } = findMusic({ mood: "melancholy", limit: 50 });
    expect(total).toBeGreaterThan(10);
    expect(results.every((r) => r.song.mood_tags.includes("melancholy"))).toBe(true);
    expect(results[0].song.location).toMatch(/—|loose sheet|catalogued/);
  });

  it("AND-combines mood + genre", () => {
    const { results } = findMusic({ mood: "wistful", genre: "Jazz Standard", limit: 20 });
    expect(results.every((r) =>
      r.song.mood_tags.includes("wistful") && r.song.genre === "Jazz Standard")).toBe(true);
  });

  it("matches composer/artist substring", () => {
    const { total, results } = findMusic({ composer: "Debussy", limit: 100 });
    expect(total).toBeGreaterThan(5);
    expect(results.every((r) => /debussy/i.test(r.song.composer ?? ""))).toBe(true);
  });

  it("respects energy range", () => {
    const { results } = findMusic({ energy_min: 5, limit: 50 });
    expect(results.every((r) => (r.song.energy ?? 0) >= 5)).toBe(true);
  });

  it("free-text query hits titles", () => {
    const { results } = findMusic({ query: "clair de lune" });
    expect(results.some((r) => /clair de lune/i.test(r.song.title))).toBe(true);
  });
});

describe("suggestByVibe", () => {
  it("maps a rainy/wistful prompt to melancholy-ish picks", () => {
    const { results } = suggestByVibe("something wistful for a rainy night", 10);
    expect(results.length).toBeGreaterThan(0);
    const moods = results[0].song.mood_tags;
    expect(moods.some((m) => ["wistful", "melancholy", "contemplative", "dreamy", "bittersweet"].includes(m)))
      .toBe(true);
  });

  it("maps an upbeat-party prompt to lively/festive picks", () => {
    const { results } = suggestByVibe("upbeat fun party music", 10);
    expect(results.length).toBeGreaterThan(0);
    expect(results.some((r) =>
      r.song.mood_tags.some((m) => ["lively", "festive", "cheerful", "playful", "groovy", "energetic"].includes(m))))
      .toBe(true);
  });
});

describe("books", () => {
  it("get_book returns Cocktail Jazz with its captured songs", () => {
    const b = getBook("Cocktail Jazz");
    expect(b).not.toBeNull();
    expect(Array.isArray(b)).toBe(false);
    if (b && !Array.isArray(b)) {
      expect(b.song_count).toBeGreaterThanOrEqual(20);
      expect(b.songs.some((s) => /as time goes by/i.test(s.title))).toBe(true);
    }
  });

  it("list_books filters by composer", () => {
    const books = listBooks({ composer: "Bach" });
    expect(books.length).toBeGreaterThanOrEqual(3); // three Bach inventions editions
  });
});

describe("getSong", () => {
  it("finds a well-known standard", () => {
    const found = getSong("Autumn in New York");
    expect(found.length).toBeGreaterThan(0);
    expect(found[0].location).toBeTruthy();
  });
});

describe("randomPick", () => {
  it("returns the requested count within filters", () => {
    const picks = randomPick({ genre: "Ragtime", count: 3 });
    expect(picks.length).toBeGreaterThan(0);
    expect(picks.every((p) => p.song.genre === "Ragtime")).toBe(true);
  });
});
