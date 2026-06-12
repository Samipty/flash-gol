"""Step 3 — Voiceover. Dispatches to TTS_PROVIDER.

synthesize(text, out_base) -> returns the audio file path.
ElevenLabs -> .mp3  |  gTTS -> .mp3 (with speed adjustment)  |  Piper -> .wav
"""
import re
import subprocess
import requests
import config


def _clean_for_tts(text):
    replacements = {
        "\u2014": ", ", "\u2013": ", ", "\u2026": ".",
        "\u201c": "", "\u201d": "", "\u2018": "", "\u2019": "",
        "\u00ab": "", "\u00bb": "", "\u2022": "", "\u00b0": " grados",
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\[.*?\]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _apply_speed(raw_path, out_path, speed):
    """Use ffmpeg atempo to adjust speed. atempo max is 2.0 per filter."""
    filters = []
    s = speed
    while s > 2.0:
        filters.append("atempo=2.0")
        s /= 2.0
    filters.append(f"atempo={s:.3f}")
    subprocess.run(
        ["ffmpeg", "-y", "-i", raw_path,
         "-filter:a", ",".join(filters), out_path],
        check=True, capture_output=True,
    )


def _gtts(text, out_base):
    from gtts import gTTS
    import tempfile, os, shutil
    speed = getattr(config, "VOICE_SPEED", 1.0)
    out_path = out_base + ".mp3"
    if abs(speed - 1.0) > 0.05:
        # Generate at normal speed into a temp file, then speed up
        tmp = out_base + "_raw.mp3"
        gTTS(text=text, lang="es", slow=False).save(tmp)
        _apply_speed(tmp, out_path, speed)
        try:
            os.remove(tmp)
        except OSError:
            pass
    else:
        gTTS(text=text, lang="es", slow=False).save(out_path)
    return out_path


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
        subprocess.run(cmd, input=text.encode("utf-8"), check=True, capture_output=True)
    except FileNotFoundError as e:
        raise RuntimeError(f"Piper not found at '{config.PIPER_BIN}'.") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Piper failed.\n{e.stderr.decode(errors='ignore')}") from e
    # Apply speed if configured
    speed = getattr(config, "VOICE_SPEED", 1.0)
    if abs(speed - 1.0) > 0.05:
        import tempfile, shutil
        tmp = out_path + ".tmp.wav"
        shutil.copy(out_path, tmp)
        _apply_speed(tmp, out_path, speed)
        import os
        try: os.remove(tmp)
        except OSError: pass
    return out_path


def synthesize(text, out_base):
    text = _clean_for_tts(text)
    if config.TTS_PROVIDER == "elevenlabs":
        return _elevenlabs(text, out_base)
    # Default: gTTS (works on Windows, Linux, GitHub Actions — no model files needed)
    return _gtts(text, out_base)