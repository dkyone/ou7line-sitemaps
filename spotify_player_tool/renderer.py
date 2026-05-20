from __future__ import annotations

import io
import math
from dataclasses import dataclass
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ── Accent ────────────────────────────────────────────────────────────────────
ACCENT = (30, 215, 96)   # Spotify green #1ED760

# ── Resolutions ───────────────────────────────────────────────────────────────
VW, VH   = 1080, 1440   # vertical   3:4
HW, HH   = 1920, 1080   # horizontal 16:9
SW, SH   = 1080, 1080   # square     1:1

# ── Font ──────────────────────────────────────────────────────────────────────
_INTER    = "/usr/share/fonts/truetype/InterVariable.ttf"
_FB_BOLD  = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
_FB_REG   = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def _font(size: int, weight: int = 400) -> ImageFont.FreeTypeFont:
    try:
        f = ImageFont.truetype(_INTER, size)
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
        return f
    except OSError:
        path = _FB_BOLD if weight >= 600 else _FB_REG
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            return ImageFont.load_default()


# ── Theme ─────────────────────────────────────────────────────────────────────
@dataclass
class Theme:
    text1:     Tuple[int, int, int]   # title
    text2:     Tuple[int, int, int]   # artist
    time_c:    Tuple[int, int, int]   # time labels
    btn:       Tuple[int, int, int]   # prev / next
    dim:       Tuple[int, int, int]   # shuffle / repeat
    play_fg:   Tuple[int, int, int]   # play circle
    play_tri:  Tuple[int, int, int]   # triangle inside play
    bar_track: Tuple[int, int, int]   # progress track


DARK = Theme(
    text1=(255, 255, 255), text2=(179, 179, 179), time_c=(100, 100, 100),
    btn=(255, 255, 255), dim=(100, 100, 100),
    play_fg=(255, 255, 255), play_tri=(18, 18, 18),
    bar_track=(83, 83, 83),
)

LIGHT = Theme(
    text1=(18, 18, 18), text2=(80, 80, 80), time_c=(140, 140, 140),
    btn=(18, 18, 18), dim=(160, 160, 160),
    play_fg=(18, 18, 18), play_tri=(255, 255, 255),
    bar_track=(200, 200, 200),
)

# For square format: art fills canvas so progress bar needs to be light enough to read
DARK_PHOTO = Theme(
    text1=(255, 255, 255), text2=(215, 215, 215), time_c=(190, 190, 190),
    btn=(255, 255, 255), dim=(175, 175, 175),
    play_fg=(255, 255, 255), play_tri=(18, 18, 18),
    bar_track=(200, 200, 200),
)


# ── Helpers ───────────────────────────────────────────────────────────────────
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


def _make_blurred_bg(cover: Image.Image, w: int, h: int,
                     blur: int = 60, darkness: float = 0.55) -> Image.Image:
    scale = max(w / cover.width, h / cover.height) * 1.1
    nw, nh = int(cover.width * scale), int(cover.height * scale)
    bg = cover.resize((nw, nh), Image.LANCZOS).convert("RGB")
    bg = bg.crop(((nw - w) // 2, (nh - h) // 2,
                   (nw - w) // 2 + w, (nh - h) // 2 + h))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=blur))
    return Image.blend(bg, Image.new("RGB", (w, h), (0, 0, 0)), alpha=darkness)


def _make_gradient_bg(colors: List[Tuple[int, int, int]], w: int, h: int) -> Image.Image:
    def dk(c, f): return tuple(max(0, int(v * f)) for v in c)
    c1, c2 = dk(colors[0], 0.45), dk(colors[1] if len(colors) > 1 else colors[0], 0.28)
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(c1[i]*(1-t) + c2[i]*t) for i in range(3)))
    return img


def _dark_bg(w: int, h: int) -> Image.Image:
    return Image.new("RGB", (w, h), (18, 18, 18))


def _light_bg(w: int, h: int) -> Image.Image:
    return Image.new("RGB", (w, h), (242, 242, 242))


# ── Icons ─────────────────────────────────────────────────────────────────────

def _arrowhead(draw: ImageDraw.ImageDraw, tip_x: int, tip_y: int,
               angle_rad: float, size: int, color: tuple):
    """Draw filled arrowhead pointing toward (tip_x, tip_y) at given angle."""
    back = size
    side = size * 0.55
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    bx = tip_x - int(back * cos_a)
    by = tip_y - int(back * sin_a)
    lx = int(bx - side * sin_a)
    ly = int(by + side * cos_a)
    rx = int(bx + side * sin_a)
    ry = int(by - side * cos_a)
    draw.polygon([(tip_x, tip_y), (lx, ly), (rx, ry)], fill=color)


def _icon_shuffle(draw: ImageDraw.ImageDraw,
                  cx: int, cy: int, s: int, color: tuple, lw: int = 4):
    """Two crossing diagonals (X-shape) both pointing right, Spotify-style."""
    hs  = int(s * 0.50)    # wider X for visibility
    tip = lw + 7

    def _line_to_tip(x0, y0, x1, y1, angle):
        """Draw line stopping short so arrowhead sits cleanly at tip."""
        ca, sa = math.cos(angle), math.sin(angle)
        draw.line([(x0, y0), (x1 - int(tip * ca), y1 - int(tip * sa))],
                  fill=color, width=lw)
        _arrowhead(draw, x1, y1, angle, tip, color)

    # ── Arrow A: top-left → bottom-right ──
    ax0, ay0 = cx - s, cy - hs
    ax1, ay1 = cx + s, cy + hs
    ang_a = math.atan2(ay1 - ay0, ax1 - ax0)
    _line_to_tip(ax0, ay0, ax1, ay1, ang_a)

    # ── Arrow B: bottom-left → top-right  (gapped at crossing center) ──
    bx0, by0 = cx - s, cy + hs
    bx1, by1 = cx + s, cy - hs
    ang_b = math.atan2(by1 - by0, bx1 - bx0)
    cb, sb = math.cos(ang_b), math.sin(ang_b)
    gap = lw * 2 + 6
    # left half: from origin to gap before center
    draw.line([(bx0, by0), (cx - int(gap * cb), cy - int(gap * sb))],
              fill=color, width=lw)
    # right half: from gap after center, stopping short for tip
    p2x = cx + int(gap * cb);  p2y = cy + int(gap * sb)
    draw.line([(p2x, p2y), (bx1 - int(tip * cb), by1 - int(tip * sb))],
              fill=color, width=lw)
    _arrowhead(draw, bx1, by1, ang_b, tip, color)


def _icon_prev(draw: ImageDraw.ImageDraw,
               cx: int, cy: int, s: int, color: tuple, lw: int = 4):
    h = int(s * 1.25)
    draw.polygon([(cx + s, cy - h), (cx + s, cy + h), (cx - s + 4, cy)], fill=color)
    draw.rectangle([cx - s - 2, cy - h, cx - s + lw, cy + h], fill=color)


def _icon_next(draw: ImageDraw.ImageDraw,
               cx: int, cy: int, s: int, color: tuple, lw: int = 4):
    h = int(s * 1.25)
    draw.polygon([(cx - s, cy - h), (cx - s, cy + h), (cx + s - 4, cy)], fill=color)
    draw.rectangle([cx + s - lw, cy - h, cx + s + 2, cy + h], fill=color)


def _icon_play(draw: ImageDraw.ImageDraw,
               cx: int, cy: int, r: int, fg: tuple, tri: tuple):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fg)
    ts = int(r * 0.38)
    draw.polygon([
        (cx - int(ts * 0.65), cy - ts),
        (cx - int(ts * 0.65), cy + ts),
        (cx + ts + 3,         cy),
    ], fill=tri)


def _icon_repeat(draw: ImageDraw.ImageDraw,
                 cx: int, cy: int, s: int, color: tuple, lw: int = 4):
    """Rounded-rectangle clockwise loop — Spotify repeat icon."""
    w   = int(s * 1.9)
    h   = int(s * 1.3)
    r   = int(s * 0.45)
    tip = lw + 6

    l  = cx - w // 2
    ri = cx + w // 2
    t  = cy - h // 2
    b  = cy + h // 2

    # top edge → : stop short so arrowhead sits cleanly at the corner
    draw.line([(l + r, t), (ri - r - tip, t)], fill=color, width=lw)
    # arrowhead at end of top edge pointing RIGHT  ←this is where direction shows
    _arrowhead(draw, ri - r, t, math.radians(0), tip, color)
    # top-right arc
    draw.arc([ri - 2*r, t, ri, t + 2*r],   start=270, end=0,   fill=color, width=lw)
    # right edge ↓
    draw.line([(ri, t + r), (ri, b - r)],  fill=color, width=lw)
    # bottom-right arc
    draw.arc([ri - 2*r, b - 2*r, ri, b],   start=0,   end=90,  fill=color, width=lw)
    # bottom edge ←
    draw.line([(l + r, b), (ri - r, b)],   fill=color, width=lw)
    # bottom-left arc
    draw.arc([l, b - 2*r, l + 2*r, b],     start=90,  end=180, fill=color, width=lw)
    # left edge ↑
    draw.line([(l, t + r), (l, b - r)],    fill=color, width=lw)
    # top-left arc
    draw.arc([l, t, l + 2*r, t + 2*r],     start=180, end=270, fill=color, width=lw)


def _progress_bar(draw: ImageDraw.ImageDraw,
                  x0: int, y: int, x1: int,
                  bar_h: int, dot_r: int,
                  progress: float, track_color: tuple, fill_color: tuple):
    fe = x0 + int((x1 - x0) * progress)
    draw.rounded_rectangle([x0, y, x1,  y + bar_h], radius=bar_h // 2, fill=(*track_color, 255))
    draw.rounded_rectangle([x0, y, fe,  y + bar_h], radius=bar_h // 2, fill=(*fill_color,  255))
    mcy = y + bar_h // 2
    draw.ellipse([fe - dot_r, mcy - dot_r, fe + dot_r, mcy + dot_r], fill=(*fill_color, 255))


# ── Shared drawing logic ──────────────────────────────────────────────────────

def _draw_controls(draw: ImageDraw.ImageDraw, ctrl_cx: int, ctrl_cy: int,
                   spacing: int, play_r: int, s_icon: int,
                   theme: Theme, lw: int = 5):
    _icon_shuffle(draw, ctrl_cx - spacing * 2, ctrl_cy, s_icon, theme.dim, lw)
    _icon_prev   (draw, ctrl_cx - spacing,     ctrl_cy, int(s_icon * 1.3), theme.btn, lw)
    _icon_play   (draw, ctrl_cx,               ctrl_cy, play_r, theme.play_fg, theme.play_tri)
    _icon_next   (draw, ctrl_cx + spacing,     ctrl_cy, int(s_icon * 1.3), theme.btn, lw)
    _icon_repeat (draw, ctrl_cx + spacing * 2, ctrl_cy, s_icon, theme.dim, lw)


def _draw_info(draw: ImageDraw.ImageDraw,
               track: dict, theme: Theme,
               text_x: int, text_y: int, text_w: int,
               fn_title, fn_artist, fn_time,
               bar_x0: int, bar_x1: int, bar_y: int, bar_h: int, dot_r: int):
    """Draw title, artist, progress bar, time labels."""
    title  = _truncate(draw, track["title"],  fn_title,  text_w)
    artist = _truncate(draw, track["artist"], fn_artist, text_w - 60)

    draw.text((text_x, text_y),              title,  font=fn_title,  fill=(*theme.text1, 255))
    draw.text((text_x, text_y + fn_title.size + 18), artist, font=fn_artist, fill=(*theme.text2, 255))

    PROGRESS  = 0.05
    total_ms  = track.get("duration_ms", 180_000)
    current_s = int(total_ms / 1000 * PROGRESS)

    _progress_bar(draw, bar_x0, bar_y, bar_x1, bar_h, dot_r,
                  PROGRESS, theme.bar_track, ACCENT)

    def fmt(s): return f"{s // 60}:{s % 60:02d}"
    rem_str = f"-{fmt(total_ms // 1000 - current_s)}"
    rw = int(draw.textlength(rem_str, font=fn_time))

    draw.text((bar_x0, bar_y + bar_h + 14), fmt(current_s),  font=fn_time, fill=(*theme.time_c, 255))
    draw.text((bar_x1 - rw, bar_y + bar_h + 14), rem_str,    font=fn_time, fill=(*theme.time_c, 255))


# ── Vertical  1080 × 1440  (3:4) ─────────────────────────────────────────────

def _draw_vertical(canvas: Image.Image, cover: Image.Image,
                   track: dict, theme: Theme):
    draw  = ImageDraw.Draw(canvas, "RGBA")
    W, H  = VW, VH
    PAD   = 60                        # equal on all four sides

    ART_SIZE = W - PAD * 2            # 960 px — equal left/right/top margin
    art = _rounded_art(cover, ART_SIZE, 22)
    canvas.alpha_composite(art, (PAD, PAD))

    INFO_Y = PAD + ART_SIZE + 36      # 60 + 960 + 36 = 1056
    TEXT_W = W - PAD * 2

    fn_title  = _font(60, 700)
    fn_artist = _font(40, 400)
    fn_time   = _font(30, 400)

    _draw_info(draw, track, theme,
               text_x=PAD, text_y=INFO_Y, text_w=TEXT_W,
               fn_title=fn_title, fn_artist=fn_artist, fn_time=fn_time,
               bar_x0=PAD, bar_x1=W - PAD,
               bar_y=INFO_Y + 140, bar_h=6, dot_r=13)

    _draw_controls(draw,
                   ctrl_cx=W // 2, ctrl_cy=INFO_Y + 268,
                   spacing=165, play_r=52, s_icon=19,
                   theme=theme, lw=5)


# ── Horizontal  1920 × 1080 ──────────────────────────────────────────────────

def _draw_horizontal(canvas: Image.Image, cover: Image.Image,
                     track: dict, theme: Theme):
    draw  = ImageDraw.Draw(canvas, "RGBA")
    W, H  = HW, HH
    PAD   = 80

    ART_SIZE = H - PAD * 2
    art = _rounded_art(cover, ART_SIZE, 22)
    canvas.alpha_composite(art, (PAD, PAD))

    RX   = PAD + ART_SIZE + 90
    RW   = W - RX - PAD
    VMID = H // 2

    fn_title  = _font(74, 700)
    fn_artist = _font(50, 400)
    fn_time   = _font(36, 400)

    _draw_info(draw, track, theme,
               text_x=RX, text_y=VMID - 170, text_w=RW,
               fn_title=fn_title, fn_artist=fn_artist, fn_time=fn_time,
               bar_x0=RX, bar_x1=RX + RW,
               bar_y=VMID + 20, bar_h=6, dot_r=13)

    _draw_controls(draw,
                   ctrl_cx=RX + RW // 2, ctrl_cy=VMID + 165,
                   spacing=145, play_r=56, s_icon=20,
                   theme=theme, lw=5)


# ── Square  1080 × 1080  (full-art + gradient overlay) ───────────────────────

def _make_square_art_canvas(cover: Image.Image, style: str,
                             colors: List[Tuple[int, int, int]]) -> Image.Image:
    """Full-canvas cover art with a bottom-to-top gradient overlay."""
    W, H = SW, SH

    # scale cover to fill the whole canvas
    scale = max(W / cover.width, H / cover.height)
    nw, nh = int(cover.width * scale), int(cover.height * scale)
    bg = cover.resize((nw, nh), Image.LANCZOS).convert("RGB")
    bg = bg.crop(((nw - W) // 2, (nh - H) // 2,
                   (nw - W) // 2 + W, (nh - H) // 2 + H))

    if style == "blur":
        bg = bg.filter(ImageFilter.GaussianBlur(radius=28))

    canvas = bg.convert("RGBA")

    # bottom-to-top gradient overlay
    grad  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd    = ImageDraw.Draw(grad)
    START = int(H * 0.35)             # gradient begins 35% from top

    for y in range(START, H):
        t = (y - START) / (H - START - 1)   # 0 → 1 top-to-bottom

        if style == "light":
            alpha = int(210 * t)
            gd.line([(0, y), (W, y)], fill=(245, 245, 245, alpha))
        elif style == "gradient":
            c1 = colors[0]
            c2 = colors[1] if len(colors) > 1 else colors[0]
            def dk(c, f): return tuple(max(0, int(v * f)) for v in c)
            col = tuple(int(dk(c1, 0.55)[i] * (1 - t) + dk(c2, 0.35)[i] * t)
                        for i in range(3))
            alpha = int(215 * t)
            gd.line([(0, y), (W, y)], fill=(*col, alpha))
        else:                          # dark / blur
            alpha = int(230 * t)
            gd.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))

    canvas.alpha_composite(grad)
    return canvas


def _draw_square(canvas: Image.Image, cover: Image.Image,
                 track: dict, theme: Theme):
    """Draw player UI on a square canvas that already has art + gradient bg."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    W, H = SW, SH
    PAD  = 54

    # anchor everything from the bottom
    BOTTOM   = H - PAD            # 1026
    ctrl_cy  = BOTTOM - 58        # 968
    bar_y    = ctrl_cy  - 128     # 840
    INFO_Y   = bar_y    - 155     # 685

    fn_title  = _font(54, 700)
    fn_artist = _font(36, 400)
    fn_time   = _font(28, 400)

    _draw_info(draw, track, theme,
               text_x=PAD, text_y=INFO_Y, text_w=W - PAD * 2,
               fn_title=fn_title, fn_artist=fn_artist, fn_time=fn_time,
               bar_x0=PAD, bar_x1=W - PAD,
               bar_y=bar_y, bar_h=5, dot_r=11)

    _draw_controls(draw,
                   ctrl_cx=W // 2, ctrl_cy=ctrl_cy,
                   spacing=148, play_r=48, s_icon=17,
                   theme=theme, lw=4)


# ── Render helpers ────────────────────────────────────────────────────────────

def _render(draw_fn, cover: Image.Image, track: dict,
            theme: Theme, bg: Image.Image) -> bytes:
    canvas = bg.convert("RGBA")
    draw_fn(canvas, cover, track, theme)
    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=97, optimize=True)
    return buf.getvalue()


def _all_themes(draw_fn, cover, track, colors, w, h):
    return {
        "dark":     _render(draw_fn, cover, track, DARK,  _dark_bg(w, h)),
        "light":    _render(draw_fn, cover, track, LIGHT, _light_bg(w, h)),
        "blur":     _render(draw_fn, cover, track, DARK,  _make_blurred_bg(cover, w, h)),
        "gradient": _render(draw_fn, cover, track, DARK,  _make_gradient_bg(colors, w, h)),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def generate_vertical_styles(track: dict, cover_bytes: bytes) -> dict[str, bytes]:
    cover  = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    return _all_themes(_draw_vertical, cover, track,
                       _extract_dominant_colors(cover), VW, VH)


def generate_all_styles(track: dict, cover_bytes: bytes) -> dict[str, bytes]:
    cover  = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    return _all_themes(_draw_horizontal, cover, track,
                       _extract_dominant_colors(cover), HW, HH)


def generate_square_styles(track: dict, cover_bytes: bytes) -> dict[str, bytes]:
    cover  = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    colors = _extract_dominant_colors(cover)

    style_theme = {
        "dark":     (DARK_PHOTO, "dark"),
        "light":    (LIGHT,      "light"),
        "blur":     (DARK_PHOTO, "blur"),
        "gradient": (DARK_PHOTO, "gradient"),
    }
    result: dict[str, bytes] = {}
    for name, (theme, style) in style_theme.items():
        canvas = _make_square_art_canvas(cover, style, colors)
        _draw_square(canvas, cover, track, theme)
        buf = io.BytesIO()
        canvas.convert("RGB").save(buf, format="JPEG", quality=97, optimize=True)
        result[name] = buf.getvalue()
    return result
