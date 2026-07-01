"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  breakLoop,
  findCousins,
  getNowPlaying,
  getVibe,
  searchTracks,
  Track,
} from "@/lib/api";
import { getTimeBand } from "@/lib/timeBand";
import { LoginButton } from "@/components/AuthBar";
import { useAuth } from "@/components/AuthProvider";
import { SearchResults } from "@/components/PageShell";
import { TrackList } from "@/components/TrackList";

type Tab = "cousins" | "vibe" | "loop";

const TABS: { id: Tab; label: string; sub: string }[] = [
  { id: "cousins", label: "Find Cousins", sub: "Hero · same tempo & feel, new artists" },
  { id: "vibe", label: "Start From Vibe", sub: "Mood · time · emojis" },
  { id: "loop", label: "Break My Loop", sub: "Escape your repeat list" },
];

function Waveform() {
  return (
    <div className="waveform" aria-hidden>
      {Array.from({ length: 24 }).map((_, i) => (
        <span key={i} style={{ animationDelay: `${i * 0.08}s` }} />
      ))}
    </div>
  );
}

export function HomeHub() {
  const { user, loading } = useAuth();
  const [tab, setTab] = useState<Tab>("cousins");
  const band = useMemo(() => getTimeBand(new Date()), []);

  // Cousins tab state
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Track[]>([]);
  const [cousins, setCousins] = useState<Track[]>([]);
  const [anchor, setAnchor] = useState<Track | null>(null);
  const [np, setNp] = useState<(Track & { progress_ms?: number }) | null>(null);

  // Vibe tab state
  const [vibeText, setVibeText] = useState("");
  const [vibeTracks, setVibeTracks] = useState<Track[]>([]);

  // Loop tab state
  const [loopQuery, setLoopQuery] = useState("");
  const [loopResults, setLoopResults] = useState<Track[]>([]);
  const [seeds, setSeeds] = useState<Track[]>([]);
  const [escapeTracks, setEscapeTracks] = useState<Track[]>([]);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const switchTab = useCallback((t: Tab) => {
    setTab(t);
    setError("");
    setResults([]);
    setCousins([]);
    setAnchor(null);
    setVibeTracks([]);
    setLoopResults([]);
    setEscapeTracks([]);
  }, []);

  const refreshNowPlaying = useCallback(async () => {
    const r = await getNowPlaying();
    setNp(r.playing);
  }, []);

  useEffect(() => {
    if (user?.logged_in) refreshNowPlaying();
    else setNp(null);
  }, [user?.logged_in, refreshNowPlaying]);

  async function searchCousins() {
    if (!query.trim()) return;
    setBusy(true);
    setError("");
    setAnchor(null);
    setCousins([]);
    try {
      const { tracks } = await searchTracks(query);
      setResults(tracks);
    } catch (e) {
      setError(String(e));
      setResults([]);
    } finally {
      setBusy(false);
    }
  }

  async function runCousins(t: Track) {
    setBusy(true);
    setError("");
    setAnchor(t);
    setResults([]);
    setCousins([]);
    try {
      const data = await findCousins(t.name, t.artist);
      setCousins(data.tracks);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function runVibe(fromMoment = false) {
    const vibe = fromMoment ? band.vibe : vibeText.trim() || band.vibe;
    setBusy(true);
    setError("");
    try {
      const data = await getVibe(vibe, 5);
      setVibeTracks(data.tracks);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function searchLoop() {
    if (!loopQuery.trim()) return;
    setBusy(true);
    setError("");
    try {
      const { tracks } = await searchTracks(loopQuery);
      setLoopResults(tracks);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  function addSeed(t: Track) {
    if (seeds.some((s) => s.id === t.id)) {
      setError("Already in your loop.");
      return;
    }
    setSeeds((s) => [...s, t].slice(0, 8));
    setLoopResults([]);
    setLoopQuery("");
    setError("");
  }

  async function runLoop() {
    if (!seeds.length) return;
    setBusy(true);
    setError("");
    try {
      const data = await breakLoop(seeds);
      setEscapeTracks(data.tracks);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  if (loading) return null;

  return (
    <section className="page-shell page-home">
      <div className="page-glow" aria-hidden />
      <Waveform />

      <header className="hub-hero">
        <p className="hero-eyebrow">Find Cousins</p>
        <h1 className="hub-title">Same feel, different artists.</h1>
        <p className="hub-lead">
          Love a song? We find unheard tracks with the same tempo, beat &amp; vibe — not the same
          artist on shuffle.
        </p>

        {tab === "cousins" && !anchor && (
          <div className="hub-search-row">
            <input
              type="text"
              className="hub-search-input"
              placeholder="Search a song you love…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && searchCousins()}
            />
            <button type="button" className="btn btn-lg" onClick={searchCousins} disabled={busy}>
              Find Cousins
            </button>
          </div>
        )}

        <div className="hub-cta-row">
          {!user?.logged_in ? (
            <>
              <span className="hub-guest">Guest mode — search works without an account</span>
              <LoginButton className="btn-lg" />
            </>
          ) : (
            <span className="hub-guest">
              Welcome, <strong>{user.display_name}</strong> — now-playing appears below when Spotify is active.
            </span>
          )}
        </div>
      </header>

      <div className="hub-tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`hub-tab ${tab === t.id ? "hub-tab-active" : ""} ${t.id === "cousins" ? "hub-tab-hero" : ""}`}
            onClick={() => switchTab(t.id)}
          >
            <span className="hub-tab-label">{t.label}</span>
            <span className="hub-tab-sub">{t.sub}</span>
          </button>
        ))}
      </div>

      <div className="hub-panel" role="tabpanel">
        {tab === "cousins" && (
          <>
            {user?.logged_in && !anchor && (
              <div className="card now-playing">
                {np ? (
                  <>
                    <p className="section-label">Now playing on Spotify</p>
                    <div className="track">
                      {np.album_art && <img src={np.album_art} alt="" className="np-art" />}
                      <div className="track-meta">
                        <strong>{np.name}</strong>
                        <small>{np.artist}</small>
                      </div>
                    </div>
                    <div className="row-actions">
                      <button type="button" className="btn btn-full" onClick={() => runCousins(np)} disabled={busy}>
                        Find Cousins of this song
                      </button>
                      <button type="button" className="btn btn-outline btn-sm" onClick={refreshNowPlaying}>
                        Refresh
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="row-between">
                    <span className="muted">Play something on Spotify, then refresh.</span>
                    <button type="button" className="btn btn-outline btn-sm" onClick={refreshNowPlaying}>
                      Refresh
                    </button>
                  </div>
                )}
              </div>
            )}

            {!anchor && (
              <SearchResults tracks={results} pickLabel="Find Cousins" onPick={runCousins} />
            )}

            {anchor && (
              <div className="results-block">
                <div className="row-between">
                  <p>
                    Cousins of <strong>{anchor.name}</strong> — {anchor.artist}
                  </p>
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    onClick={() => {
                      setAnchor(null);
                      setCousins([]);
                    }}
                  >
                    Clear
                  </button>
                </div>
                {busy && !cousins.length ? (
                  <div className="loading-pulse">Scanning musical DNA…</div>
                ) : (
                  <TrackList tracks={cousins} />
                )}
              </div>
            )}

            <p className="hub-deep-link">
              Full experience → <Link href="/cousins">Open Find Cousins</Link>
            </p>
          </>
        )}

        {tab === "vibe" && (
          <>
            <button type="button" className="moment-card moment-card-click" onClick={() => runVibe(true)} disabled={busy}>
              <p className="moment-time">IT&apos;S {band.clock}</p>
              <p className="moment-mood">{band.mood}</p>
              <p className="moment-cta">Tap for your time-of-day vibe →</p>
            </button>
            <div className="card glass">
              <label className="field-label">Describe your mood</label>
              <p className="field-hint">Rainy evening, coffee, late-night drive…</p>
              <input
                type="text"
                value={vibeText}
                onChange={(e) => setVibeText(e.target.value)}
                placeholder="Soft heartbreak, gym energy, focus mode…"
              />
              <button type="button" className="btn btn-full" style={{ marginTop: "1rem" }} onClick={() => runVibe(false)} disabled={busy}>
                Get My Vibe
              </button>
            </div>
            {vibeTracks.length > 0 && <TrackList tracks={vibeTracks} />}
            <p className="hub-deep-link">
              Full experience → <Link href="/vibe">Open Start From Vibe</Link>
            </p>
          </>
        )}

        {tab === "loop" && (
          <>
            <div className="card glass">
              <label className="field-label">Add songs you repeat</label>
              <p className="field-hint">Search → pick from list → add up to 8</p>
              <input
                type="text"
                value={loopQuery}
                onChange={(e) => setLoopQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && searchLoop()}
                placeholder="Search a song stuck on loop…"
              />
              <button type="button" className="btn btn-full" style={{ marginTop: "1rem" }} onClick={searchLoop} disabled={busy}>
                Search
              </button>
            </div>
            <SearchResults tracks={loopResults} pickLabel="Add" onPick={addSeed} />
            {seeds.length > 0 && (
              <>
                <TrackList tracks={seeds} onRemove={(id) => setSeeds((s) => s.filter((x) => x.id !== id))} />
                <button type="button" className="btn btn-full" onClick={runLoop} disabled={busy}>
                  Break the loop
                </button>
              </>
            )}
            {escapeTracks.length > 0 && <TrackList tracks={escapeTracks} />}
            <p className="hub-deep-link">
              Full experience → <Link href="/loop">Open Break My Loop</Link>
            </p>
          </>
        )}

        {error && <p className="error">{error}</p>}
      </div>
    </section>
  );
}
