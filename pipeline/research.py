"""Step 2 — The brain. Dispatches to the configured LLM_PROVIDER.

  "claude"  -> paid, with built-in web search (richest research)
  "gemini"  -> free tier (recommended temporary option)
  "groq"    -> free tier, fast Llama
  "ollama"  -> local, fully free

Only Claude can browse the web. The other providers write from the FACTS we
pass in (injuries for previews, goals for recaps via API-Sports) plus durable
general knowledge — so pairing a free LLM with DATA_PROVIDER=api_sports keeps
quality high without web access.

All providers return the same strict JSON:
{title, description, hashtags[], hook, segments[{text,card_title,card_stat}], cta, sources[]}
"""
import json

import requests

import config

SCHEMA_HINT = """Return ONLY a JSON object, no markdown fences, with these exact keys:

title       : string ≤80 chars, punchy, includes team names
description : string, 1-2 sentences for YouTube description
hashtags    : array of 3-6 strings WITHOUT the # symbol
hook        : ONE spoken sentence ≤10 words that opens with a curiosity gap or
              surprising fact. Examples: "Nadie habla de este jugador... pero debería."
              "Este dato del Mundial te va a sorprender."
segments    : array of 4-6 objects, each with:
                text       = one spoken sentence (the voiceover line)
                card_title = 2-4 word on-screen label (shown in banner)
                card_stat  = short stat or phrase shown BIG on screen
underdog    : object with:
                name   = full name of the least-known or most-surprising player
                        in this match (could be from either team)
                fact   = one surprising fact about them in ≤15 words
                team   = their team name
cta         : a SPECIFIC comment-bait CTA in Spanish using this exact pattern:
              "Comenta [KEYWORD] si [opinion/prediction]" — for example:
              "Comenta MEXICO si crees que ganan el grupo" or
              "Comenta el marcador que crees que va a quedar"
              Do NOT mention the channel name in the CTA — it appears on screen separately.
sources     : array of URLs used, or []

CRITICAL: The hook + all segment texts + cta spoken aloud = ~%d seconds (~110-130 words total).
The hook must be ≤10 words and create immediate curiosity."""


def _lang():
    return "Spanish" if config.SCRIPT_LANGUAGE == "es" else "English"


def _research_line(searchable, extra=""):
    if searchable:
        return ("Use web search to research this specific match (recent form, "
                "head-to-head, key players, team news, any FIFA controversy). "
                "Prefer official/major outlets; discard rumors. " + extra)
    return ("You have NO web access. Use ONLY the facts given above plus durable "
            "general knowledge about these teams. Do NOT invent recent results, "
            "current form numbers, or stats you cannot be sure of. " + extra)


# ── Winning patterns from Instagram research (June 11 2026) ──────────────────
# Data source: 106 posts analyzed, #mundial2026 #copaDelmundo #futbol
# Pattern 1: Comment CTAs ("Comenta X para recibir / si crees que") → algorithm flood
# Pattern 2: Unknown/underdog player arc → series + viral reach
# Pattern 3: Curiosity-gap hooks under 10 words → watch time
# Pattern 4: FIFA controversy → instant spread
# Pattern 5: Opening day / first result urgency → maximum leverage
# Pattern 6: Guarda y Comparte calendar format → shares
_VIRAL_PATTERNS = """
PROVEN VIRAL PATTERNS to apply (from real engagement data in this niche):
1. HOOK: Open with a curiosity gap under 10 words. Do NOT start with the teams.
   Bad: "Hoy se enfrentan México y Sudáfrica..."
   Good: "Nadie esperaba esto del Mundial... pero aquí estamos."
2. UNDERDOG ARC: Always include the least-known or most-surprising player.
   Content about unknown players consistently outperforms star coverage.
3. COMMENT CTA: End with "Comenta [KEYWORD] si [specific prediction/opinion]".
   This floods the algorithm and boosts reach to non-followers.
4. FIFA CONTROVERSY: If there is ANY recent FIFA rule, restriction, or controversy
   related to this match or tournament — include it. It spreads organically.
5. URGENCY: Use time-pressure language ("hoy", "en minutos", "antes del pitazo")
   — posts tied to live events get dramatically more engagement.
"""


def _preview_prompt(m, injuries, searchable):
    inj_block = ""
    if injuries:
        lines = "; ".join(
            f"{i['player']} ({i['team']}{', ' + i['reason'] if i['reason'] else ''})"
            for i in injuries if i.get("player")
        )
        if lines:
            inj_block = f"\nCONFIRMED absences (treat as fact): {lines}\n"
    return f"""You are a viral World Cup content writer for a YouTube Shorts / Instagram Reels channel.

Upcoming match: {m['home']} vs {m['away']}
Stage: {m.get('round', '')}
Kickoff: {m['kickoff_iso']}
{inj_block}
{_research_line(searchable, "Also look for: any FIFA controversy, the least-known player in this match, and any surprising stat.")}

{_VIRAL_PATTERNS}

Write a {_lang()} pre-match voiceover script for a ~{config.SCRIPT_TARGET_SECONDS}s
vertical Short. Informative tone. Explain who holds the edge and WHY using
form, head-to-head, key players, and absences. Do NOT predict the scoreline.
No invented stats. Apply ALL 5 viral patterns above.

{SCHEMA_HINT % config.SCRIPT_TARGET_SECONDS}"""


def _recap_prompt(m, result, searchable):
    goals = "; ".join(
        f"{g['minute']}' {g['player']} ({g['team']})" for g in result.get("goals", [])
    ) or "no goals data provided"
    return f"""You are a viral World Cup content writer for a YouTube Shorts / Instagram Reels channel.

FINISHED match — these facts are CONFIRMED, use them exactly:
  {m['home']} {m['home_score']} - {m['away_score']} {m['away']}
  Stage: {m.get('round', '')}
  Goals: {goals}

{_research_line(searchable, "Find: turning point, standout performer, post-match reaction, any surprise or controversy.")}

{_VIRAL_PATTERNS}

Write a {_lang()} POST-MATCH news recap voiceover for a ~{config.SCRIPT_TARGET_SECONDS}s
vertical Short. Past tense, news tone, factual. Include the turning point,
a standout stat, and what the result means for the bracket.
Apply ALL 5 viral patterns — especially the curiosity hook and comment CTA.

{SCHEMA_HINT % config.SCRIPT_TARGET_SECONDS}"""


def _extract_json(text):
    """Robust JSON extractor that handles common LLM formatting quirks."""
    # 1. Strip markdown fences
    cleaned = text.replace("```json", "").replace("```", "").strip()

    # 2. Isolate the outermost { ... }
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in model output: {text[:300]}")
    candidate = cleaned[start : end + 1]

    # 3. First try: parse as-is
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # 4. Second try: replace smart/curly quotes with straight quotes
    for old, new in [("\u201c", '"'), ("\u201d", '"'), ("\u2018", "'"), ("\u2019", "'"),
                     ("\u2013", "-"), ("\u2014", "-")]:
        candidate = candidate.replace(old, new)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # 5. Third try: use json5-style lenient parsing via regex fix for
    #    trailing commas (most common Gemini quirk)
    import re
    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse JSON after cleanup: {e}\nRaw (first 400 chars): {candidate[:400]}") from e


# ---- provider calls (each returns plain text) ----
def _call_claude(prompt):
    import anthropic  # lazy: only needed for this provider
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=config.CLAUDE_MODEL, max_tokens=2000,
        tools=[config.WEB_SEARCH_TOOL],
        messages=[{"role": "user", "content": prompt}],
    )
    return "\n".join(b.text for b in resp.content if b.type == "text")


def _call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent"
    r = requests.post(
        url,
        headers={"x-goog-api-key": config.GEMINI_API_KEY, "Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,          # lower = more consistent JSON
                "maxOutputTokens": 2000,
                "responseMimeType": "application/json",  # force Gemini to return valid JSON
            },
        },
        timeout=120,
    )
    r.raise_for_status()
    parts = r.json()["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)


def _call_groq(prompt):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": config.GROQ_MODEL, "temperature": 0.7, "max_tokens": 2000,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _call_ollama(prompt):
    r = requests.post(
        f"{config.OLLAMA_HOST}/api/generate",
        json={"model": config.OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=300,
    )
    r.raise_for_status()
    return r.json()["response"]


_CALLERS = {
    "claude": _call_claude, "gemini": _call_gemini,
    "groq": _call_groq, "ollama": _call_ollama,
}


def build(match, mode, result=None, injuries=None):
    searchable = config.LLM_PROVIDER == "claude"
    prompt = (
        _recap_prompt(match, result or {}, searchable)
        if mode == "recap"
        else _preview_prompt(match, injuries, searchable)
    )
    caller = _CALLERS.get(config.LLM_PROVIDER)
    if caller is None:
        raise ValueError(f"Unknown LLM_PROVIDER: {config.LLM_PROVIDER}")
    text = caller(prompt)
    script = _extract_json(text)
    script["match_id"] = match["id"]
    script["mode"] = mode
    return script