"""Step 4 — Visuals. Premium dark + gold design with team color tint."""
from PIL import Image, ImageDraw, ImageFont
import config

W, H = config.VIDEO_W, config.VIDEO_H

# ── Color system ──────────────────────────────────────────────────────────────
GOLD       = (212, 175,  55)   # primary accent — all highlights
GOLD_DIM   = (160, 130,  40)   # secondary gold
WHITE      = (245, 245, 250)   # main text
MUTED      = (170, 165, 185)   # secondary text
DARK_BASE  = ( 10,   8,  18)   # near-black background base
RED_CTA    = (210,  40,  60)   # CTA button

# ── Team flag colors (used as subtle background tint only) ────────────────────
TEAM_COLORS = {
    "argentina":    (116, 172, 223),
    "spain":        (170,  21,  27),
    "brazil":       (  0, 156,  59),
    "mexico":       (  0, 104,  71),
    "france":       (  0,  35, 149),
    "england":      (207,   8,  31),
    "portugal":     (  0,  80,   0),
    "colombia":     (252, 209,  22),
    "panama":       (218,  18,  26),
    "south africa": (  0, 122,  77),
    "usa":          (  0,  40, 104),
    "germany":      ( 50,  50,  50),
    "netherlands":  (255, 106,  19),
    "default":      ( 40,  20,  80),
}

def _normalize(text):
    import unicodedata
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    )

def _team_tint(home):
    key = _normalize(home.strip())
    for k, v in TEAM_COLORS.items():
        if _normalize(k) in key or key in _normalize(k):
            return v
    return TEAM_COLORS["default"]

# ── Fonts ─────────────────────────────────────────────────────────────────────
def _font(size, bold=True):
    # Segoe UI is cleanest on Windows; fallback to Arial then DejaVu
    candidates = (
        ["C:/Windows/Fonts/seguibl.ttf",   # Segoe UI Black
         "C:/Windows/Fonts/segoeuib.ttf",  # Segoe UI Bold
         "C:/Windows/Fonts/arialbd.ttf",
         "C:/Windows/Fonts/calibrib.ttf",
         "DejaVuSans-Bold.ttf",
         "LiberationSans-Bold.ttf"]
        if bold else
        ["C:/Windows/Fonts/segoeui.ttf",
         "C:/Windows/Fonts/arial.ttf",
         "C:/Windows/Fonts/calibri.ttf",
         "DejaVuSans.ttf",
         "LiberationSans-Regular.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=max(size // 3, 10))

# ── Background ────────────────────────────────────────────────────────────────
def _make_bg(tint_color):
    """Near-black background with subtle team color tint at the edges."""
    img = Image.new("RGB", (W, H))
    px = img.load()
    tr, tg, tb = tint_color
    for y in range(H):
        for x in range(W):
            t_y = y / H
            # Edge glow — stronger at corners, fades to center
            edge_x = 1 - abs(x / W - 0.5) * 2       # 0=center, 1=edge
            edge_y = abs(t_y - 0.5) * 2              # 0=center, 1=edge
            edge = (edge_x * 0.3 + edge_y * 0.15)
            r = int(DARK_BASE[0] + tr * edge * 0.35)
            g = int(DARK_BASE[1] + tg * edge * 0.35)
            b = int(DARK_BASE[2] + tb * edge * 0.35)
            px[x, y] = (min(r,255), min(g,255), min(b,255))
    return img

# ── Drawing helpers ────────────────────────────────────────────────────────────
def _centered(d, text, y, font, color, shadow=True, max_w=W-80):
    while font.size > 20 and d.textlength(text, font=font) > max_w:
        font = _font(font.size - 5, bold=True)
    tw = d.textlength(text, font=font)
    x = int((W - tw) / 2)
    if shadow:
        d.text((x+3, y+3), text, font=font, fill=(0, 0, 0))
    d.text((x, y), text, font=font, fill=color)
    return int(y + font.getbbox(text)[3] + 14)

def _top_pill(d, text, color=GOLD):
    """Top banner pill."""
    d.rounded_rectangle([50, 80, W-50, 175], radius=28, fill=color)
    f = _font(46)
    while d.textlength(text, font=f) > W-130 and f.size > 24:
        f = _font(f.size - 3)
    d.text(((W - d.textlength(text, font=f)) / 2, 108), text, font=f,
           fill=DARK_BASE)

def _gold_line(d, y=193):
    d.rectangle([60, y, W-60, y+4], fill=GOLD)

def _cta_btn(d, text, color=RED_CTA):
    d.rounded_rectangle([70, H-210, W-70, H-80], radius=28, fill=color)
    f = _font(52)
    while d.textlength(text, font=f) > W-180 and f.size > 28:
        f = _font(f.size - 3)
    d.text(((W - d.textlength(text, font=f)) / 2, H-178), text, font=f,
           fill=WHITE)

def _vcentered_block(lines_data, top=175, bottom=None):
    """Calculate starting Y to vertically center a block of lines."""
    if bottom is None:
        bottom = H - 240
    total = sum(lh for _, _, _, lh in lines_data)
    return top + max(0, (bottom - top - total) // 2)

# ── Card builders ─────────────────────────────────────────────────────────────
def _render_lines(d, lines_data, y):
    """lines_data: list of (text, font, color, line_height)"""
    for text, font, color, lh in lines_data:
        tw = d.textlength(text, font=font)
        x = int((W - tw) / 2)
        d.text((x+2, y+2), text, font=font, fill=(0, 0, 0))
        d.text((x, y), text, font=font, fill=color)
        y += lh
    return y


def _hook_card(path, home, away, title, hook, league=""):
    """Opening card: Flash Gol brand top, hook text upper, team names in center."""
    img = _make_bg(_team_tint(home))
    d = ImageDraw.Draw(img)

    # Top pill — Flash Gol branding (general, not World Cup specific)
    stage = league if league else "⚡  FLASH GOL"
    _top_pill(d, stage, GOLD)
    _gold_line(d)

    # Hook text — large, starts from just below the gold line
    hook_clean = hook.strip().rstrip(".")
    words = hook_clean.split()
    for size in [90, 76, 64, 54]:
        hf = _font(size)
        lines, cur = [], ""
        for w in words:
            trial = f"{cur} {w}".strip()
            if d.textlength(trial, font=hf) <= W - 100:
                cur = trial
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        if len(lines) <= 3:
            break

    lh = hf.getbbox("A")[3] + 22
    y = 230
    for line in lines:
        tw = d.textlength(line, font=hf)
        d.text((int((W-tw)/2)+2, y+2), line, font=hf, fill=(0,0,0))
        d.text((int((W-tw)/2), y), line, font=hf, fill=WHITE)
        y += lh

    # Team names — centered in the lower-middle of the screen
    label = f"{home.upper()}  vs  {away.upper()}"
    tf = _font(68)
    while d.textlength(label, font=tf) > W - 80:
        tf = _font(tf.size - 4)
    team_y = H // 2 + 80   # comfortably below center — the area Sami circled
    _centered(d, label, team_y, tf, GOLD, max_w=W-80)

    # Thin separator below teams
    sep_y = team_y + tf.getbbox("A")[3] + 30
    d.rectangle([W//2 - 100, sep_y, W//2 + 100, sep_y + 4], fill=MUTED)

    img.save(path, "PNG")
    return path


def _stat_card(path, home, away, banner, stat, label, body_lines):
    """Standard segment card: big stat + label + body text."""
    img = _make_bg(_team_tint(home))
    d = ImageDraw.Draw(img)
    _top_pill(d, banner, GOLD)
    _gold_line(d)

    # Build line data
    ld = []
    if stat:
        st = stat.upper()
        sf = _font(120 if len(st) <= 8 else 80 if len(st) <= 16 else 60)
        lh = sf.getbbox("A")[3] + 20
        ld.append((st, sf, GOLD, lh))
    if label:
        lbf = _font(64)
        ld.append((label.upper(), lbf, WHITE, lbf.getbbox("A")[3] + 16))
    for line in body_lines:
        if line:
            bf = _font(46, bold=False)
            ld.append((line, bf, MUTED, bf.getbbox("A")[3] + 12))

    y = _vcentered_block(ld)
    _render_lines(d, ld, y)
    img.save(path, "PNG")
    return path


def _underdog_card(path, home, away, name, team, fact):
    """Jugador a seguir card."""
    img = _make_bg(_team_tint(home))
    d = ImageDraw.Draw(img)
    _top_pill(d, "🔍  JUGADOR A SEGUIR", GOLD_DIM)
    _gold_line(d)

    ld = [
        ("¿LO CONOCÍAS?", _font(58), GOLD, _font(58).getbbox("A")[3] + 16),
        (name.upper(), _font(82), WHITE, _font(82).getbbox("A")[3] + 20),
        (team.upper(), _font(52, bold=False), MUTED, _font(52).getbbox("A")[3] + 14),
    ]
    if fact:
        ff = _font(44, bold=False)
        words = fact.split()
        lines, cur = [], ""
        for w in words:
            trial = f"{cur} {w}".strip()
            if d.textlength(trial, font=ff) <= W - 100:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        for line in lines:
            ld.append((line, ff, MUTED, ff.getbbox("A")[3] + 10))

    y = _vcentered_block(ld)
    _render_lines(d, ld, y)
    img.save(path, "PNG")
    return path


def _cta_card(path, home, away, cta_text):
    """Closing comment CTA card."""
    img = _make_bg(_team_tint(home))
    d = ImageDraw.Draw(img)
    _top_pill(d, "🔔  SÍGUENOS PARA MÁS", GOLD)
    _gold_line(d)

    # Extract keyword if pattern "Comenta X si..."
    keyword = ""
    low = cta_text.lower()
    if "comenta" in low:
        parts = cta_text.split()
        for i, p in enumerate(parts):
            if p.lower() == "comenta" and i + 1 < len(parts):
                keyword = parts[i + 1].upper().strip(".,!?")
                break

    ld = []
    if keyword:
        ld.append(("COMENTA", _font(70), MUTED, _font(70).getbbox("A")[3]+10))
        ld.append((keyword, _font(180), GOLD, _font(180).getbbox("A")[3]+16))
        ld.append(("👇", _font(100), WHITE, _font(100).getbbox("A")[3]+10))
    else:
        ld.append((cta_text[:36].upper(), _font(62), GOLD, _font(62).getbbox("A")[3]+16))
        ld.append(("👇", _font(100), WHITE, _font(100).getbbox("A")[3]+10))

    y = _vcentered_block(ld, top=175, bottom=H-240)
    _render_lines(d, ld, y)
    _cta_btn(d, f"SEGUIR @FlashGol  ⚡")
    img.save(path, "PNG")
    return path


def _scoreboard_card(path, home, away, hs, away_s):
    img = _make_bg(_team_tint(home))
    d = ImageDraw.Draw(img)
    _top_pill(d, "⚽  RESULTADO FINAL", GOLD)
    _gold_line(d)

    ld = [
        (home.upper(), _font(78), WHITE, _font(78).getbbox("A")[3]+16),
        (f"{hs}  —  {away_s}", _font(260), GOLD, _font(260).getbbox("A")[3]+20),
        (away.upper(), _font(78), MUTED, _font(78).getbbox("A")[3]+14),
    ]
    y = _vcentered_block(ld, top=175, bottom=H-240)
    _render_lines(d, ld, y)
    _cta_btn(d, "¿SORPRENDIDO? 👇 @FlashGol")
    img.save(path, "PNG")
    return path


# ── Public API ────────────────────────────────────────────────────────────────
def build_cards(script, mode="preview", result=None):
    if result:
        home = result.get("home", "")
        away = result.get("away", "")
    else:
        home = script.get("home", "")
        away = script.get("away", "")
        if not home:
            title = script.get("title", "")
            if " vs " in title.lower():
                parts = title.lower().split(" vs ")
                home = parts[0].strip().split()[-1]
                away = parts[1].strip().split()[0] if len(parts) > 1 else ""

    mid   = script["match_id"]
    title = script.get("title", "")
    segs  = script.get("segments", [])
    paths = []

    # ── Card 0: scoreboard (recap) or hook (preview) ──
    if mode == "recap" and result:
        p = str(config.OUTPUT_DIR / f"{mid}_card_00.png")
        _scoreboard_card(p, result["home"], result["away"],
                         result["home_score"], result["away_score"])
        paths.append(p)
    else:
        p = str(config.OUTPUT_DIR / f"{mid}_card_00.png")
        league_label = f"⚽  {script.get('league', 'FLASH GOL').upper()}" if script.get('league') else "⚡  FLASH GOL"
        _hook_card(p, home, away, title, script.get("hook", "¿Quién tiene la ventaja?"), league_label)
        paths.append(p)

    # ── Segment cards ──
    for i, seg in enumerate(segs):
        text  = seg.get("text", "")
        stat  = seg.get("card_stat", "")
        label = seg.get("card_title", "")
        words = text.split()
        mid_i = len(words) // 2
        body  = [" ".join(words[:mid_i]), " ".join(words[mid_i:])]
        p = str(config.OUTPUT_DIR / f"{mid}_card_{i+1:02d}.png")
        banner = f"⚽  {label.upper()}" if label else "⚡  FLASH GOL"
        _stat_card(p, home, away, banner, stat, label, body)
        paths.append(p)

    # ── Underdog card ──
    ud = script.get("underdog")
    next_idx = len(segs) + 1
    if ud and ud.get("name"):
        p = str(config.OUTPUT_DIR / f"{mid}_card_{next_idx:02d}.png")
        _underdog_card(p, home, away,
                       ud.get("name", ""), ud.get("team", ""), ud.get("fact", ""))
        paths.append(p)
        next_idx += 1

    # ── CTA card ──
    p = str(config.OUTPUT_DIR / f"{mid}_card_{next_idx:02d}.png")
    _cta_card(p, home, away, script.get("cta", "Comenta tu predicción 👇"))
    paths.append(p)

    return paths