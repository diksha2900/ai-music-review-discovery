"use client";

import { useState } from "react";
import { breakLoop, searchTracks, Track } from "@/lib/api";
import { TrackList } from "@/components/TrackList";

export default function LoopPage() {
  const [query, setQuery] = useState("");
  const [seeds, setSeeds] = useState<Track[]>([]);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function addSeed() {
    if (!query.trim()) return;
    setError("");
    setLoading(true);
    try {
      const { tracks: found } = await searchTracks(query);
      if (found[0]) setSeeds((s) => [...s, found[0]].slice(0, 8));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
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
    <section>
      <h1>
        Break my <span style={{ color: "var(--green)" }}>loop</span>
      </h1>
      <p style={{ color: "var(--muted)" }}>Paste songs you repeat — get unheard tracks with the same feel.</p>
      <div className="card">
        <input
          type="text"
          placeholder="Add a song you keep replaying…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addSeed()}
        />
        <button className="btn" style={{ marginTop: "1rem" }} onClick={addSeed} disabled={loading}>
          Add song
        </button>
      </div>
      {seeds.length > 0 && (
        <>
          <h3>Your loop ({seeds.length})</h3>
          <TrackList tracks={seeds} />
          <button className="btn" onClick={run} disabled={loading}>
            Break the loop
          </button>
        </>
      )}
      {error && <p className="error">{error}</p>}
      {tracks.length > 0 && (
        <div style={{ marginTop: "1.5rem" }}>
          <h2>Escape tracks</h2>
          <TrackList tracks={tracks} />
        </div>
      )}
    </section>
  );
}
