"""LLM vibe engine (Groq · Llama 3.3 70B) — the discovery core.

The core idea: COUSINS. Given an anchor (a song, a free-text vibe, an intent, or
the currently-playing moment), the LLM reveals real songs that belong to the same
musical *family* — same emotional + sonic DNA — but that the listener has almost
certainly never heard: any era, any country, hidden gems and under-the-radar
artists. It reasons about felt similarity (mood, rhythm, groove, texture), not
audio features or collaborative filtering.

Spotify deprecated Audio Features / Audio Analysis for new apps, so the LLM's
musical knowledge replaces that DSP layer entirely — and reasoning about emotional
lineage across eras/languages is something audio matching fundamentally cannot do.
"""

import datetime
import json

from groq import Groq

from config import get_groq_api_key

MODEL = "llama-3.3-70b-versatile"
_client = None


def _groq():
    global _client
    if _client is None:
        key = get_groq_api_key()
        if not key:
            raise RuntimeError("GROQ_API_KEY missing — add it in Streamlit Secrets.")
        _client = Groq(api_key=key)
    return _client

INTENT_PRESETS = {
    "🚗 Driving": "an upbeat long drive — energetic, feel-good, sing-along momentum. Not slow or sad.",
    "💪 Gym": "a high-energy workout — intense, hard-hitting, fast, motivating. Definitely not mellow.",
    "🎯 Focus": "deep focus work — calm, steady, low-distraction, mostly soft or instrumental.",
    "🌙 Relax": "winding down — soft, warm, mellow, soothing, low energy.",
    "🍵 Chilling": "chilled-out and laid-back — easy-going, breezy, relaxed but not sad.",
    "🕺 Dance": "a dance party — HIGH ENERGY, upbeat, danceable, infectious beat you can move to, joyful. NEVER slow, sad or emotional songs.",
    "☀️ Happy": "happy and uplifting — sunny, feel-good, bright, cheerful energy.",
    "🧭 Explore": "pure discovery — fresh, surprising, adventurous new music; energy can vary but it must feel exciting and new.",
}


def time_band_vibe(now: datetime.datetime | None = None) -> dict:
    """Time-of-day suggestion: a friendly line + the vibe phrase to generate from."""
    h = (now or datetime.datetime.now()).hour
    if 5 <= h < 9:
        return {"mood": "Early morning — ease in, calm and spiritual.",
                "vibe": "calm, peaceful, spiritual early-morning music", "label": "morning calm"}
    if 9 <= h < 12:
        return {"mood": "Morning — easy, feel-good momentum to start the day.",
                "vibe": "easy, uplifting, feel-good morning music", "label": "feel-good morning"}
    if 12 <= h < 17:
        return {"mood": "Afternoon break — want something light and fun?",
                "vibe": "light, fun, upbeat afternoon pick-me-up", "label": "afternoon fun"}
    if 17 <= h < 21:
        return {"mood": "Evening — keep the energy up, maybe a drive?",
                "vibe": "upbeat, high-energy evening drive music", "label": "evening energy"}
    return {"mood": "Night — time to slow down and relax.",
            "vibe": "relaxing, mellow, soothing late-night music", "label": "late-night relax"}


def _familiarity_guidance(familiarity: int) -> str:
    if familiarity <= 2:
        return ("Make ALMOST EVERY song one the listener has likely NEVER heard — lesser-known "
                "artists and deep cuts. At most 0-1 familiar songs.")
    if familiarity <= 5:
        return ("Mostly songs the listener hasn't heard, with just 1-2 familiar favorites that "
                "fit the vibe as comfortable anchors.")
    if familiarity <= 8:
        return "A balanced mix of the listener's familiar favorites and new discoveries, all on-vibe."
    return ("Mostly the listener's familiar favorites that fit the vibe, with only a couple of "
            "new ones sprinkled in.")


def _known_block(taste: dict | None, exclude_names=None) -> str:
    """Tell the model what the listener ALREADY knows (cousins must avoid these)."""
    lines = []
    if taste:
        if taste.get("top_artists"):
            lines.append("Artists they already listen to: " + ", ".join(taste["top_artists"][:20]))
        if taste.get("top_genres"):
            lines.append("Their taste / genres (stay in THIS lane): " + ", ".join(taste["top_genres"][:10]))
    if exclude_names:
        lines.append("Already heard or shown (NEVER include): " + "; ".join(list(exclude_names)[:45]))
    if not lines:
        return ""
    return (
        "\n\nThe listener's taste — recommend the KIND of music they love, but songs they "
        "haven't heard. Do NOT recommend these exact artists/songs:\n- " + "\n- ".join(lines)
    )


def _taste_anchor_block(taste: dict | None) -> str:
    """For vibe sessions: capture the listener's SENSIBILITY (genres/artists), not exact songs.

    Note: we deliberately do NOT list their favorite tracks here — listing them makes the
    model echo the same handful of songs into every playlist.
    """
    lines = []
    if taste:
        if taste.get("top_artists"):
            lines.append("Artists that show their taste: " + ", ".join(taste["top_artists"][:15]))
        if taste.get("top_genres"):
            lines.append("Genres / lane: " + ", ".join(taste["top_genres"][:10]))
    if not lines:
        return ""
    return ("\n\nThe listener's taste lane (use ONLY to judge sensibility — do not just "
            "recommend these exact artists every time):\n- " + "\n- ".join(lines))


# ---------------------------- Cousins (a song) ----------------------------

def build_cousins_prompt(anchor_song, n, taste=None, exclude_names=None, moment=None):
    moment_block = ""
    if moment:
        moment_block = (
            f"\n\nThe listener pressed this at a specific moment in the song ({moment}). "
            "Anchor on that exact section's RHYTHM, GROOVE, tempo feel, energy and instrumentation."
        )

    return f"""You are VibePilot, a deeply knowledgeable music curator.

The listener is enjoying this song: "{anchor_song}".{moment_block}

Reveal its COUSINS — {n} real songs this listener has almost certainly NEVER heard, that \
feel like they belong to the SAME musical family.

THE #1 RULE — VIBE LOCK (most important):
First, silently identify the anchor song's exact lane — its mood, energy, tempo feel, \
instrumentation and emotional tone (e.g. "soft, melancholic Hindi indie with gentle guitar"). \
Then EVERY cousin must clearly live in that SAME lane.
- If the anchor is soft / mellow / acoustic / emotional, every cousin must also be soft and \
mellow — NEVER a rap track, party/dance number, item song, or anything loud or aggressive.
- Do NOT switch genre, language or energy just to seem diverse. Matching the FEELING beats variety.

A good cousin:
- A DIFFERENT artist from the anchor.
- Genuinely undiscovered for this listener — hidden gems, deep cuts, under-the-radar artists, NOT chart hits.
- Old OR new — both fine, as long as the feeling matches exactly.
- Within the listener's sensibility (their genres below) — the kind of music they'd love.

Crossing language/region is allowed ONLY when the feeling is genuinely identical (e.g. a \
mellow Pakistani acoustic track as cousin to a mellow Hindi indie one). When unsure, stay in \
the anchor's exact lane and language.{_known_block(taste, exclude_names)}

Hard rules:
- Real songs by real artists only. NEVER invent songs.
- Same vibe/feeling as the anchor above ALL else — no off-vibe genres.
- No duplicate artists.

Return ONLY a JSON object with a "tracks" array of exactly {n} items:
{{"tracks": [
  {{"title": "<exact track title>", "artist": "<primary artist>", "why": "<one line: the shared feeling + a hint of era/origin, max 16 words>"}}
]}}"""


def propose_cousins(anchor_song, n=8, taste=None, exclude_names=None, moment=None):
    """Cousins of a SPECIFIC song — same vibe, unheard. Returns [{title,artist,why}]."""
    prompt = build_cousins_prompt(anchor_song, n, taste, exclude_names, moment)
    resp = _groq().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.65,
        max_tokens=min(2600, 500 + n * 100),
        response_format={"type": "json_object"},
    )
    return _parse_tracks(resp)


# ------------------------ Vibe session (a moment) -------------------------

def build_vibe_session_prompt(vibe_text, n, taste=None, usual_tracks=None, exclude_names=None, familiarity=5):
    usual_block = ""
    if usual_tracks:
        usual_block = (
            "\n\nAround this time the listener tends to play songs like these — use ONLY the ones "
            "that match the vibe above as a sensibility hint:\n- " + "\n- ".join(usual_tracks[:8])
        )
    exclude_block = ""
    if exclude_names:
        exclude_block = (
            "\n\nDO NOT include ANY of these — they were heard recently or already shown. "
            "Every playlist must contain DIFFERENT songs:\n- "
            + "\n- ".join(list(exclude_names)[:45])
        )
    return f"""You are VibePilot, building a {n}-song listening session for this vibe: "{vibe_text}".

THE #1 RULE — VIBE LOCK (most important, overrides everything else):
First decide the exact MOOD and ENERGY this vibe demands. Then EVERY single song must match \
that mood and energy. Before adding any song, ask: "does this song's energy truly match the vibe?" \
If not, drop it.
- If the vibe is high-energy / dance / workout / driving, every song must be genuinely upbeat \
and danceable — NEVER slow, sad, mellow or emotional songs.
- If the vibe is mellow / relax / spiritual / focus, every song must be soft and low-energy — \
NEVER party, rap, hip-hop, hype or high-energy songs.
- A song must NEVER be included just because the listener likes it, if it breaks this mood. \
The VIBE wins over taste, every single time.

Use the listener's taste ONLY to choose WHICH on-vibe songs feel like them (genre, language, \
sensibility) — never to override the mood:{_taste_anchor_block(taste)}{usual_block}{exclude_block}

Familiar vs new balance: {_familiarity_guidance(familiarity)}

Keep the whole playlist consistent in mood and energy from start to finish.

Hard rules:
- Real songs by real artists only. NEVER invent songs.
- EVERY song must match the vibe's mood and energy. Zero off-vibe songs.
- No duplicate artists.

Return ONLY a JSON object with a "tracks" array of exactly {n} items:
{{"tracks": [
  {{"title": "<exact track title>", "artist": "<primary artist>", "why": "<one line on why it fits the vibe, max 14 words>"}}
]}}"""


def propose_vibe_session(vibe_text, n=15, taste=None, usual_tracks=None, exclude_names=None, familiarity=5):
    """A taste-grounded session for a moment/intent. Returns [{title,artist,why}]."""
    prompt = build_vibe_session_prompt(vibe_text, n, taste, usual_tracks, exclude_names, familiarity)
    resp = _groq().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.75,
        max_tokens=min(3000, 500 + n * 90),
        response_format={"type": "json_object"},
    )
    return _parse_tracks(resp)


def _parse_tracks(resp):
    data = json.loads(resp.choices[0].message.content.strip())
    picks = data.get("tracks", []) if isinstance(data, dict) else data
    cleaned, seen = [], set()
    for p in picks:
        title = str(p.get("title", "")).strip()
        artist = str(p.get("artist", "")).strip()
        if not title or not artist or artist.lower() in seen:
            continue
        seen.add(artist.lower())
        cleaned.append({"title": title, "artist": artist, "why": str(p.get("why", "")).strip()})
    return cleaned


def vibe_plan(vibe_text, taste=None, n=3) -> dict:
    """LLM picks a few ACCURATE, well-known seed songs + Last.fm mood tags for a vibe.

    Last.fm then expands these seeds into a real, on-vibe candidate pool. The LLM only
    has to name a handful of famous songs (which it's reliable at) — not 15 obscure ones.
    """
    lane = ""
    if taste:
        if taste.get("top_genres"):
            lane += "Genres they like: " + ", ".join(taste["top_genres"][:8]) + ". "
        if taste.get("top_artists"):
            lane += "Artists they like: " + ", ".join(taste["top_artists"][:12]) + "."
    prompt = f"""Pick {n} REAL, well-known songs that strongly match this vibe: "{vibe_text}".
The listener's taste lane: {lane or 'general / open'}.

Rules:
- Every seed song must clearly match the vibe's MOOD and ENERGY (e.g. a chill vibe → soft, mellow songs only; a dance vibe → upbeat danceable songs only).
- Strongly prefer songs in the listener's likely language/region and taste lane.
- Choose WELL-KNOWN songs so they're easy to look up. These are SEEDS, not the final playlist.
- Also list 3-5 Last.fm-style mood/genre tags for this vibe (lowercase, e.g. "chillout", "mellow", "bollywood", "party", "workout").

Return ONLY JSON: {{"seeds": [{{"title": "...", "artist": "..."}}], "tags": ["...", "..."]}}"""
    try:
        resp = _groq().chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content.strip())
        seeds = [
            {"title": str(s.get("title", "")).strip(), "artist": str(s.get("artist", "")).strip()}
            for s in data.get("seeds", []) if s.get("title") and s.get("artist")
        ]
        tags = [str(t).strip().lower() for t in data.get("tags", []) if str(t).strip()]
        return {"seeds": seeds, "tags": tags}
    except Exception:
        return {"seeds": [], "tags": []}


def annotate_whys(items: list[str], context: str, kind: str = "vibe") -> list[str]:
    """One short reason per track. Best-effort; returns [] on failure (caller handles)."""
    if not items:
        return []
    listing = "\n".join(f"{i+1}. {x}" for i, x in enumerate(items))
    ask = (f"why each song fits a playlist for the vibe: {context}" if kind == "vibe"
           else f"the shared feeling making each song a cousin (same vibe) of: {context}")
    prompt = f"""For each numbered song, write a very short reason — {ask}. Max 12 words each.
Keep the SAME order and count.
Songs:
{listing}

Return ONLY JSON: {{"whys": ["...", "..."]}} with exactly {len(items)} strings, same order."""
    try:
        resp = _groq().chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=min(1500, 80 + len(items) * 30),
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content.strip())
        whys = [str(w).strip() for w in data.get("whys", [])]
        if len(whys) >= len(items):
            return whys[:len(items)]
        return whys + [""] * (len(items) - len(whys))
    except Exception:
        return [""] * len(items)


def infer_mood(taste: dict | None, local_time_str: str) -> str:
    """Suggest a likely current mood from recent listening + time of day (one short line)."""
    recent = ""
    if taste and taste.get("recent"):
        recent = "; ".join(r["name"] for r in taste["recent"][:12])
    genres = ", ".join((taste or {}).get("top_genres", [])[:6])

    prompt = f"""It is currently {local_time_str}. A Spotify listener's recent tracks: {recent or 'unknown'}.
Their favorite genres: {genres or 'unknown'}.

In ONE short, friendly sentence (max 16 words), guess the kind of music mood they might want \
RIGHT NOW given the time of day and their recent listening. Be specific about feel. \
Return ONLY a JSON object: {{"mood": "<sentence>", "vibe": "<3-6 word vibe phrase for a music search>"}}"""
    try:
        resp = _groq().chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=120,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content.strip())
        return data
    except Exception:
        return {"mood": "Ready to discover something new?", "vibe": "fresh discovery"}


def resolve_anchor_text(anchor_kind: str, value: str) -> str:
    if anchor_kind == "intent":
        return INTENT_PRESETS.get(value, value)
    if anchor_kind == "song":
        return f"the song '{value}'"
    return value
