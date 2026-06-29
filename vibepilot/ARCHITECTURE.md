# VibePilot AI — Product & Technical Architecture

> **One feature, done well:** play a song you love → meet its **cousins** — unheard songs that match its **tempo, beat & feel**, from artists, eras, and countries you've never heard. Built for Spotify's Growth team to break repetitive listening.

---

## 1. Why this exists (one paragraph)

Spotify's recommendation engine optimizes for *not-skipping*, so it defaults users to familiar music in slightly rearranged order. As of 2026, Spotify has even **closed its algorithmic Web API endpoints** (Recommendations, Audio Features, Related Artists) to new apps. VibePilot flips the objective: instead of maximizing retention through familiarity, it **maximizes discovery within a feel**. It rebuilds the missing recommendation stack from two open sources — **Last.fm** for real human co-listening data and **ReccoBeats** for the audio features Spotify locked away — and uses an LLM only where language understanding genuinely helps (interpreting a vibe, naming a mood).

---

## 2. The problem (evidence-backed)

From our Review Discovery Engine (Part 1) + survey (Part 2):

| Theme | Evidence |
|---|---|
| **Recommendation Quality** | Largest discovery theme — "same songs," "worst recommendations," "feels random" |
| **Repetition Fatigue** | Users stuck replaying the same tracks; autoplay loops the already-heard |
| **Discovery Effort** | Users *want* new music but finding it is too much manual work → fall back to old playlists |
| **The core unmet need** | "I love *this* song — give me more that *sound and feel* like it, but that I've never heard." Autoplay and Song Radio answer with the same artist or known hits. |

**Root cause:** Spotify's objective function (engagement) makes repetition the *safe* default, and its similarity signals lean on the same artists/popularity. Genuine "same feel, new song" discovery is penalized because novelty raises short-term skip risk.

---

## 3. Target segment

**Repetition-Trapped Heavy Listeners** — open Spotify multiple times daily across distinct contexts (commute, gym, focus, relax). They want discovery, but the algorithm keeps them in a loop and keeps handing back the same artists.

---

## 4. The MVP: ONE feature — Cousins

> A *cousin* is a song that shares your track's **tempo, beat & mood** — its musical DNA — but comes from an artist, era, or country you've **never heard**. Not a remix, not the same singer. **Same feel, different blood.**

Everything in the app serves this one idea. The "sub-features" are just different ways in:

| Entry point | What happens |
|---|---|
| **Now playing** (primary) | App reads the track playing on your Spotify right now → one click → its cousins. |
| **Type any song** | Search any song → its cousins. |
| **Start from a vibe** (secondary, in a popup) | No song in mind? Pick a time-aware mood, an intent chip (Gym/Focus/Relax…), or describe it in emojis → a discovery playlist of unheard songs that fit. A *familiar ↔ new* slider controls adventurousness. |
| **Save** | Any result → a brand-new or an existing Spotify playlist, in one click. |

### Why this is the right MVP
- It targets the **exact unmet need** ("more like *this*, but new") that autoplay/radio fail.
- It's the only place where **real audio matching** (tempo/beat) + **real co-listening** + **hard novelty** combine — none of which Spotify exposes to the user as a single lever.

---

## 5. How a cousin is found (the engine)

```
ANCHOR SONG (now-playing or searched → real Spotify track, with track ID)
        │
        ▼
1. LANE     Last.fm track.getSimilar  → ~120 songs people who love this song also love
        │   (Bollywood-robust: tries composer + each singer, strips "(From …)")
        ▼
2. CLEAN    dedupe · drop the anchor's OWN artist (different blood) ·
        │   drop already-heard + already-shown-this-session · one per artist
        ▼
3. RESOLVE  each candidate → Spotify /search → real track (id, art, link)
        │
        ▼
4. GRADE    ReccoBeats audio-features for anchor + all candidates
        │   (tempo BPM, energy, danceability, acousticness, valence…)
        ▼
5. RANK     weighted distance to the anchor — TEMPO weighted highest —
        │   audio-graded songs first, ungraded only as filler
        ▼
TOP N COUSINS, each tagged with its real "🥁 ~120 BPM · acoustic · chill"
```

If Last.fm has no data for an obscure anchor, the engine falls back to the **LLM (Groq Llama 3.3 70B)** to propose same-feel candidates, which are then resolved the same way.

### Why AI is uniquely suited (deck argument)

| Traditional recsys | What this unlocks |
|---|---|
| Collaborative filtering returns the same artists / popular hits | Co-listening **lane** + **hard same-artist exclusion** forces genuinely new blood |
| Spotify's Audio Features API is now **closed** | ReccoBeats reconstructs **tempo/energy/feel**, so we can rank on the *actual beat*, not metadata |
| "Feels random" black box | Every cousin shows its **real BPM & feel tag**, proving the match |
| Can't cross language/era on "feeling" | Lane + audio match jump Hindi → Turkish → Portuguese while holding the tempo & mood |
| Vibe/mood input is unstructured | The **LLM** turns "🌧️😌☕" or "winding down after work" into concrete seed songs + mood tags |

---

## 6. Technical architecture

```
┌─────────────────────────────────────────────────────────────┐
│  STREAMLIT FRONTEND  (deployed to prod)                       │
│  • Login w/ Spotify   • Now-playing card   • Cousins results  │
│  • "Start from a vibe" popup (st.dialog)   • Save playlist    │
└──────┬───────────────┬───────────────┬───────────────┬───────┘
       │               │               │               │
 ┌─────▼─────┐  ┌──────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
 │ SPOTIFY   │  │  LAST.FM    │  │ RECCOBEATS │  │ VIBE ENGINE│
 │ CLIENT    │  │  CLIENT     │  │  CLIENT    │  │ (Groq LLM) │
 │ OAuth     │  │ getSimilar  │  │ audio-     │  │ vibe→seeds │
 │ search    │  │ tag.getTop  │  │ features   │  │ +tags,     │
 │ now-play  │  │ (co-listen) │  │ (tempo/    │  │ LLM        │
 │ playlists │  │             │  │  energy)   │  │ fallback   │
 └───────────┘  └─────────────┘  └────────────┘  └────────────┘
```

### Stack
- **Frontend:** Streamlit (Python-native, interactive, fast to deploy)
- **Music similarity (lane):** **Last.fm API** — `track.getSimilar`, `tag.getTopTracks` (real human co-listening)
- **Audio features (beat/feel):** **ReccoBeats API** — free, no-auth replacement for Spotify's deprecated Audio Features (tempo, energy, danceability, acousticness, valence…)
- **LLM:** Groq · Llama 3.3 70B — interprets vibe/emoji into seed songs + mood tags; fallback track proposals
- **Music graph + actions:** Spotify Web API — OAuth **Authorization Code** flow
- **Deploy:** Streamlit Community Cloud (HTTPS URL = OAuth redirect URI)

### Spotify endpoints used (all available in 2026)
`/me` · `/search` · `/me/player/currently-playing` · `/me/player/recently-played` · `/me/top/{artists,tracks}` · `/me/tracks` · `/me/playlists` · `/users/{id}/playlists` (create) · `/playlists/{id}/tracks` (add)

### Scopes
`user-read-private`, `user-read-currently-playing`, `user-read-recently-played`, `user-top-read`, `user-library-read`, `playlist-read-private`, `playlist-read-collaborative`, `playlist-modify-private`, `playlist-modify-public`

### Module layout
```
vibepilot/
├── ARCHITECTURE.md          ← this file
├── README.md                ← setup + run
├── requirements.txt
├── .streamlit/
│   ├── secrets.toml.example ← Spotify + Groq + Last.fm keys template
│   └── config.toml          ← theme
├── app.py                   ← Streamlit UI, cousins/vibe flows, ranking glue
├── auth.py                  ← Spotify OAuth (Authorization Code) flow
├── config.py                ← keys + scopes loader (env / st.secrets)
├── spotify_client.py        ← Spotify Web API wrapper (search, now-playing, playlists…)
├── lastfm_client.py         ← Last.fm: similar tracks + mood-tag tracks
├── reccobeats_client.py     ← ReccoBeats: audio features + distance/tag helpers
├── vibe_engine.py           ← Groq LLM: vibe→seeds/tags, time-band mood, fallback picks
└── capture.py               ← save to new / existing Spotify playlist
```

---

## 7. Anti-repetition & success metric

- **Hard exclusion:** recently-played + already-shown-this-session + the anchor's own artist are removed from the candidate pool before ranking, so the loop can't repeat and cousins are always new blood.
- **Success metric — Discovery Rate:** % of a result that is net-new artists (never in the user's recent/top). Cousins targets **~100% new artists** by design (same-artist is excluded), while holding tempo/feel close to the anchor.

---

## 8. Key risks & mitigations

| Risk | Mitigation |
|---|---|
| Spotify **Developer Mode** user cap (25) | Allowlist your account + grader's email — fine for a graded demo |
| Bollywood metadata mismatch (Spotify credits composer, Last.fm credits singer) | `_clean_title` + try composer **and** each singer until Last.fm matches |
| ReccoBeats missing an obscure track | Graded songs rank first; ungraded used only as filler; never blocks results |
| Last.fm has no data for a niche anchor | Fall back to LLM-proposed same-feel candidates, resolved via Search |
| LLM proposes non-existent tracks | Every pick resolved via Spotify Search; unresolved dropped |
| OAuth redirect on Streamlit Cloud | Register the Cloud HTTPS URL as a Redirect URI in the Spotify app |

---

## 9. Status & next steps

- ✅ Cousins engine (Last.fm lane → Spotify resolve → ReccoBeats tempo/beat ranking)
- ✅ Now-playing + type-a-song + vibe-popup entry points
- ✅ Save to new / existing playlist · session-long de-duplication
- ⏭️ Deploy to a public Streamlit URL + register prod redirect URI
- ⏭️ (Optional) "Catch That" passive capture — *product vision, not core MVP*
