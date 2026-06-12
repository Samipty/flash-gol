"""Step 5 — Video assembly with ffmpeg.

Simple, reliable: each card shown for its time slice with a quick
fade-in/fade-out "blink cut" between cards (proven social-media transition,
subtle, no zoompan/bouncing issues).
Mixes in looping background music at low volume under the voiceover.
"""
import os
import subprocess
import config

FADE_DUR = 0.12  # seconds — quick blink cut between cards


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
    fade_out_start = max(per - FADE_DUR, 0)

    # Each card: scale to exact size, pad if needed, set SAR,
    # then a quick fade-in and fade-out (blink cut) on its own timeline.
    inputs = []
    filter_parts = []
    for i, card in enumerate(card_paths):
        inputs += ["-loop", "1", "-t", f"{per:.3f}", "-i", card]
        filter_parts.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,fps={fps},"
            f"fade=t=in:st=0:d={FADE_DUR}:color=black,"
            f"fade=t=out:st={fade_out_start:.3f}:d={FADE_DUR}:color=black[v{i}]"
        )

    concat_in  = "".join(f"[v{i}]" for i in range(len(card_paths)))
    filtergraph = (
        ";".join(filter_parts)
        + f";{concat_in}concat=n={len(card_paths)}:v=1:a=0[vout]"
    )

    voice_idx = len(card_paths)
    cmd = ["ffmpeg", "-y", *inputs, "-i", voice_path]

    music_path = getattr(config, "MUSIC_PATH", None)
    music_volume = getattr(config, "MUSIC_VOLUME", 0.12)

    if music_path and os.path.exists(music_path):
        # Loop the music indefinitely; -shortest later trims to voice length.
        cmd += ["-stream_loop", "-1", "-i", music_path]
        music_idx = voice_idx + 1
        filtergraph += (
            f";[{voice_idx}:a]volume=1.0[voice]"
            f";[{music_idx}:a]volume={music_volume}[music]"
            f";[voice][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]"
        )
        audio_map = "[aout]"
    else:
        audio_map = f"{voice_idx}:a"

    cmd += [
        "-filter_complex", filtergraph,
        "-map", "[vout]",
        "-map", audio_map,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        out_path,
    ]
    subprocess.run(cmd, check=True, capture_output=False)
    return out_path