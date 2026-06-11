"""Step 5 — Video assembly with ffmpeg.

Simple, reliable: each card shown statically for its time slice.
No zoompan (caused bouncing on Windows). Clean fade between cards.
"""
import subprocess
import config


def _audio_duration(audio_path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def build_video(card_paths, voice_path, out_path):
    duration = _audio_duration(voice_path)
    per = max(duration / len(card_paths), 1.5)
    fps = 30
    w, h = config.VIDEO_W, config.VIDEO_H

    # Each card: scale to exact size, pad if needed, set SAR
    inputs = []
    filter_parts = []
    for i, card in enumerate(card_paths):
        inputs += ["-loop", "1", "-t", f"{per:.3f}", "-i", card]
        filter_parts.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,fps={fps}[v{i}]"
        )

    concat_in  = "".join(f"[v{i}]" for i in range(len(card_paths)))
    filtergraph = (
        ";".join(filter_parts)
        + f";{concat_in}concat=n={len(card_paths)}:v=1:a=0[vout]"
    )

    audio_idx = len(card_paths)
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-i", voice_path,
        "-filter_complex", filtergraph,
        "-map", "[vout]",
        "-map", f"{audio_idx}:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        out_path,
    ]
    subprocess.run(cmd, check=True, capture_output=False)
    return out_path