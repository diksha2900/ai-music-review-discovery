"use client";

import { useState } from "react";
import { findCousins, searchTracks, Track } from "../lib/api";
import { TrackList } from "../components/TrackList";

export default function CousinsPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Track[]>([]);
  const [cousins, setCousins] = useState<Track[]>([]);
  const [anchor, setAnchor] = useState<Track | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onSearch() {
    if (!query.trim()) return;
    setError("");
    setLoading(true);
    try {
      const { tracks } = await searchTracks(query);
      setResults(tracks);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function pickTrack(t: Track) {
    setError("");
    setLoading(true);
    setAnchor(t);
    try {
      const data = await findCousins(t.name, t.artist);
      setCousins(data.tracks);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h1>
        Find <span style={{ color: "var(--green)" }}>cousins</span>
      </h1>
      <p style={{ color: "var(--muted)" }}>Same tempo, beat &amp; feel — different artists.</p>
      <div className="card" style={{ marginTop: "1.5rem" }}>
        <input
          type="text"
          placeholder="Search a song you love…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
        />
        <button className="btn" style={{ marginTop: "1rem" }} onClick={onSearch} disabled={loading}>
          {loading ? "Searching…" : "Search"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>
      {results.length > 0 && !anchor && (
        <div className="track-grid" style={{ marginTop: "1rem" }}>
          {results.map((t) => (
            <button key={t.id} className="card track" onClick={() => pickTrack(t)} style={{ width: "100%", textAlign: "left", cursor: "pointer" }}>
              {t.album_art && <img src={t.album_art} alt="" />}
              <div className="track-meta">
                <strong>{t.name}</strong>
                <small>{t.artist}</small>
              </div>
            </button>
          ))}
        </div>
      )}
      {anchor && (
        <div style={{ marginTop: "1.5rem" }}>
          <p>
            Cousins of <strong>{anchor.name}</strong> — {anchor.artist}
          </p>
          <TrackList tracks={cousins} />
        </div>
      )}
    </section>
  );
}
