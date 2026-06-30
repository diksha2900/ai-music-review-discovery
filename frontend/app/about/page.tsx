import { loginUrl } from "@/lib/api";

export default function AboutPage() {
  return (
    <section>
      <h1>About VibePilot</h1>
      <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>
        VibePilot finds songs with the same tempo, beat, and emotional feel — but from artists you
        haven&apos;t heard. Built on Spotify search, Last.fm co-listening graphs, ReccoBeats audio
        features, and Groq LLM fallbacks.
      </p>
      <p style={{ marginTop: "2rem" }}>
        <a href={loginUrl()} className="btn">
          Log in with Spotify
        </a>
      </p>
    </section>
  );
}
