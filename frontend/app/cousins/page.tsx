"use client";

import { useEffect, useState } from "react";
import { findCousins, getNowPlaying, searchTracks, Track } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import { NowPlayingCard, PageShell, SearchResults } from "@/components/PageShell";
import { TrackList } from "@/components/TrackList";

function formatProgress(ms: number) {
  const s = Math.floor(ms / 1000);
  const mm = Math.floor(s / 60);
  const ss = s % 60;
  return `${mm}:${ss.toString().padStart(2, "0")}`;
}

export default function CousinsPage() {
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Track[]>([]);
  const [cousins, setCousins] = useState<Track[]>([]);
  const [anchor, setAnchor] = useState<Track | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [np, setNp] = useState<(Track & { progress_ms?: number }) | null>(null);
  const [pickingId, setPickingId] = useState<string | undefined>();

  useEffect(() => {
    if (user?.logged_in) {
      getNowPlaying().then((r) => setNp(r.playing));
    }
  }, [user?.logged_in]);

  async function runCousins(t: Track) {
    setError("");
    setLoading(true);
    setAnchor(t);
    setCousins([]);
    setResults([]);
    try {
      const data = await findCousins(t.name, t.artist);
      setCousins(data.tracks);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
      setPickingId(undefined);
    }
  }

  async function onSearch() {
    if (!query.trim()) return;
    setError("");
    setLoading(true);
    setAnchor(null);
    setCousins([]);
    try {
      const { tracks } = await searchTracks(query);
      setResults(tracks);
    } catch (e) {
      setError(String(e));
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  function clearAnchor() {
    setAnchor(null);
    setCousins([]);
    setError("");
  }

  return (
    <PageShell
      variant="cousins"
      title={
        <>
          Find <span className="accent">cousins</span>
        </>
      }
      subtitle="Same tempo, beat, feel & genre — different artists you haven't heard."
    >
      {user?.logged_in && np && !anchor && (
        <NowPlayingCard
          track={np}
          progress={np.progress_ms != null ? formatProgress(np.progress_ms) : undefined}
          onFindCousins={() => runCousins(np)}
          loading={loading}
        />
      )}

      {user?.logged_in && !np && !anchor && (
        <div className="hint-card row-between">
          <span>Press play on Spotify to see now-playing here.</span>
          <button type="button" className="btn btn-outline btn-sm" onClick={() => getNowPlaying().then((r) => setNp(r.playing))}>
            Refresh
          </button>
        </div>
      )}

      <div className="card glass">
        <label className="field-label">Search a song</label>
        <p className="field-hint">Type a track name — e.g. kabira, sicko mode, blinding lights</p>
        <input
          type="text"
          placeholder="Search a song you love…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
        />
        <button type="button" className="btn btn-full" style={{ marginTop: "1rem" }} onClick={onSearch} disabled={loading}>
          {loading && !results.length ? "Searching…" : "Search Spotify"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>

      {!anchor && (
        <SearchResults
          tracks={results}
          pickLabel="Find Cousins"
          loadingId={pickingId}
          onPick={(t) => {
            setPickingId(t.id);
            runCousins(t);
          }}
        />
      )}

      {anchor && (
        <div className="results-block">
          <div className="row-between">
            <p>
              Cousins of <strong>{anchor.name}</strong> — {anchor.artist}
            </p>
            <button type="button" className="btn btn-outline btn-sm" onClick={clearAnchor}>
              ← New search
            </button>
          </div>
          {loading && cousins.length === 0 ? (
            <div className="loading-pulse">Scanning musical DNA…</div>
          ) : (
            <TrackList tracks={cousins} />
          )}
        </div>
      )}
    </PageShell>
  );
}
