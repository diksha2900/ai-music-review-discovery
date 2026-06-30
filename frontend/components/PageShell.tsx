import { Track } from "@/lib/api";

type Props = {
  variant?: "default" | "cousins" | "vibe" | "loop" | "about" | "home";
  title: React.ReactNode;
  subtitle?: string;
  children: React.ReactNode;
};

export function PageShell({ variant = "default", title, subtitle, children }: Props) {
  return (
    <section className={`page-shell page-${variant}`}>
      <div className="page-glow" aria-hidden />
      <header className="page-header">
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </header>
      {children}
    </section>
  );
}

export function NowPlayingCard({
  track,
  progress,
  onFindCousins,
  loading,
}: {
  track: Track;
  progress?: string;
  onFindCousins: () => void;
  loading?: boolean;
}) {
  return (
    <div className="card now-playing">
      <p className="section-label">Now playing on Spotify</p>
      <div className="track now-playing-inner">
        {track.album_art && <img src={track.album_art} alt="" className="np-art" />}
        <div className="track-meta">
          <strong>{track.name}</strong>
          <small>
            {track.artist}
            {progress ? ` · ${progress}` : ""}
          </small>
        </div>
      </div>
      <button type="button" className="btn btn-full" onClick={onFindCousins} disabled={loading}>
        {loading ? "Finding cousins…" : "✨ Find Cousins of this song"}
      </button>
    </div>
  );
}

export function SearchResults({
  tracks,
  onPick,
  pickLabel = "Select",
  loadingId,
}: {
  tracks: Track[];
  onPick: (t: Track) => void;
  pickLabel?: string;
  loadingId?: string;
}) {
  if (!tracks.length) return null;
  return (
    <div className="search-results">
      <p className="section-label">Pick a match from Spotify</p>
      <div className="track-grid">
        {tracks.map((t) => (
          <div key={t.id} className="card track track-row">
            {t.album_art && <img src={t.album_art} alt="" />}
            <div className="track-meta">
              <strong>{t.name}</strong>
              <small>{t.artist}</small>
            </div>
            <button
              type="button"
              className="btn btn-sm"
              onClick={() => onPick(t)}
              disabled={loadingId === t.id}
            >
              {loadingId === t.id ? "…" : pickLabel}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
