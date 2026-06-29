# Deploy VibePilot to Streamlit Community Cloud

## 1. Push code to GitHub

The `vibepilot/` folder must be on GitHub (repo: `diksha2900/ai-music-review-discovery`).

## 2. Create the app on Streamlit Cloud

1. Go to **https://share.streamlit.io**
2. Sign in with **GitHub**
3. Click **New app**
4. Fill in:
   - **Repository:** `diksha2900/ai-music-review-discovery`
   - **Branch:** `main`
   - **Main file path:** `vibepilot/app.py`
5. Click **Deploy** (it will fail first time until secrets are set — that's normal)

## 3. Add secrets

In the Streamlit Cloud app → **Settings** → **Secrets**, paste (replace with your real values):

```toml
SPOTIFY_CLIENT_ID = "your_client_id"
SPOTIFY_CLIENT_SECRET = "your_client_secret"
SPOTIFY_REDIRECT_URI = "https://YOUR-APP-NAME.streamlit.app"
GROQ_API_KEY = "your_groq_key"
LASTFM_API_KEY = "your_lastfm_key"
```

Copy values from your local `vibepilot/.streamlit/secrets.toml`.

**Important:** After deploy, copy your **exact** public URL from the browser (e.g. `https://vibepilot-ai.streamlit.app`) and set `SPOTIFY_REDIRECT_URI` to that URL in Secrets, then **Reboot app**.

## 4. Spotify Developer Dashboard

1. **https://developer.spotify.com/dashboard** → your app → **Settings**
2. Under **Redirect URIs**, add:
   ```
   https://YOUR-APP-NAME.streamlit.app
   ```
   (Must match `SPOTIFY_REDIRECT_URI` in Streamlit secrets **exactly** — no trailing slash)
3. Keep `http://127.0.0.1:8502` for local dev
4. Save

## 5. Verify

- Open your public URL
- **Guest:** Try it now → search a song → cousins
- **Login:** Log in with Spotify (allow-listed email only in Dev Mode)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Login redirect error | Redirect URI mismatch — URL in Spotify must match secrets exactly |
| Guest search fails | Check secrets have valid Spotify Client ID/Secret |
| App won't start | Logs in Streamlit Cloud → check requirements install |
| Only 5 users can log in | Dev Mode cap — use guest mode for evaluators |
