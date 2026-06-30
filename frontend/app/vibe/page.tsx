"use client";

import { useState } from "react";
import { getVibe, Track } from "@/lib/api";
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
    const vibe = `${emoji} ${text}`.trim();
    if (!vibe) return;
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
        Start from a <span style={{ color: "var(--green)" }}>vibe</span>
      </h1>
      <div className="mood-row">
        {MOODS.map((m) => (
          <button key={m.label} className="chip" onClick={() => pickMood(m)}>
            {m.emoji} {m.label}
          </button>
        ))}
      </div>
      <div className="card">
        <label style={{ display: "block", marginBottom: "0.5rem", color: "var(--muted)" }}>
          Emoji mood
        </label>
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
        <p style={{ color: "var(--muted)", margin: "1rem 0 0.5rem" }}>
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
        <button className="btn" style={{ marginTop: "1rem", width: "100%" }} onClick={submit} disabled={loading}>
          {loading ? "Building your vibe…" : "Get My Vibe"}
        </button>
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
