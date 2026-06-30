"use client";

import { useMemo, useState } from "react";
import { getVibe, Track } from "@/lib/api";
import { getTimeBand } from "@/lib/timeBand";
import { PageShell } from "@/components/PageShell";
import { TrackList } from "@/components/TrackList";

const MOODS = [
  { emoji: "😌", label: "Chill", vibe: "chill, relaxed, mellow music" },
  { emoji: "🏋️", label: "Gym", vibe: "high energy workout gym music" },
  { emoji: "🌧️", label: "Rain", vibe: "rainy day cozy introspective music" },
  { emoji: "🚗", label: "Drive", vibe: "upbeat long drive sing-along music" },
  { emoji: "🌙", label: "Late Night", vibe: "late night slow emotional music" },
  { emoji: "📚", label: "Focus", vibe: "focus study instrumental calm music" },
  { emoji: "💔", label: "Heartbreak", vibe: "sad heartbreak emotional music" },
  { emoji: "✨", label: "Main Character", vibe: "main character energy cinematic music" },
];

export default function VibePage() {
  const band = useMemo(() => getTimeBand(new Date()), []);
  const [text, setText] = useState("");
  const [emoji, setEmoji] = useState("");
  const [familiarity, setFamiliarity] = useState(5);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(vibeOverride?: string) {
    let vibe = vibeOverride || `${emoji} ${text}`.trim();
    if (!vibe) vibe = band.vibe;
    setError("");
    setLoading(true);
    try {
      const data = await getVibe(vibe, familiarity);
      setTracks(data.tracks);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell
      variant="vibe"
      title={
        <>
          Start from a <span className="accent">vibe</span>
        </>
      }
      subtitle="Your moment, your mood — we build a discovery playlist around it."
    >
      <button
        type="button"
        className="moment-card moment-card-click"
        onClick={() => submit(band.vibe)}
        disabled={loading}
      >
        <p className="moment-time">IT&apos;S {band.clock}</p>
        <p className="moment-mood">{band.mood}</p>
        <p className="moment-cta">{loading ? "Building…" : "Tap for your time-of-day vibe →"}</p>
      </button>

      <p className="section-label">Or pick a mood</p>
      <div className="mood-row">
        {MOODS.map((m) => (
          <button
            key={m.label}
            type="button"
            className="chip"
            onClick={() => {
              setEmoji(m.emoji);
              setText(m.label.toLowerCase());
            }}
          >
            {m.emoji} {m.label}
          </button>
        ))}
      </div>

      <div className="card glass">
        <label className="field-label">Emoji mood</label>
        <p className="field-hint">Express the feeling in emojis — rain, coffee, heartbreak, party…</p>
        <input
          type="text"
          placeholder="🌧️😌☕ or 🔥🕺🎉"
          value={emoji}
          onChange={(e) => setEmoji(e.target.value)}
          style={{ marginBottom: "1.25rem" }}
        />

        <label className="field-label">Describe your mood</label>
        <p className="field-hint">A short scene works best — rainy evening, coffee, soft heartbreak…</p>
        <input
          type="text"
          placeholder="Rainy evening, coffee, soft heartbreak…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        <p className="field-label" style={{ marginTop: "1.25rem" }}>
          How adventurous?{" "}
          <span className="accent">
            {familiarity <= 3 ? "Adventurous" : familiarity >= 8 ? "Familiar" : "Balanced"}
          </span>
        </p>
        <p className="field-hint">Left = deep cuts. Right = comfort picks you already love.</p>
        <input
          type="range"
          min={1}
          max={10}
          value={familiarity}
          onChange={(e) => setFamiliarity(Number(e.target.value))}
          className="range"
        />
        <button type="button" className="btn btn-full" style={{ marginTop: "1rem" }} onClick={() => submit()} disabled={loading}>
          {loading ? "Building your vibe…" : "Get My Vibe"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>

      {tracks.length > 0 && (
        <div className="results-block">
          <h2 className="section-heading">Your session</h2>
          <TrackList tracks={tracks} />
        </div>
      )}
    </PageShell>
  );
}
