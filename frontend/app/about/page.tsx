import { PageShell } from "@/components/PageShell";

export default function AboutPage() {
  return (
    <PageShell variant="about" title="About VibePilot" subtitle="Same feel, different blood.">
      <div className="about-grid">
        <div className="card glass">
          <h2 className="section-heading">What is VibePilot?</h2>
          <p className="about-text">
            VibePilot is an AI music discovery engine that finds songs with the same tempo, beat, and
            emotional feel — but from artists you haven&apos;t heard yet. Not another playlist of your
            top artists. Not genre-only radio. Musical cousins.
          </p>
        </div>

        <div className="card glass">
          <h2 className="section-heading">How it works</h2>
          <ul className="about-list">
            <li>
              <strong>Find Cousins</strong> — Pick a song you love. We match its audio DNA (BPM,
              energy, danceability) and genre lane, then surface unheard tracks that feel the same.
            </li>
            <li>
              <strong>Start From Vibe</strong> — No song in mind? Tell us the moment (time of day,
              emojis, mood) and we build a discovery session around it.
            </li>
            <li>
              <strong>Break My Loop</strong> — Paste songs you repeat on loop. We find fresh tracks
              with the combined feel of your rut.
            </li>
          </ul>
        </div>

        <div className="card glass">
          <h2 className="section-heading">Under the hood</h2>
          <p className="about-text">
            Spotify for search &amp; catalog · Last.fm for real co-listening similarity · ReccoBeats
            for tempo/energy features · Groq LLM for vibe planning and fallbacks. Log in with Spotify
            from the sidebar to unlock now-playing and personalized taste exclusion.
          </p>
        </div>

        <div className="card glass">
          <h2 className="section-heading">Built for</h2>
          <p className="about-text">
            Listeners stuck in repetition loops who want discovery without losing the feeling — gym
            energy that stays gym energy, heartbreak that stays heartbreak, hip-hop that stays
            hip-hop.
          </p>
        </div>
      </div>
    </PageShell>
  );
}
