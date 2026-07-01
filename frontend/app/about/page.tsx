import { PageShell } from "@/components/PageShell";

export default function AboutPage() {
  return (
    <PageShell variant="about" title="About VibePilot" subtitle="Same feel, different artists.">
      <div className="about-grid">
        <div className="card glass">
          <h2 className="section-heading">What is VibePilot?</h2>
          <p className="about-text">
            VibePilot finds songs with the same tempo, beat, and emotional feel — but from artists
            you haven&apos;t heard yet. Our hero feature is <strong>Find Cousins</strong>: one song
            in, unheard matches out.
          </p>
        </div>

        <div className="card glass">
          <h2 className="section-heading">How it works</h2>
          <ul className="about-list">
            <li>
              <strong>Find Cousins</strong> — Pick a song. We match tempo, energy, and genre, then
              surface tracks you likely haven&apos;t heard.
            </li>
            <li>
              <strong>Start From Vibe</strong> — No song in mind? Tell us the moment.
            </li>
            <li>
              <strong>Break My Loop</strong> — Stuck on repeat? Escape without losing the feel.
            </li>
          </ul>
        </div>

        <div className="card glass coming-soon">
          <p className="section-label">Coming soon</p>
          <h2 className="section-heading">Catch That</h2>
          <p className="about-text">
            When a song hits while you&apos;re driving, at the gym, or can&apos;t search — capture
            it hands-free. We&apos;re building voice-first discovery for those moments.
          </p>
        </div>

        <div className="card glass">
          <h2 className="section-heading">Under the hood</h2>
          <p className="about-text">
            Spotify · Last.fm co-listening · ReccoBeats audio features · Groq LLM fallbacks. Log in
            from the home page for now-playing and personalized exclusion.
          </p>
        </div>
      </div>
    </PageShell>
  );
}
