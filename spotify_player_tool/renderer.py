from __future__ import annotations

import io
import math
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ── Palette ──────────────────────────────────────────────────────────────────

ACCENT      = (30, 215, 96)     # Spotify green  #1ED760
WHITE       = (255, 255, 255)
GREY_TEXT   = (179, 179, 179)   # secondary text
GREY_BAR    = (83,  83,  83)    # progress track
GREY_DIM    = (100, 100, 100)   # dim controls / time

# ── Resolutions ──────────────────────────────────────────────────────────────

# Вертикальный  9:16  Full HD
VW, VH = 1080, 1920

# Горизонтальный 16:9 Full HD
HW, HH = 1920, 1080

# ── Fonts ────────────────────────────────────────────────────────────────────

_INTER = "/usr/share/fonts/truetype/InterVariable.ttf"
_FALLBACK_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
_FALLBACK_REG  = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def _font(size: int, weight: int = 400) -> ImageFont.FreeTypeFont:
    """Load Inter Variable at requested size; weight 400=regular 700=bold."""
    try:
        font = ImageFont.truetype(_INTER, size)
        # Inter Variable supports wght axis – set via variation if available
        try:
            font.set_variation_by_axes([weight])
        except Exception:
            pass
        return font
    except OSError:
        fallback = _FALLBACK_BOLD if weight >= 600 else _FALLBACK_REG
        try:
            return ImageFont.truetype(fallback, size)
        except OSError:
            return ImageFont.load_default()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _truncate(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> str:
    if draw.textlength(text, font=font) <= max_w:
        return text
    while len(text) > 1:
        text = text[:-1]
        if draw.textlength(text + "…", font=font) <= max_w:
            return text + "…"
    return "…"


def _rounded_art(img: Image.Image, size: int, radius: int) -> Image.Image:
    img = img.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    img.putalpha(mask)
    return img


def _extract_dominant_colors(img: Image.Image) -> List[Tuple[int, int, int]]:
    small = img.resize((80, 80), Image.LANCZOS).convert("RGB")
    q = small.quantize(colors=8)
    pal = q.getpalette()
    n = min(8, len(pal) // 3)
    colors = [(pal[i*3], pal[i*3+1], pal[i*3+2]) for i in range(n)]

    def score(c):
        r, g, b = c
        return (max(r, g, b) - min(r, g, b)) * 0.65 + (r + g + b) / 3 * 0.35

    colors.sort(key=score, reverse=True)
    return colors[:3] if colors else [(40, 40, 40)]


def _make_blurred_bg(cover: Image.Image, w: int, h: int, blur: int = 60, darkness: float = 0.55) -> Image.Image:
    scale = max(w / cover.width, h / cover.height) * 1.1
    nw, nh = int(cover.width * scale), int(cover.height * scale)
    bg = cover.resize((nw, nh), Image.LANCZOS).convert("RGB")
    bg = bg.crop(((nw - w) // 2, (nh - h) // 2, (nw - w) // 2 + w, (nh - h) // 2 + h))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=blur))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.blend(bg, dark, alpha=darkness)


def _make_gradient_bg(colors: List[Tuple[int, int, int]], w: int, h: int) -> Image.Image:
    def dk(c, f): return tuple(max(0, int(v * f)) for v in c)
    c1 = dk(colors[0], 0.45)
    c2 = dk(colors[1] if len(colors) > 1 else colors[0], 0.28)
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        color = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=color)
    return img


# ── SVG-style icon drawers (scalable, s = unit size) ─────────────────────────

def _icon_shuffle(draw: ImageDraw.ImageDraw, cx: int, cy: int, s: int, color: tuple, lw: int = 3):
    hs = s // 3
    for (x0, y0, x1, y1) in [(cx - s, cy + hs, cx + s, cy - hs), (cx - s, cy - hs, cx + s, cy + hs)]:
        draw.line([x0, y0, x1, y1], fill=color, width=lw)
    # arrowheads
    ax, ay = cx + s, cy - hs
    draw.polygon([(ax - 8, ay - 5), (ax + 1, ay), (ax - 8, ay + 5)], fill=color)
    bx, by = cx + s, cy + hs
    draw.polygon([(bx - 8, by + 5), (bx + 1, by), (bx - 8, by - 5)], fill=color)


def _icon_prev(draw: ImageDraw.ImageDraw, cx: int, cy: int, s: int, color: tuple, lw: int = 3):
    h = int(s * 1.25)
    draw.polygon([(cx + s, cy - h), (cx + s, cy + h), (cx - s + 4, cy)], fill=color)
    draw.rectangle([cx - s - 2, cy - h, cx - s + lw, cy + h], fill=color)


def _icon_next(draw: ImageDraw.ImageDraw, cx: int, cy: int, s: int, color: tuple, lw: int = 3):
    h = int(s * 1.25)
    draw.polygon([(cx - s, cy - h), (cx - s, cy + h), (cx + s - 4, cy)], fill=color)
    draw.rectangle([cx + s - lw, cy - h, cx + s + 2, cy + h], fill=color)


def _icon_play(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, fg: tuple, inner: tuple):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fg)
    ts = int(r * 0.38)
    draw.polygon([
        (cx - int(ts * 0.65), cy - ts),
        (cx - int(ts * 0.65), cy + ts),
        (cx + ts + 2, cy),
    ], fill=inner)


def _icon_repeat(draw: ImageDraw.ImageDraw, cx: int, cy: int, s: int, color: tuple, lw: int = 3):
    r = s - 2
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=40, end=320, fill=color, width=lw)
    for angle_deg, sign in [(320, 1), (40, -1)]:
        ang = math.radians(angle_deg)
        ax = cx + int(r * math.cos(ang))
        ay = cy + int(r * math.sin(ang))
        draw.polygon([
            (ax + sign * 6, ay - 4),
            (ax - sign * 2, ay),
            (ax + sign * 6, ay + 4),
        ], fill=color)


def _progress_bar(draw: ImageDraw.ImageDraw,
                  x0: int, y: int, x1: int,
                  bar_h: int, dot_r: int,
                  progress: float, track_color: tuple, fill_color: tuple):
    fill_end = x0 + int((x1 - x0) * progress)
    # track
    draw.rounded_rectangle([x0, y, x1, y + bar_h], radius=bar_h // 2, fill=(*track_color, 255))
    # filled
    draw.rounded_rectangle([x0, y, fill_end, y + bar_h], radius=bar_h // 2, fill=(*fill_color, 255))
    # dot
    dot_cx = fill_end
    dot_cy = y + bar_h // 2
    draw.ellipse([dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r], fill=(*fill_color, 255))


# ── Vertical player  (1080 × 1920) ───────────────────────────────────────────

def _draw_vertical(canvas: Image.Image, cover: Image.Image, track: dict):
    draw = ImageDraw.Draw(canvas, "RGBA")
    W, H = VW, VH
    PAD = 60

    # ── Album art ──
    ART_SIZE = W - PAD * 2          # 960 px
    ART_X    = PAD
    ART_Y    = 160
    art = _rounded_art(cover, ART_SIZE, 20)
    canvas.alpha_composite(art, (ART_X, ART_Y))

    # ── Track info ──
    INFO_Y = ART_Y + ART_SIZE + 60  # ~1180
    TEXT_W = W - PAD * 2

    fn_title  = _font(72, 700)
    fn_artist = _font(46, 400)
    fn_time   = _font(38, 400)
    fn_ctrl   = _font(32, 400)

    title = _truncate(draw, track["title"], fn_title, TEXT_W)
    draw.text((PAD, INFO_Y), title, font=fn_title, fill=(*WHITE, 255))

    artist = _truncate(draw, track["artist"], fn_artist, TEXT_W - 60)
    draw.text((PAD, INFO_Y + 90), artist, font=fn_artist, fill=(*GREY_TEXT, 255))

    # ── Progress bar ──
    PROGRESS  = 0.05
    BAR_Y     = INFO_Y + 200
    BAR_H     = 6
    DOT_R     = 14
    total_ms  = track.get("duration_ms", 180_000)
    current_s = int(total_ms / 1000 * PROGRESS)

    _progress_bar(draw, PAD, BAR_Y, W - PAD, BAR_H, DOT_R,
                  PROGRESS, GREY_BAR, ACCENT)

    # time labels
    def fmt(s): return f"{s // 60}:{s % 60:02d}"
    draw.text((PAD, BAR_Y + BAR_H + 16), fmt(current_s), font=fn_time, fill=(*GREY_DIM, 255))
    rem = total_ms // 1000 - current_s
    rem_str = f"-{fmt(rem)}"
    rw = int(draw.textlength(rem_str, font=fn_time))
    draw.text((W - PAD - rw, BAR_Y + BAR_H + 16), rem_str, font=fn_time, fill=(*GREY_DIM, 255))

    # ── Controls ──
    CTRL_Y   = BAR_Y + 160
    ctrl_cx  = W // 2
    spacing  = 190
    dim      = GREY_DIM
    lw = 5

    _icon_shuffle(draw, ctrl_cx - spacing * 2,        CTRL_Y, 22, dim, lw)
    _icon_prev   (draw, ctrl_cx - spacing,             CTRL_Y, 28, WHITE, lw)
    _icon_play   (draw, ctrl_cx,                       CTRL_Y, 62, WHITE, (18, 18, 18))
    _icon_next   (draw, ctrl_cx + spacing,             CTRL_Y, 28, WHITE, lw)
    _icon_repeat (draw, ctrl_cx + spacing * 2,         CTRL_Y, 22, dim, lw)


def _render_vertical(cover: Image.Image, track: dict, bg: Image.Image) -> bytes:
    canvas = bg.convert("RGBA")
    _draw_vertical(canvas, cover, track)
    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=97, optimize=True)
    return buf.getvalue()


# ── Horizontal player  (1920 × 1080) ─────────────────────────────────────────

def _draw_horizontal(canvas: Image.Image, cover: Image.Image, track: dict):
    draw = ImageDraw.Draw(canvas, "RGBA")
    W, H = HW, HH
    PAD = 80

    # ── Album art (left half) ──
    ART_SIZE = H - PAD * 2          # 920 px
    ART_X    = PAD
    ART_Y    = PAD
    art = _rounded_art(cover, ART_SIZE, 20)
    canvas.alpha_composite(art, (ART_X, ART_Y))

    # ── Right panel ──
    RX     = ART_X + ART_SIZE + 90  # ~1170
    RW     = W - RX - PAD           # ~670

    VMID   = H // 2                 # 540 — vertical center of right panel

    fn_title  = _font(74, 700)
    fn_artist = _font(48, 400)
    fn_time   = _font(36, 400)

    # title + artist — centered vertically around VMID - 100
    title  = _truncate(draw, track["title"],  fn_title,  RW)
    artist = _truncate(draw, track["artist"], fn_artist, RW)

    title_y  = VMID - 160
    artist_y = title_y + 96

    draw.text((RX, title_y),  title,  font=fn_title,  fill=(*WHITE, 255))
    draw.text((RX, artist_y), artist, font=fn_artist, fill=(*GREY_TEXT, 255))

    # ── Progress bar ──
    PROGRESS  = 0.05
    BAR_Y     = VMID + 20
    BAR_H     = 6
    DOT_R     = 13
    total_ms  = track.get("duration_ms", 180_000)
    current_s = int(total_ms / 1000 * PROGRESS)

    _progress_bar(draw, RX, BAR_Y, RX + RW, BAR_H, DOT_R,
                  PROGRESS, GREY_BAR, ACCENT)

    def fmt(s): return f"{s // 60}:{s % 60:02d}"
    draw.text((RX, BAR_Y + BAR_H + 14), fmt(current_s), font=fn_time, fill=(*GREY_DIM, 255))
    rem = total_ms // 1000 - current_s
    rem_str = f"-{fmt(rem)}"
    rw = int(draw.textlength(rem_str, font=fn_time))
    draw.text((RX + RW - rw, BAR_Y + BAR_H + 14), rem_str, font=fn_time, fill=(*GREY_DIM, 255))

    # ── Controls ──
    CTRL_Y  = BAR_Y + 130
    ctrl_cx = RX + RW // 2
    spacing = 145
    dim     = GREY_DIM
    lw = 5

    _icon_shuffle(draw, ctrl_cx - spacing * 2,  CTRL_Y, 20, dim, lw)
    _icon_prev   (draw, ctrl_cx - spacing,       CTRL_Y, 26, WHITE, lw)
    _icon_play   (draw, ctrl_cx,                 CTRL_Y, 56, WHITE, (18, 18, 18))
    _icon_next   (draw, ctrl_cx + spacing,       CTRL_Y, 26, WHITE, lw)
    _icon_repeat (draw, ctrl_cx + spacing * 2,   CTRL_Y, 20, dim, lw)


def _render_horizontal(cover: Image.Image, track: dict, bg: Image.Image) -> bytes:
    canvas = bg.convert("RGBA")
    _draw_horizontal(canvas, cover, track)
    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=97, optimize=True)
    return buf.getvalue()


# ── Background factories ──────────────────────────────────────────────────────

def _dark_bg(w: int, h: int) -> Image.Image:
    return Image.new("RGB", (w, h), (18, 18, 18))


def _light_bg(w: int, h: int) -> Image.Image:
    return Image.new("RGB", (w, h), (242, 242, 242))


# ── Public API ────────────────────────────────────────────────────────────────

def generate_vertical_styles(track: dict, cover_bytes: bytes) -> dict[str, bytes]:
    cover  = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    colors = _extract_dominant_colors(cover)

    return {
        "dark":     _render_vertical(cover, track, _dark_bg(VW, VH)),
        "light":    _render_vertical(cover, track, _light_bg(VW, VH)),
        "blur":     _render_vertical(cover, track, _make_blurred_bg(cover, VW, VH)),
        "gradient": _render_vertical(cover, track, _make_gradient_bg(colors, VW, VH)),
    }


def generate_all_styles(track: dict, cover_bytes: bytes) -> dict[str, bytes]:
    cover  = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    colors = _extract_dominant_colors(cover)

    return {
        "dark":     _render_horizontal(cover, track, _dark_bg(HW, HH)),
        "light":    _render_horizontal(cover, track, _light_bg(HW, HH)),
        "blur":     _render_horizontal(cover, track, _make_blurred_bg(cover, HW, HH)),
        "gradient": _render_horizontal(cover, track, _make_gradient_bg(colors, HW, HH)),
    }
