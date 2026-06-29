# 🎧 VibePilot AI

> **Play a song you love → meet its _cousins_:** unheard songs that match its **tempo, beat & feel** — from artists, eras, and countries you've never heard. Same feel, different blood.

VibePilot is an AI-native discovery agent built to break Spotify's repetitive-listening loop. It rebuilds the recommendation stack Spotify closed off — using **Last.fm** for real human co-listening and **ReccoBeats** for the audio features (tempo/energy) Spotify deprecated — so it can rank songs by the *actual beat*, not metadata.

> See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full product + technical design.

## What it does

- **Cousins (the one feature)** — anchor on the song playing *right now*, or type any song, and get unheard songs that match its **tempo, beat & mood**. Each result is tagged with its real `🥁 ~120 BPM · acoustic · chill` so you can see the match. The anchor's own artist is excluded — cousins are always *new blood*.
- **Start from a vibe** *(secondary, in a popup)* — no song in mind? Pick a time-aware mood, an intent (Gym / Focus / Relax…), or describe it in emojis, and get a discovery playlist. A *familiar ↔ new* slider sets how adventurous it is.
- **Save** — any result → a new or existing Spotify playlist in one click.

## How a cousin is found

```
song → Last.fm "similar" (the lane) → resolve to Spotify
     → ReccoBeats grades tempo/energy/feel → rank by closeness to your song → top cousins
```
If Last.fm doesn't know an obscure song, an LLM (Groq Llama 3.3 70B) proposes same-feel candidates as a fallback.

## Stack
Streamlit · Spotify Web API (OAuth Authorization Code) · **Last.fm API** (co-listening) · **ReccoBeats API** (audio features, free/no-auth) · Groq · Llama 3.3 70B · deploys on Streamlit Community Cloud.

## Setup

1. **Spotify app** — create one at https://developer.spotify.com/dashboard
   - Add Redirect URIs: `http://127.0.0.1:8502` (local) and your `https://<app>.streamlit.app` URL (prod).
   - Select **Web API**. In Developer Mode, add each tester's Spotify email under *User Management*.
2. **Last.fm API key** — get one at https://www.last.fm/api/account/create (free).
3. **Groq key** — https://console.groq.com (free tier).
   *(ReccoBeats needs no key.)*
4. **Secrets** — `cp .streamlit/secrets.toml.example .streamlit/secrets.toml` and fill in:
   `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`, `GROQ_API_KEY`, `LASTFM_API_KEY`.
5. **Install + run**:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py --server.port 8502
   ```

## Deploy (Streamlit Community Cloud)
1. Push the repo to GitHub.
2. Create an app on https://share.streamlit.io pointing at `vibepilot/app.py`.
3. Paste the same keys into the app's **Secrets**, with `SPOTIFY_REDIRECT_URI` set to the `*.streamlit.app` URL.
4. Add that same URL as a Redirect URI in the Spotify dashboard.

## Status
✅ Cousins engine + vibe popup + save live locally. ⏭️ Production deploy is the next step.
