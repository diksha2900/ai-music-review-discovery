# VibePilot AI — Presentation Brief

> **One-line pitch:** Play a song you love → meet its **cousins** — unheard songs that match its **tempo, beat & feel**, from artists you've never heard. Same feel, different blood.

Use this doc for slides, speaker notes, or submission write-ups.

---

## 1. The Problem (Evidence-Backed)

Spotify's recommendation engine optimizes for **retention**, not discovery. Heavy listeners end up in a loop:


| Pain                   | What users experience                                                                         |
| ---------------------- | --------------------------------------------------------------------------------------------- |
| **Repetition fatigue** | Same 3–4 songs appear in autoplay, radio, and AI DJ                                           |
| **Discovery effort**   | Finding genuinely new music that *fits* takes manual work → people fall back to old playlists |
| **Wrong "similar"**    | Song Radio matches artist/genre, not **felt similarity** (tempo, beat, mood)                  |
| **Capture loss**       | A great unknown track plays while driving/gym — by the time you can act, it's gone            |


**Our review analysis** (Discovery Engine, n=1,490+ classified records) confirmed **Recommendation Quality** and **Repetition Fatigue** as the top discovery-related themes.

**Target segment:** Repetition-trapped heavy listeners — people who open Spotify multiple times daily across different contexts (commute, gym, focus, relax) and want discovery but keep hearing the same artists.

---

## 2. Why Traditional Spotify Features Fall Short


| Spotify feature     | Limitation                                                          |
| ------------------- | ------------------------------------------------------------------- |
| Autoplay / AI DJ    | Recycles familiar tracks; optimizes for not-skipping                |
| Song / Artist Radio | Same artist pool; metadata-based, not beat/tempo DNA                |
| Discover Weekly     | Weekly batch, not moment-of-love for *this specific song*           |
| Audio Features API  | **Closed to new apps in 2026** — no tempo/BPM access for developers |


**Gap we fill:** At the moment you love *this* song, get *unheard* songs that share its **musical DNA** (tempo, energy, feel) — not its artist or lyrics.

---

## 3. Our Solution: ONE Feature — **Cousins**

### What is a cousin?

> A song that shares your track's **tempo, beat & mood** — its musical DNA — but comes from an artist, era, or country you've **never heard**. Not a remix. Not the same singer. **Same feel, different blood.**

Everything in VibePilot serves this one idea. Sub-features are just different ways in:


| Entry point                    | Who it's for                                                                            |
| ------------------------------ | --------------------------------------------------------------------------------------- |
| **Now playing → Find cousins** | Logged-in user; song playing on Spotify right now                                       |
| **Search → Find cousins**      | Anyone (guest or logged-in); type song → pick from Spotify results                      |
| **Break my loop**              | Guest or logged-in; add 2+ songs you repeat → get unheard alternatives in the same vibe |
| **Start from a vibe** (popup)  | No song in mind; pick mood/intent/emojis → discovery playlist                           |


---

## 4. Did We Solve It?

### ✅ What we solved


| Problem                      | How VibePilot addresses it                                                           |
| ---------------------------- | ------------------------------------------------------------------------------------ |
| Repetitive listening         | **Hard exclusion** — anchor artist + already-shown songs removed from results        |
| Wrong "similar" songs        | **ReccoBeats** ranks by real tempo/BPM, energy, danceability — not just co-listening |
| Cross-language/era discovery | Last.fm lane + audio matching jumps Hindi → Turkish → indie while holding feel       |
| Evaluators can't log in      | **Guest mode** — full cousins + break-my-loop without Spotify account                |
| Trust ("why this song?")     | Each cousin tagged: `🥁 ~118 BPM · acoustic · chill`                                 |
| Save discoveries             | Logged-in users save to new or existing Spotify playlist                             |


### ⚠️ Honest limitations (say these in Q&A — shows maturity)


| Limitation                                         | Why                                                               |
| -------------------------------------------------- | ----------------------------------------------------------------- |
| Spotify login capped at **~5 testers** in Dev Mode | Spotify policy; guest mode is the public demo path                |
| Now-playing + save need login                      | Spotify API requires user OAuth for personal data                 |
| Can't read someone's playlist without login        | Spotify blocks playlist contents for anonymous access             |
| ReccoBeats may miss obscure regional tracks        | Falls back to Last.fm order for those candidates                  |
| Not true "analyze this 10-second clip"             | Would need audio segmentation + DSP; MVP matches whole-track feel |


---

## 5. How It Works (Technical — for one slide)

```
ANCHOR SONG (now playing or user picks from Spotify search)
        │
        ▼
① LANE      Last.fm track.getSimilar → ~120 songs in the same listening lane
        │   (Bollywood-robust: tries composer + each singer name)
        ▼
② CLEAN     Remove anchor's artist · already-heard · duplicates · one per artist
        ▼
③ RESOLVE   Each candidate → Spotify Search → real track (id, art, link)
        ▼
④ GRADE     ReccoBeats audio-features: tempo, energy, danceability, acousticness
        ▼
⑤ RANK      Weighted distance to anchor — TEMPO weighted highest
        ▼
TOP 8 COUSINS — each with BPM/feel tag proving the match
```

**Break my loop:** Same pipeline, but anchor = **average feel** of 2–8 songs the user keeps repeating → returns unheard songs in that combined vibe, excluding all those artists.

**Vibe mode (popup):** LLM (Groq Llama 3.3 70B) picks seed songs + mood tags → Last.fm expands → same ranking/filtering.

---

## 6. Why AI Is Uniquely Suited


| Traditional recsys                             | What we unlock                                              |
| ---------------------------------------------- | ----------------------------------------------------------- |
| Collaborative filtering → same popular artists | Lane + **hard same-artist exclusion** → genuinely new blood |
| Spotify closed Audio Features API              | **ReccoBeats** reconstructs tempo/energy for ranking        |
| Black-box recommendations                      | Visible **BPM tags** build trust                            |
| Can't interpret "🌧️😌☕" or "gym at 7am"       | **LLM** turns free text/emojis into searchable seeds        |
| Can't cross language on metadata alone         | Semantic vibe + audio matching spans genre/era/region       |


---

## 7. Stack


| Layer            | Technology                                                     |
| ---------------- | -------------------------------------------------------------- |
| Frontend         | Streamlit (Python, deployable to Streamlit Cloud)              |
| Music similarity | **Last.fm API** — real human co-listening data                 |
| Audio features   | **ReccoBeats API** — free, no-auth; tempo/BPM/energy           |
| LLM              | Groq · Llama 3.3 70B — vibe interpretation, fallback picks     |
| Music graph      | Spotify Web API — OAuth, search, now-playing, playlists        |
| Auth             | Spotify Authorization Code + Client Credentials (guest search) |


---

## 8. User Flows (Demo Script)

### For evaluators (Guest — no login)

1. Open link → **✨ Try it now — no login**
2. Read "What's a cousin?" definition
3. Type `kabira` → **Search** → pick from green Spotify results → **Find cousins**
4. Scroll to **Break my loop** → add 2 repeating songs → get discovery playlist
5. *(Optional)* open **Start from a vibe** popup → pick Gym/Relax → playlist

### For your demo video (Logged in)

1. Play a song on Spotify → refresh VibePilot → **✨ find cousins** on now-playing card
2. Show BPM tags matching anchor song
3. **Save to Spotify playlist** → show it in Spotify app
4. Contrast: "Spotify radio would give same artist; we gave [different artist, same BPM]"

---

## 9. Metrics / Success Criteria

- **Discovery Rate:** % of results from artists not in user's recent/top (cousins targets ~100% new artists by design)
- **Feel match:** User validates BPM tags align with anchor (qualitative in demo)
- **Session freshness:** Same songs don't repeat across generations (session exclusion list)

---

## 10. Product Positioning (One Slide)

**Before:** Spotify defaults to familiar. Discovery is effort. "Similar" ≠ same feel.

**After (VibePilot):** One tap from the song you love → unheard cousins that match its **tempo, beat & mood**. Guest-accessible. Logged-in users get now-playing + save.

**Tagline:** *Same feel, different blood.*

---

## 11. What's Built vs What's Next


| Status      | Item                                                      |
| ----------- | --------------------------------------------------------- |
| ✅ Done      | Cousins engine (Last.fm + ReccoBeats ranking)             |
| ✅ Done      | Guest mode + Break my loop + Spotify search picker        |
| ✅ Done      | Now-playing + save to playlist (logged-in)                |
| ✅ Done      | Vibe/mood popup (secondary path)                          |
| ⏭️ Next     | Deploy to public Streamlit URL                            |
| ⏭️ Optional | "Catch That" voice capture (product vision, not core MVP) |


---

## 12. Suggested Slide Outline (10 slides)

1. **Title** — VibePilot AI · Same feel, different blood
2. **Problem** — Repetition fatigue + discovery gap (with review data)
3. **Target user** — Heavy multi-session listeners
4. **Insight** — Users want "more like *this song*" not "more like *this artist*"
5. **Solution** — Cousins: one feature, multiple entry points
6. **Demo screenshot** — Search → cousins with BPM tags
7. **How it works** — Pipeline diagram (§5 above)
8. **Why AI** — Table from §6
9. **Validation** — Guest mode for evaluators; logged-in for full demo
10. **Impact & next steps** — Deploy, measure Discovery Rate, Spotify partnership pitch

---

## 13. Adding Spotify Developer Testers (Allow-List)

Your app is in **Development Mode**. Only emails you add can log in with Spotify.

### Steps

1. Go to **[https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)**
2. Log in with the account that owns the app
3. Click your **VibePilot** app
4. Open **Settings** (gear icon, top right)
5. Go to the **User Management** tab
6. Click **Add new user**
7. Enter:
  - **Name:** person's name (any label)
  - **Email:** their **Spotify account email** (must match exactly)
8. Click **Add** / **Save**

### Important rules

- The email must be the one on their **Spotify profile** (spotify.com → Account → Edit profile)
- If they signed up via Google/Apple, use that linked email
- **Cap:** Spotify currently limits Dev Mode apps (you may see **5 users**, not 25 — this varies)
- **Guest mode does NOT need allow-listing** — unlimited evaluators can use cousins search + break my loop
- Allow-list is only for: now-playing, save to playlist, personalized exclusion

### If you need more than 5 logins

- Apply for **Extended Quota Mode** in Spotify Dashboard (manual review, slow, not guaranteed for student projects)
- **Recommended:** Guest mode for all evaluators + 1–2 allow-listed accounts for live demo video

---

## 14. Elevator Pitch (30 seconds)

*"Spotify keeps playing what you already know. VibePilot does one thing: you give it a song you love, and it finds its **cousins** — songs you've never heard that share the same tempo, beat, and mood. We use real co-listening data and audio feature matching because Spotify locked their algorithm API. Evaluators can try it instantly without logging in; logged-in users get now-playing detection and one-click playlist save. It's discovery by **feel**, not by artist."*