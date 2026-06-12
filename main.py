"""Orchestrator — one run handles BOTH previews and recaps.

Per run:
  recaps first (news is time-sensitive), then previews.
  For each candidate, up to per-run and per-day caps:
    research+script (Claude) -> voiceover -> cards -> video -> upload -> log

Schedule HOURLY during the World Cup so recaps post while results are fresh.
Dry pass (no posting):  python main.py --dry-run
"""
import json
import sys
from datetime import datetime, timezone

import config
print("DEBUG DATA_PROVIDER =", repr(config.DATA_PROVIDER))
from pipeline import matches, research, voice, visuals, video, upload


def _load_posted():
    try:
        return json.loads(config.POSTED_LOG.read_text())  # {"id:mode": iso_ts}
    except (FileNotFoundError, ValueError):
        return {}


def _save_posted(posted):
    config.POSTED_LOG.write_text(json.dumps(posted, indent=2, sort_keys=True))


def _today_count(posted):
    today = datetime.now(timezone.utc).date().isoformat()
    return sum(1 for ts in posted.values() if str(ts).startswith(today))


def _candidates():
    """List of (match, mode, result_or_None), recaps first."""
    out = []
    if config.ENABLE_RECAPS:
        for m in matches.find_finished():
            out.append((m, "recap"))
    if config.ENABLE_PREVIEWS:
        for m in matches.find_upcoming():
            out.append((m, "preview"))
    return out


def run(dry_run=False):
    posted = _load_posted()
    remaining_day = config.MAX_SHORTS_PER_DAY - _today_count(posted)
    made = 0

    cands = _candidates()
    print(f"Found {len(cands)} candidate(s). Daily budget left: {remaining_day}.")

    for m, mode in cands:
        if made >= config.MAX_SHORTS_PER_RUN or remaining_day <= 0:
            break
        key = f"{m['id']}:{mode}"
        if key in posted:
            continue

        label = f"[{mode}] {m['home']} vs {m['away']} — {m.get('round','')}"
        print(f"\n=== {label} ===")
        try:
            result = None
            injuries = None
            if mode == "recap":
                ev = matches.get_result(m["id"])
                result = {
                    "home": m["home"], "away": m["away"],
                    "home_score": m["home_score"], "away_score": m["away_score"],
                    "goals": ev["goals"], "cards": ev["cards"],
                }
            else:
                injuries = matches.get_injuries(m["id"])

            print("  1/5 researching + writing script (Claude)...")
            script = research.build(m, mode, result, injuries)
            script["home"] = m["home"]
            script["away"] = m["away"]

            spoken = " ".join(
                [script["hook"]] + [s["text"] for s in script["segments"]] + [script["cta"]]
            )
            voice_base = str(config.OUTPUT_DIR / f"{m['id']}_{mode}_voice")
            voice_path = None
            print("  2/5 voiceover...")
            if not dry_run:
                voice_path = voice.synthesize(spoken, voice_base)

            print("  3/5 cards...")
            cards = visuals.build_cards(script, mode, result)

            video_path = str(config.OUTPUT_DIR / f"{m['id']}_{mode}_short.mp4")
            print("  4/5 video...")
            if not dry_run:
                video.build_video(cards, voice_path, video_path)

            print("  5/5 upload...")
            if dry_run:
                print("     [dry-run] no se publica nada. Guion generado:")
                print("     TITULO:", script["title"])
                print("     HOOK:  ", script["hook"])
                for i, s in enumerate(script["segments"], 1):
                    print(f"       {i}. {s['text']}  [{s.get('card_title','')}: {s.get('card_stat','')}]")
                print("     CIERRE:", script["cta"])
            else:
                vid = upload.upload(video_path, script)
                print(f"     uploaded: https://youtube.com/watch?v={vid}")
                posted[key] = datetime.now(timezone.utc).isoformat()
                _save_posted(posted)

            made += 1
            remaining_day -= 1
        except Exception as e:  # noqa: BLE001
            print(f"  ! failed on {label}: {e}")
            continue

    print(f"\nDone. Built {made} Short(s) this run.")


if __name__ == "__main__":
    run(dry_run="--dry-run" in sys.argv)