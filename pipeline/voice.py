"""Step 3 — Voiceover. Dispatches to TTS_PROVIDER.

synthesize(text, out_base) -> returns the audio file path.
ElevenLabs -> .mp3   |   Piper -> .wav
"""
import re
import subprocess
import requests
import config


def _clean_for_tts(text):
    """Normalize text so TTS doesn't read punctuation as character names."""
    replacements = {
        "\u2014": ", ",   # em dash —
        "\u2013": ", ",   # en dash –
        "\u2026": ".",    # ellipsis …
        "\u201c": "",     # left double quote "
        "\u201d": "",     # right double quote "
        "\u2018": "",     # left single quote '
        "\u2019": "",     # right single quote '
        "\u00ab": "",     # «
        "\u00bb": "",     # »
        "\u2022": "",     # bullet •
        "\u00b0": " grados",  # °
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove content inside brackets/parentheses that might be markup
    text = re.sub(r"\[.*?\]", "", text)
    # Collapse multiple spaces/newlines
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _elevenlabs(text, out_base):
    if not config.TTS_VOICE_ID:
        raise RuntimeError("Set TTS_VOICE_ID in .env")
    out_path = out_base + ".mp3"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.TTS_VOICE_ID}"
    headers = {"xi-api-key": config.ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": config.ELEVENLABS_MODEL,
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.8},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)
    return out_path


def _piper(text, out_base):
    out_path = out_base + ".wav"
    cmd = [config.PIPER_BIN, "-m", config.PIPER_MODEL, "-f", out_path]
    try:
        subprocess.run(cmd, input=text.encode("utf-8"),
                       check=True, capture_output=True)
    except FileNotFoundError as e:
        raise RuntimeError(
            f"Piper not found at '{config.PIPER_BIN}'. Check PIPER_BIN in .env."
        ) from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Piper failed. Check PIPER_MODEL path.\n{e.stderr.decode(errors='ignore')}"
        ) from e
    return out_path


def _gtts(text, out_base):
    import subprocess
    from gtts import gTTS
    raw_path = out_base + "_raw.mp3"
    out_path = out_base + ".mp3"
    tts = gTTS(text=text, lang="es", slow=False)
    tts.save(raw_path)
    speed = getattr(config, "VOICE_SPEED", 1.0)
    if abs(speed - 1.0) > 0.05:
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_path,
            "-filter:a", f"atempo={speed}",
            out_path
        ], check=True, capture_output=True)
    else:
        import shutil
        shutil.copy(raw_path, out_path)
    return out_path

def synthesize(text, out_base):
    text = _clean_for_tts(text)
    if config.TTS_PROVIDER == "elevenlabs":
        return _elevenlabs(text, out_base)
    return _gtts(text, out_base)