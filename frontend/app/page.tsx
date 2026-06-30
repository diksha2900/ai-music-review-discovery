"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getNowPlaying } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

export default function HomePage() {
  const { user, loading } = useAuth();
  const [nowPlaying, setNowPlaying] = useState<string | null>(null);

  useEffect(() => {
    if (user?.logged_in) {
      getNowPlaying().then((r) => {
        if (r.playing?.name) setNowPlaying(`${r.playing.name} — ${r.playing.artist}`);
      });
    }
  }, [user?.logged_in]);

  if (loading) return null;

  return (
    <section className="page-shell page-home">
      <div className="page-glow" aria-hidden />
      <div className="hero">
        <p className="hero-eyebrow">AI music discovery</p>
        <h1>
          VibePilot <span>AI</span>
        </h1>
        <p className="hero-tagline">Same feel, different blood.</p>

        {user?.logged_in ? (
          <>
            <p className="hero-welcome">
              Welcome back, <strong>{user.display_name || "listener"}</strong>.
              {nowPlaying ? (
                <>
                  {" "}
                  You&apos;re vibing to <em>{nowPlaying}</em> — find its cousins?
                </>
              ) : (
                <> Ready to discover something new?</>
              )}
            </p>
            <div className="hero-actions">
              <Link href="/cousins" className="btn btn-lg">
                ✨ Find Cousins
              </Link>
              <Link href="/vibe" className="btn btn-outline btn-lg">
                Start From Vibe
              </Link>
              <Link href="/loop" className="btn btn-outline btn-lg">
                Break My Loop
              </Link>
            </div>
          </>
        ) : (
          <>
            <p className="hero-desc">
              Give us a song you love — we&apos;ll find unheard songs with the same tempo, beat
              &amp; vibe.
            </p>
            <div className="hero-actions">
              <Link href="/cousins" className="btn btn-lg">
                ✨ Try it now
              </Link>
              <Link href="/about" className="btn btn-outline btn-lg">
                How it works
              </Link>
            </div>
            <p className="hero-footnote">No account needed for search. Log in from the sidebar for now-playing.</p>
          </>
        )}

        <div className="hero-pillars">
          <div className="pillar">
            <span>🥁</span>
            <h3>Same beat</h3>
            <p>Tempo &amp; energy matched via audio DNA</p>
          </div>
          <div className="pillar">
            <span>🎭</span>
            <h3>Same feel</h3>
            <p>Genre lane preserved — not random sad songs</p>
          </div>
          <div className="pillar">
            <span>🩸</span>
            <h3>New blood</h3>
            <p>Artists you haven&apos;t heard yet</p>
          </div>
        </div>
      </div>
    </section>
  );
}
