"use client";

import { useState } from "react";
import { breakLoop, searchTracks, Track } from "@/lib/api";
import { PageShell, SearchResults } from "@/components/PageShell";
import { TrackList } from "@/components/TrackList";

export default function LoopPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Track[]>([]);
  const [seeds, setSeeds] = useState<Track[]>([]);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onSearch() {
    if (!query.trim()) return;
    setError("");
    setLoading(true);
    try {
      const { tracks: found } = await searchTracks(query);
      setResults(found);
    } catch (e) {
      setError(String(e));
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  function addSeed(t: Track) {
    if (seeds.some((s) => s.id === t.id)) {
      setError("Already in your loop — remove it first to re-add.");
      return;
    }
    setError("");
    setSeeds((s) => [...s, t].slice(0, 8));
    setResults([]);
    setQuery("");
  }

  function removeSeed(id: string) {
    setSeeds((s) => s.filter((x) => x.id !== id));
    setError("");
  }

  async function run() {
    if (!seeds.length) return;
    setLoading(true);
    setError("");
    try {
      const data = await breakLoop(seeds);
      setTracks(data.tracks);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell
      variant="loop"
      title={
        <>
          Break my <span className="accent">loop</span>
        </>
      }
      subtitle="Stuck replaying the same 5 songs? Add them — we'll find unheard tracks with the same feel."
    >
      <div className="card glass">
        <label className="field-label">Add a song you repeat</label>
        <p className="field-hint">Search → pick from Spotify list → add up to 8 songs</p>
        <input
          type="text"
          placeholder="Search a song you keep replaying…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
        />
        <button type="button" className="btn btn-full" style={{ marginTop: "1rem" }} onClick={onSearch} disabled={loading}>
          {loading && !results.length ? "Searching…" : "Search Spotify"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>

      <SearchResults tracks={results} pickLabel="Add" onPick={addSeed} />

      {seeds.length > 0 && (
        <div className="results-block">
          <div className="row-between">
            <h2 className="section-heading">Your loop ({seeds.length}/8)</h2>
            <button type="button" className="btn btn-sm" onClick={run} disabled={loading}>
              {loading ? "Breaking…" : "Break the loop"}
            </button>
          </div>
          <TrackList tracks={seeds} onRemove={removeSeed} />
        </div>
      )}

      {tracks.length > 0 && (
        <div className="results-block">
          <h2 className="section-heading">Escape tracks</h2>
          <TrackList tracks={tracks} />
        </div>
      )}
    </PageShell>
  );
}
