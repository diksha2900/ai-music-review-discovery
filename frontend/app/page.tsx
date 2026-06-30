"use client";

import Link from "next/link";
import { loginUrl } from "@/lib/api";

export default function HomePage() {
  return (
    <section className="hero">
      <h1>
        VibePilot <span>AI</span>
      </h1>
      <p>Same feel, different blood.</p>
      <p>
        Give us a song you love — we&apos;ll find unheard songs with the same tempo, beat &amp; vibe.
      </p>
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", marginTop: "2rem" }}>
        <Link href="/cousins" className="btn">
          ✨ Try it now
        </Link>
        <a href={loginUrl()} className="btn btn-outline">
          Log in with Spotify
        </a>
      </div>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: "0.75rem" }}>
        No account needed for search. Login unlocks now-playing &amp; save.
      </p>
    </section>
  );
}
