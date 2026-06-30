"use client";

import { useMemo, useState } from "react";
import { getVibe, Track } from "@/lib/api";
import { getTimeBand } from "@/lib/timeBand";
import { TrackList } from "@/components/TrackList";

const MOODS = [
  { emoji: "😌", label: "Chill" },
  { emoji: "🏋️", label: "Gym" },
  { emoji: "🌧️", label: "Rain" },
  { emoji: "🚗", label: "Drive" },
  { emoji: "🌙", label: "Late Night" },
  { emoji: "📚", label: "Focus" },
  { emoji: "💔", label: "Heartbreak" },
  { emoji: "✨", label: "Main Character" },
];

export default function VibePage() {
  const band = useMemo(() => getTimeBand(new Date()), []);
  const [text, setText] = useState("");
  const [emoji, setEmoji] = useState("");
  const [familiarity, setFamiliarity] = useState(5);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function pickMood(m: (typeof MOODS)[0]) {
    setText(`${m.emoji} ${m.label.toLowerCase()}`);
  }

  async function submit() {
    let vibe = `${emoji} ${text}`.trim();
    if (!vibe) {
      vibe = band.vibe;
    }
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
    <section>
      <h1>
        Start from a <span className="accent">vibe</span>
      </h1>

      <div className="moment-card">
        <p className="moment-time">IT&apos;S {band.clock}</p>
        <p className="moment-mood">{band.mood}</p>
      </div>

      <div className="mood-row">
        {MOODS.map((m) => (
          <button key={m.label} type="button" className="chip" onClick={() => pickMood(m)}>
            {m.emoji} {m.label}
          </button>
        ))}
      </div>
      <div className="card">
        <label className="field-label">Emoji mood</label>
        <input
          type="text"
          placeholder="🌧️😌☕"
          value={emoji}
          onChange={(e) => setEmoji(e.target.value)}
          style={{ marginBottom: "1rem" }}
        />
        <input
          type="text"
          placeholder="Rainy evening, coffee, soft heartbreak…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <p className="muted" style={{ margin: "1rem 0 0.5rem" }}>
          How adventurous? {familiarity <= 3 ? "Adventurous" : familiarity >= 8 ? "Familiar" : "Balanced"}
        </p>
        <input
          type="range"
          min={1}
          max={10}
          value={familiarity}
          onChange={(e) => setFamiliarity(Number(e.target.value))}
          style={{ width: "100%", accentColor: "var(--green)" }}
        />
        <button type="button" className="btn" style={{ marginTop: "1rem", width: "100%" }} onClick={submit} disabled={loading}>
          {loading ? "Building your vibe…" : "Get My Vibe"}
        </button>
        {!text && !emoji && (
          <p className="muted" style={{ marginTop: "0.75rem", fontSize: "0.85rem" }}>
            No input? We&apos;ll use your time-of-day vibe: {band.label}
          </p>
        )}
        {error && <p className="error">{error}</p>}
      </div>
      {tracks.length > 0 && (
        <div style={{ marginTop: "1.5rem" }}>
          <h2>Your session</h2>
          <TrackList tracks={tracks} />
        </div>
      )}
    </section>
  );
}
