import { Track } from "@/lib/api";

type Props = {
  tracks: Track[];
  onRemove?: (id: string) => void;
};

export function TrackList({ tracks, onRemove }: Props) {
  if (!tracks.length) return null;
  return (
    <div className="track-grid">
      {tracks.map((t) => (
        <div key={`${t.id}-${t.name}`} className="card track track-row">
          {t.album_art ? (
            <img src={t.album_art} alt="" />
          ) : (
            <div className="track-art-placeholder" />
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
            {t.why && <small className="track-why">{t.why}</small>}
          </div>
          {onRemove && (
            <button type="button" className="btn-icon" onClick={() => onRemove(t.id)} title="Remove">
              ✕
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
