"""Step 1 — Discover matches (World Cup) via API-Sports or football-data.org."""
from datetime import datetime, timedelta, timezone

import requests

import config

def _watchlisted(home, away):
    wl = config.TEAM_WATCHLIST
    if not wl:
        return True
    return any(t.lower() in (home.lower(), away.lower()) for t in wl)

# ── API-Sports (paid) ──────────────────────────────────────────────────────────
_AS_BASE = "https://v3.football.api-sports.io"

def _as_headers():
    return {"x-apisports-key": config.APISPORTS_KEY}

def _as_fixtures(status):
    now = datetime.now(timezone.utc)
    params = {
        "league": config.WORLD_CUP_LEAGUE_ID,
        "season": config.SEASON,
        "from": (now - timedelta(hours=config.RECAP_LOOKBACK_HOURS + 6)).date().isoformat(),
        "to": (now + timedelta(hours=config.PREVIEW_LOOKAHEAD_HOURS + 6)).date().isoformat(),
        "status": status,
    }
    try:
        r = requests.get(
            f"{_AS_BASE}/fixtures",
            headers=_as_headers(),
            params=params,
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("response", [])
    except Exception as e:  # noqa: BLE001
        print(f"  ! api-sports error ({status}): {e}")
        return []

def _as_base_dict(fx):
    return {
        "id": str(fx["fixture"]["id"]),
        "league": fx["league"]["name"],
        "round": fx["league"].get("round", ""),
        "home": fx["teams"]["home"]["name"],
        "away": fx["teams"]["away"]["name"],
        "kickoff_iso": fx["fixture"]["date"],
    }

def _as_injuries(fixture_id):
    out = []
    try:
        r = requests.get(
            f"{_AS_BASE}/injuries",
            headers=_as_headers(),
            params={"fixture": fixture_id},
            timeout=30,
        )
        r.raise_for_status()
        for it in r.json().get("response", []):
            player = it.get("player") or {}
            out.append({
                "team": (it.get("team") or {}).get("name", ""),
                "player": player.get("name", ""),
                "reason": player.get("reason") or it.get("reason") or "",
            })
    except Exception as e:  # noqa: BLE001
        print(f"  ! api-sports injuries error for {fixture_id}: {e}")
    return out

def _as_result(fixture_id):
    goals, cards = [], []
    try:
        r = requests.get(
            f"{_AS_BASE}/fixtures/events",
            headers=_as_headers(),
            params={"fixture": fixture_id},
            timeout=30,
        )
        r.raise_for_status()
        for ev in r.json().get("response", []):
            entry = {
                "team": ev["team"]["name"],
                "player": (ev.get("player") or {}).get("name") or "",
                "minute": ev["time"]["elapsed"],
                "detail": ev.get("detail", ""),
            }
            if ev["type"] == "Goal":
                goals.append(entry)
            elif ev["type"] == "Card":
                cards.append(entry)
    except Exception as e:  # noqa: BLE001
        print(f"  ! api-sports events error for {fixture_id}: {e}")
    return {"goals": goals, "cards": cards}

def _as_upcoming():
    now = datetime.now(timezone.utc)
    out = []
    for fx in _as_fixtures("NS"):
        ko = datetime.fromisoformat(fx["fixture"]["date"].replace("Z", "+00:00"))
        if not (now <= ko <= now + timedelta(hours=config.PREVIEW_LOOKAHEAD_HOURS)):
            continue
        m = _as_base_dict(fx)
        if _watchlisted(m["home"], m["away"]):
            out.append(m)
    out.sort(key=lambda m: m["kickoff_iso"])
    return out

def _as_finished():
    now = datetime.now(timezone.utc)
    out = []
    for fx in _as_fixtures("FT-AET-PEN"):
        ko = datetime.fromisoformat(fx["fixture"]["date"].replace("Z", "+00:00"))
        if now - ko > timedelta(hours=config.RECAP_LOOKBACK_HOURS + 2):
            continue
        m = _as_base_dict(fx)
        m["home_score"] = fx["goals"]["home"]
        m["away_score"] = fx["goals"]["away"]
        if _watchlisted(m["home"], m["away"]):
            out.append(m)
    out.sort(key=lambda m: m["kickoff_iso"], reverse=True)
    return out

# ── football-data.org (free fallback) ─────────────────────────────────────────
_FD_BASE = "https://api.football-data.org/v4"
_FD_UPCOMING = {"SCHEDULED", "TIMED"}
_FD_FINISHED = {"FINISHED", "AWARDED"}

def _fd_matches(hours_back, hours_fwd):
    now = datetime.now(timezone.utc)
    params = {
        "dateFrom": (now - timedelta(hours=hours_back)).date().isoformat(),
        "dateTo": (now + timedelta(hours=hours_fwd)).date().isoformat(),
    }
    try:
        r = requests.get(
            f"{_FD_BASE}/competitions/{config.WC_COMPETITION}/matches",
            headers={"X-Auth-Token": config.FOOTBALLDATA_TOKEN},
            params=params,
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("matches", [])
    except Exception as e:  # noqa: BLE001
        print(f"  ! football-data error: {e}")
        return []

def _fd_base_dict(mt):
    stage = (mt.get("stage") or "").replace("_", " ").title()
    grp = mt.get("group") or ""
    return {
        "id": str(mt["id"]),
        "league": "FIFA World Cup",
        "round": f"{stage} {grp}".strip(),
        "home": mt["homeTeam"]["name"],
        "away": mt["awayTeam"]["name"],
        "kickoff_iso": mt["utcDate"],
    }

def _fd_upcoming():
    now = datetime.now(timezone.utc)
    out = []
    for mt in _fd_matches(2, config.PREVIEW_LOOKAHEAD_HOURS + 4):
        if mt.get("status") not in _FD_UPCOMING:
            continue
        ko = datetime.fromisoformat(mt["utcDate"].replace("Z", "+00:00"))
        if not (now <= ko <= now + timedelta(hours=config.PREVIEW_LOOKAHEAD_HOURS)):
            continue
        m = _fd_base_dict(mt)
        if _watchlisted(m["home"], m["away"]):
            out.append(m)
    out.sort(key=lambda m: m["kickoff_iso"])
    return out

def _fd_finished():
    now = datetime.now(timezone.utc)
    out = []
    for mt in _fd_matches(config.RECAP_LOOKBACK_HOURS + 6, 2):
        if mt.get("status") not in _FD_FINISHED:
            continue
        ko = datetime.fromisoformat(mt["utcDate"].replace("Z", "+00:00"))
        if now - ko > timedelta(hours=config.RECAP_LOOKBACK_HOURS + 2):
            continue
        m = _fd_base_dict(mt)
        ft = (mt.get("score") or {}).get("fullTime") or {}
        m["home_score"], m["away_score"] = ft.get("home"), ft.get("away")
        if _watchlisted(m["home"], m["away"]):
            out.append(m)
    out.sort(key=lambda m: m["kickoff_iso"], reverse=True)
    return out

def _fd_result(match_id):
    goals = []
    try:
        r = requests.get(
            f"{_FD_BASE}/matches/{match_id}",
            headers={"X-Auth-Token": config.FOOTBALLDATA_TOKEN},
            timeout=30,
        )
        r.raise_for_status()
        for g in r.json().get("goals", []) or []:
            goals.append({
                "team": (g.get("team") or {}).get("name", ""),
                "player": (g.get("scorer") or {}).get("name", ""),
                "minute": g.get("minute", ""),
                "detail": g.get("type", ""),
            })
    except Exception as e:  # noqa: BLE001
        print(f"  ! football-data detail missing for {match_id}: {e}")
    return {"goals": goals, "cards": []}

# ── Dispatch ───────────────────────────────────────────────────────────────────
def find_upcoming():
    return _as_upcoming() if config.DATA_PROVIDER == "api_sports" else _fd_upcoming()

def find_finished():
    return _as_finished() if config.DATA_PROVIDER == "api_sports" else _fd_finished()

def get_result(match_id):
    return _as_result(match_id) if config.DATA_PROVIDER == "api_sports" else _fd_result(match_id)

def get_injuries(match_id):
    return _as_injuries(match_id) if config.DATA_PROVIDER == "api_sports" else []