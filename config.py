"""Central configuration.

Providers are switchable so you can use your PAID keys for quality, or flip
back to the FREE stack if credit runs low.

  DATA_PROVIDER: "api_sports"   (paid, full World Cup data) | "football_data" (free)
  TTS_PROVIDER:  "elevenlabs"   (paid, natural voice)        | "piper"         (free, local)

Claude (the brain + web search) is always paid.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---- Paths ----
ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / "state"
OUTPUT_DIR = ROOT / "output"
MODELS_DIR = ROOT / "models"
POSTED_LOG = STATE_DIR / "posted.json"
for d in (STATE_DIR, OUTPUT_DIR, MODELS_DIR):
    d.mkdir(exist_ok=True)

# ---- Provider switches ----
DATA_PROVIDER = os.environ.get("DATA_PROVIDER", "api_sports")    # or "football_data"
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "elevenlabs")      # or "piper"
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "claude")          # "claude"|"gemini"|"groq"|"ollama"

# ---- LLM "brain" providers ----
# Claude (paid; the only one with built-in web search)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"
WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search", "max_uses": 8}
# Gemini (free tier — recommended temporary option). Free key at Google AI Studio.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
# Groq (free tier, fast Llama models)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
# Ollama (local, fully free; needs a capable machine)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")

# ---- DATA providers ----
# api-sports.io (API-Football). World Cup = league 1, season 2026.
APISPORTS_KEY = os.environ.get("APISPORTS_KEY", "")
WORLD_CUP_LEAGUE_ID = 1
SEASON = 2026
# football-data.org (free). World Cup competition code "WC".
FOOTBALLDATA_TOKEN = os.environ.get("FOOTBALLDATA_TOKEN", "")
WC_COMPETITION = "WC"

# ---- TTS providers ----
# ElevenLabs (paid, uses your credit)
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
TTS_VOICE_ID = os.environ.get("TTS_VOICE_ID", "")               # pick one in your ElevenLabs account
ELEVENLABS_MODEL = "eleven_multilingual_v2"                     # handles Spanish
# Piper (free, local) — only needed if TTS_PROVIDER="piper"
PIPER_BIN = os.environ.get("PIPER_BIN", "piper")
PIPER_MODEL = os.environ.get("PIPER_MODEL", str(MODELS_DIR / "es_MX-claude-high.onnx"))

# ---- YouTube upload ----
YOUTUBE_TOKEN_FILE = os.environ.get("YOUTUBE_TOKEN_FILE", str(STATE_DIR / "yt_token.json"))
YOUTUBE_CLIENT_SECRET_FILE = os.environ.get(
    "YOUTUBE_CLIENT_SECRET_FILE", str(STATE_DIR / "yt_client_secret.json")
)

# ---- Content settings ----
ENABLE_PREVIEWS = True
ENABLE_RECAPS = True
PREVIEW_LOOKAHEAD_HOURS = 18
RECAP_LOOKBACK_HOURS = 6
MAX_SHORTS_PER_RUN = 3
MAX_SHORTS_PER_DAY = 8

TEAM_WATCHLIST = [
    "Argentina", "Spain", "Brazil", "Mexico", "France",
    "England", "Portugal", "Colombia", "Panama",
    "USA", "Uruguay", "Paraguay", "Ecuador",
    "Germany", "Netherlands", "Croatia",
]

SCRIPT_TARGET_SECONDS = 45
VIDEO_W, VIDEO_H = 1080, 1920
SCRIPT_LANGUAGE = "es"

YT_CATEGORY_ID = "17"
YT_PRIVACY = "private"

CHANNEL_NAME = "Flash Gol"