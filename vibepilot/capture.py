"""Playlist creation + Catch That capture.

Phase 3: save a generated session as a real, ownable Spotify playlist.
Phase 4: capture the currently-playing track into a running "Caught" playlist.
"""

import spotify_client

CAUGHT_PLAYLIST_NAME = "Caught by VibePilot"


def save_session_as_playlist(name: str, tracks: list[dict], description: str = "") -> dict:
    """Create a playlist and add the session's tracks. Returns the playlist object."""
    uris = [t["uri"] for t in tracks if t.get("uri")]
    if not uris:
        raise ValueError("No tracks to save.")
    playlist = spotify_client.create_playlist(
        name=name,
        description=description or "Built by VibePilot AI — fresh, taste-anchored discovery.",
        public=False,
    )
    spotify_client.add_tracks(playlist["id"], uris)
    return playlist


def add_to_existing_playlist(playlist_id: str, tracks: list[dict]):
    """Append the session's tracks to an existing playlist."""
    uris = [t["uri"] for t in tracks if t.get("uri")]
    if not uris:
        raise ValueError("No tracks to add.")
    spotify_client.add_tracks(playlist_id, uris)


def ensure_caught_playlist() -> dict:
    """Find or create the running 'Caught by VibePilot' playlist (Phase 4)."""
    # Implemented in Phase 4.
    return spotify_client.create_playlist(
        name=CAUGHT_PLAYLIST_NAME,
        description="Songs you caught hands-free with VibePilot.",
        public=False,
    )
