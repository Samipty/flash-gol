"""Offline render test — no API keys or network needed.

Feeds a MOCK script through the parts that run locally (cards + video).
The live steps (API-Sports data, Claude script, ElevenLabs voice, YouTube
upload) are skipped here; this just proves the rendering pipeline works and
shows you the output format. Run: python smoke_test.py
"""
import subprocess

import config
from pipeline import visuals, video

PREVIEW = {
    "match_id": "demo_preview",
    "mode": "preview",
    "title": "Argentina vs Mexico — quién llega mejor",
    "hook": "Dos pesos pesados se ven las caras en fase de grupos.",
    "segments": [
        {"text": "Argentina llega como campeona vigente y líder del ranking.",
         "card_title": "Forma", "card_stat": "5-0-0"},
        {"text": "Mexico aprovecha el factor local con su afición de su lado.",
         "card_title": "Local", "card_stat": "ANFITRION"},
        {"text": "Una baja por lesión obliga a mover el mediocampo argentino.",
         "card_title": "Baja clave", "card_stat": "-1 MED"},
        {"text": "El historial reciente favorece ligeramente a la albiceleste.",
         "card_title": "Head-to-head", "card_stat": "3-1"},
    ],
    "cta": "Quien crees que llega con ventaja, dejalo en los comentarios.",
}

RECAP = {
    "match_id": "demo_recap",
    "mode": "recap",
    "title": "Argentina 2-1 Mexico — asi quedo",
    "hook": "Partidazo en el debut: Argentina lo saca sobre el final.",
    "segments": [
        {"text": "Argentina golpeo primero con un cabezazo tempranero.",
         "card_title": "Min 12", "card_stat": "1-0"},
        {"text": "Mexico respondio con un golazo de media distancia.",
         "card_title": "Min 38", "card_stat": "1-1"},
        {"text": "El gol del triunfo llego en tiempo de descuento.",
         "card_title": "Min 90", "card_stat": "2-1"},
        {"text": "Con esto Argentina queda como lider del grupo.",
         "card_title": "Grupo", "card_stat": "1ro"},
    ],
    "cta": "Te esperabas este resultado? Comentalo.",
}
RECAP_RESULT = {"home": "Argentina", "away": "Mexico", "home_score": 2, "away_score": 1}


def fake_audio(path, seconds):
    """Generate a quiet test tone so the video step has audio to time against."""
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=220:duration={seconds}",
         "-af", "volume=0.05", path],
        check=True, capture_output=True,
    )
    return path


def run_one(script, mode, result=None):
    print(f"\n=== rendering [{mode}] {script['title']} ===")
    cards = visuals.build_cards(script, mode, result)
    print(f"  cards: {len(cards)}")
    audio = fake_audio(str(config.OUTPUT_DIR / f"{script['match_id']}_test.wav"), 12)
    out = str(config.OUTPUT_DIR / f"{script['match_id']}_short.mp4")
    video.build_video(cards, audio, out)
    print(f"  video: {out}")
    return cards, out


if __name__ == "__main__":
    run_one(PREVIEW, "preview")
    run_one(RECAP, "recap", RECAP_RESULT)
    print("\nDone.")
