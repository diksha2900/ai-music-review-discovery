import { Track } from "../lib/api";

export function TrackList({ tracks }: { tracks: Track[] }) {
  if (!tracks.length) return null;
  return (
    <div className="track-grid">
      {tracks.map((t) => (
        <div key={`${t.id}-${t.name}`} className="card track">
          {t.album_art ? (
            <img src={t.album_art} alt="" />
          ) : (
            <div style={{ width: 56, height: 56, background: "var(--border)", borderRadius: 6 }} />
          )}
          <div className="track-meta">
            <strong>
              {t.url ? (
                <a href={t.url} target="_blank" rel="noreferrer">
                  {t.name}
                </a>
              ) : (
                t.name
              )}
            </strong>
            <small>{t.artist}</small>
            {t.why && <small style={{ color: "var(--green)", marginTop: 4 }}>{t.why}</small>}
          </div>
        </div>
      ))}
    </div>
  );
}
