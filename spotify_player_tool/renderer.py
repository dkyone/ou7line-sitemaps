from __future__ import annotations

import io
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ACCENT = (29, 185, 84)  # Spotify green

# Горизонтальный формат (16:9)
CANVAS_W, CANVAS_H = 1200, 630
ART_X, ART_Y, ART_SIZE = 70, 95, 440
TEXT_X, TEXT_MAX_X = 575, 1150
TEXT_W = TEXT_MAX_X - TEXT_X

# Вертикальный формат (9:16)
VERTICAL_W, VERTICAL_H = 540, 960
VERTICAL_ART_Y = 120
VERTICAL_ART_SIZE = 380
VERTICAL_TEXT_Y = 520
VERTICAL_PADDING = 40

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


@dataclass
class Theme:
    bg: Tuple[int, int, int]
    title: Tuple[int, int, int]
    artist: Tuple[int, int, int]
    album_c: Tuple[int, int, int]
    bar_bg: Tuple[int, int, int]
    controls: Tuple[int, int, int]
    play_inner: Tuple[int, int, int]
    time_c: Tuple[int, int, int]
    card: Optional[Tuple[int, int, int, int]] = None


DARK = Theme(
    bg=(18, 18, 18),
    title=(255, 255, 255),
    artist=(179, 179, 179),
    album_c=(100, 100, 100),
    bar_bg=(83, 83, 83),
    controls=(255, 255, 255),
    play_inner=(18, 18, 18),
    time_c=(100, 100, 100),
)

LIGHT = Theme(
    bg=(240, 240, 240),
    title=(18, 18, 18),
    artist=(80, 80, 80),
    album_c=(155, 155, 155),
    bar_bg=(195, 195, 195),
    controls=(40, 40, 40),
    play_inner=(240, 240, 240),
    time_c=(155, 155, 155),
)

BLUR = Theme(
    bg=(0, 0, 0),
    title=(255, 255, 255),
    artist=(210, 210, 210),
    album_c=(170, 170, 170),
    bar_bg=(175, 175, 175),
    controls=(255, 255, 255),
    play_inner=(15, 15, 15),
    time_c=(170, 170, 170),
    card=(10, 10, 10, 155),
)

GRADIENT = Theme(
    bg=(0, 0, 0),
    title=(255, 255, 255),
    artist=(210, 210, 210),
    album_c=(170, 170, 170),
    bar_bg=(175, 175, 175),
    controls=(255, 255, 255),
    play_inner=(15, 15, 15),
    time_c=(170, 170, 170),
    card=(0, 0, 0, 100),
)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


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
    m = ImageDraw.Draw(mask)
    m.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    img.putalpha(mask)
    return img


def _extract_dominant_colors(img: Image.Image) -> List[Tuple[int, int, int]]:
    small = img.resize((80, 80), Image.LANCZOS).convert("RGB")
    quantized = small.quantize(colors=8)
    palette = quantized.getpalette()

    num_colors = min(8, len(palette) // 3)
    colors = [(palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]) for i in range(num_colors)]

    def score(c: tuple) -> float:
        r, g, b = c
        return (max(r, g, b) - min(r, g, b)) * 0.65 + (r + g + b) / 3 * 0.35

    colors.sort(key=score, reverse=True)
    return colors[:3] if colors else [(128, 128, 128)]


def _blur_background(cover: Image.Image) -> Image.Image:
    scale = max(CANVAS_W / cover.width, CANVAS_H / cover.height)
    nw = int(cover.width * scale) + 2
    nh = int(cover.height * scale) + 2
    bg = cover.resize((nw, nh), Image.LANCZOS).convert("RGB")
    left = (nw - CANVAS_W) // 2
    top = (nh - CANVAS_H) // 2
    bg = bg.crop((left, top, left + CANVAS_W, top + CANVAS_H))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
    dark = Image.new("RGB", (CANVAS_W, CANVAS_H), (0, 0, 0))
    return Image.blend(bg, dark, alpha=0.40)


def _gradient_background(colors: List[Tuple[int, int, int]]) -> Image.Image:
    def darken(c: tuple, f: float) -> tuple:
        return tuple(max(0, int(v * f)) for v in c)

    c1 = darken(colors[0], 0.52)
    c2 = darken(colors[1] if len(colors) > 1 else colors[0], 0.38)

    img = Image.new("RGB", (CANVAS_W, CANVAS_H))
    draw = ImageDraw.Draw(img)
    for y in range(CANVAS_H):
        t = y / (CANVAS_H - 1)
        color = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
        draw.line([(0, y), (CANVAS_W, y)], fill=color)
    return img


# ── Control icon drawers ─────────────────────────────────────────────────────

def _draw_prev(draw: ImageDraw.ImageDraw, cx: int, cy: int, s: int, color: tuple):
    h = int(s * 1.35)
    draw.polygon([(cx + s, cy - h), (cx + s, cy + h), (cx - s, cy)], fill=color)
    bx = cx - s - 5
    draw.rectangle([bx, cy - h, bx + 3, cy + h], fill=color)


def _draw_next(draw: ImageDraw.ImageDraw, cx: int, cy: int, s: int, color: tuple):
    h = int(s * 1.35)
    draw.polygon([(cx - s, cy - h), (cx - s, cy + h), (cx + s, cy)], fill=color)
    bx = cx + s + 2
    draw.rectangle([bx, cy - h, bx + 3, cy + h], fill=color)


def _draw_play(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int,
               fg: tuple, inner: tuple):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fg)
    ts = int(r * 0.42)
    draw.polygon([
        (cx - int(ts * 0.68), cy - ts),
        (cx - int(ts * 0.68), cy + ts),
        (cx + ts, cy),
    ], fill=inner)


def _draw_shuffle(draw: ImageDraw.ImageDraw, cx: int, cy: int, s: int, color: tuple):
    lw = 2
    hs = s // 3
    # Upper diagonal: bottom-left → top-right, with arrowhead
    x0, y0 = cx - s, cy + hs
    x1, y1 = cx + s, cy - hs
    draw.line([x0, y0, x1, y1], fill=color, width=lw)
    draw.polygon([(x1 - 5, y1 - 3), (x1, y1), (x1 - 3, y1 + 5)], fill=color)
    # Lower diagonal: top-left → bottom-right, with arrowhead
    x2, y2 = cx - s, cy - hs
    x3, y3 = cx + s, cy + hs
    draw.line([x2, y2, x3, y3], fill=color, width=lw)
    draw.polygon([(x3 - 5, y3 + 3), (x3, y3), (x3 - 3, y3 - 5)], fill=color)


def _draw_repeat(draw: ImageDraw.ImageDraw, cx: int, cy: int, s: int, color: tuple):
    r = s - 1
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=35, end=325, fill=color, width=2)
    # Arrow at end of arc (~325°)
    angle = math.radians(325)
    ax = cx + int(r * math.cos(angle))
    ay = cy + int(r * math.sin(angle))
    draw.polygon([(ax - 4, ay - 3), (ax + 3, ay), (ax - 4, ay + 3)], fill=color)
    # Arrow at start of arc (~35°)
    angle2 = math.radians(35)
    bx = cx + int(r * math.cos(angle2))
    by = cy + int(r * math.sin(angle2))
    draw.polygon([(bx + 4, by - 3), (bx - 3, by), (bx + 4, by + 3)], fill=color)


# ── Main player UI ───────────────────────────────────────────────────────────

def _draw_player(canvas: Image.Image, cover: Image.Image, track: dict, theme: Theme):
    draw = ImageDraw.Draw(canvas, "RGBA")

    # Card overlay for blur/gradient styles
    if theme.card:
        draw.rounded_rectangle(
            [TEXT_X - 28, 52, TEXT_MAX_X + 18, CANVAS_H - 52],
            radius=24,
            fill=theme.card,
        )

    # Album art with rounded corners
    art = _rounded_art(cover, ART_SIZE, 24)
    canvas.alpha_composite(art, (ART_X, ART_Y))

    # NOW PLAYING label
    fn_label = _font(16)
    draw.text((TEXT_X, 115), "NOW PLAYING", font=fn_label, fill=(*ACCENT, 255))

    # Track title
    fn_title = _font(50, bold=True)
    title = _truncate(draw, track["title"], fn_title, TEXT_W)
    draw.text((TEXT_X, 145), title, font=fn_title, fill=(*theme.title, 255))

    # Artist
    fn_artist = _font(31)
    artist = _truncate(draw, track["artist"], fn_artist, TEXT_W)
    draw.text((TEXT_X, 214), artist, font=fn_artist, fill=(*theme.artist, 255))

    # Album
    fn_album = _font(21)
    album = _truncate(draw, track["album"], fn_album, TEXT_W)
    draw.text((TEXT_X, 258), album, font=fn_album, fill=(*theme.album_c, 255))

    # Progress bar
    BAR_Y = 358
    BAR_H = 5
    PROGRESS = 0.40
    bar_end = TEXT_X + int(TEXT_W * PROGRESS)

    draw.rounded_rectangle(
        [TEXT_X, BAR_Y, TEXT_MAX_X, BAR_Y + BAR_H], radius=3, fill=(*theme.bar_bg, 255)
    )
    draw.rounded_rectangle(
        [TEXT_X, BAR_Y, bar_end, BAR_Y + BAR_H], radius=3, fill=(*ACCENT, 255)
    )
    # Indicator dot
    ci_y = BAR_Y + BAR_H // 2
    draw.ellipse([bar_end - 7, ci_y - 7, bar_end + 7, ci_y + 7], fill=(*ACCENT, 255))

    # Time labels
    fn_time = _font(18)
    total_ms = track.get("duration_ms", 180000)
    current_ms = int(total_ms * PROGRESS)

    def fmt(ms: int) -> str:
        s = ms // 1000
        return f"{s // 60}:{s % 60:02d}"

    draw.text((TEXT_X, BAR_Y + 14), fmt(current_ms), font=fn_time, fill=(*theme.time_c, 255))
    total_str = fmt(total_ms)
    tw = int(draw.textlength(total_str, font=fn_time))
    draw.text((TEXT_MAX_X - tw, BAR_Y + 14), total_str, font=fn_time, fill=(*theme.time_c, 255))

    # Controls
    CTRL_Y = 462
    ctrl_cx = (TEXT_X + TEXT_MAX_X) // 2
    spacing = 100
    dim_color = tuple(max(0, int(c * 0.55)) for c in theme.controls)

    _draw_shuffle(draw, ctrl_cx - spacing * 2 + 10, CTRL_Y, 12, dim_color)
    _draw_prev(draw, ctrl_cx - spacing, CTRL_Y, 14, theme.controls)
    _draw_play(draw, ctrl_cx, CTRL_Y, 30, theme.controls, theme.play_inner)
    _draw_next(draw, ctrl_cx + spacing, CTRL_Y, 14, theme.controls)
    _draw_repeat(draw, ctrl_cx + spacing * 2 - 10, CTRL_Y, 12, dim_color)

    # Spotify branding
    fn_brand = _font(19, bold=True)
    draw.text((TEXT_X, CANVAS_H - 55), "Spotify", font=fn_brand, fill=(*ACCENT, 255))


def _draw_player_vertical(canvas: Image.Image, cover: Image.Image, track: dict, theme: Theme):
    draw = ImageDraw.Draw(canvas, "RGBA")

    # Card overlay for blur/gradient
    if theme.card:
        draw.rounded_rectangle(
            [20, VERTICAL_TEXT_Y - 20, VERTICAL_W - 20, VERTICAL_H - 60],
            radius=20,
            fill=theme.card,
        )

    # Album art centered at top
    art = _rounded_art(cover, VERTICAL_ART_SIZE, 24)
    art_x = (VERTICAL_W - VERTICAL_ART_SIZE) // 2
    canvas.alpha_composite(art, (art_x, VERTICAL_ART_Y))

    # Track title
    fn_title = _font(32, bold=True)
    title = _truncate(draw, track["title"], fn_title, VERTICAL_W - VERTICAL_PADDING * 2)
    title_y = VERTICAL_TEXT_Y
    draw.text((VERTICAL_PADDING, title_y), title, font=fn_title, fill=(*theme.title, 255))

    # Artist
    fn_artist = _font(20)
    artist = _truncate(draw, track["artist"], fn_artist, VERTICAL_W - VERTICAL_PADDING * 2)
    draw.text((VERTICAL_PADDING, title_y + 50), artist, font=fn_artist, fill=(*theme.artist, 255))

    # Album
    fn_album = _font(16)
    album = _truncate(draw, track["album"], fn_album, VERTICAL_W - VERTICAL_PADDING * 2)
    draw.text((VERTICAL_PADDING, title_y + 85), album, font=fn_album, fill=(*theme.album_c, 255))

    # Progress bar
    BAR_Y = title_y + 130
    BAR_H = 4
    PROGRESS = 0.40
    bar_end = VERTICAL_PADDING + int((VERTICAL_W - VERTICAL_PADDING * 2) * PROGRESS)

    draw.rounded_rectangle(
        [VERTICAL_PADDING, BAR_Y, VERTICAL_W - VERTICAL_PADDING, BAR_Y + BAR_H],
        radius=2,
        fill=(*theme.bar_bg, 255),
    )
    draw.rounded_rectangle(
        [VERTICAL_PADDING, BAR_Y, bar_end, BAR_Y + BAR_H],
        radius=2,
        fill=(*ACCENT, 255),
    )

    # Time labels
    fn_time = _font(14)
    total_ms = track.get("duration_ms", 180000)
    current_ms = int(total_ms * PROGRESS)

    def fmt(ms: int) -> str:
        s = ms // 1000
        return f"{s // 60}:{s % 60:02d}"

    draw.text((VERTICAL_PADDING, BAR_Y + 10), fmt(current_ms), font=fn_time, fill=(*theme.time_c, 255))
    total_str = fmt(total_ms)
    tw = int(draw.textlength(total_str, font=fn_time))
    draw.text((VERTICAL_W - VERTICAL_PADDING - tw, BAR_Y + 10), total_str, font=fn_time, fill=(*theme.time_c, 255))

    # Controls
    CTRL_Y = BAR_Y + 50
    ctrl_cx = VERTICAL_W // 2
    spacing = 50
    dim_color = tuple(max(0, int(c * 0.55)) for c in theme.controls)

    _draw_shuffle(draw, ctrl_cx - spacing * 1.5, CTRL_Y, 10, dim_color)
    _draw_prev(draw, ctrl_cx - spacing * 0.5, CTRL_Y, 12, theme.controls)
    _draw_play(draw, ctrl_cx + spacing * 0.5, CTRL_Y, 25, theme.controls, theme.play_inner)
    _draw_next(draw, ctrl_cx + spacing * 1.5, CTRL_Y, 12, theme.controls)

    # Spotify branding
    fn_brand = _font(14, bold=True)
    draw.text((VERTICAL_PADDING, VERTICAL_H - 30), "Spotify", font=fn_brand, fill=(*ACCENT, 255))


def _blur_background_vertical(cover: Image.Image) -> Image.Image:
    scale = max(VERTICAL_W / cover.width, VERTICAL_H / cover.height)
    nw = int(cover.width * scale) + 2
    nh = int(cover.height * scale) + 2
    bg = cover.resize((nw, nh), Image.LANCZOS).convert("RGB")
    left = (nw - VERTICAL_W) // 2
    top = (nh - VERTICAL_H) // 2
    bg = bg.crop((left, top, left + VERTICAL_W, top + VERTICAL_H))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
    dark = Image.new("RGB", (VERTICAL_W, VERTICAL_H), (0, 0, 0))
    return Image.blend(bg, dark, alpha=0.40)


def _gradient_background_vertical(colors: List[Tuple[int, int, int]]) -> Image.Image:
    def darken(c: tuple, f: float) -> tuple:
        return tuple(max(0, int(v * f)) for v in c)

    c1 = darken(colors[0], 0.52)
    c2 = darken(colors[1] if len(colors) > 1 else colors[0], 0.38)

    img = Image.new("RGB", (VERTICAL_W, VERTICAL_H))
    draw = ImageDraw.Draw(img)
    for y in range(VERTICAL_H):
        t = y / (VERTICAL_H - 1)
        color = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
        draw.line([(0, y), (VERTICAL_W, y)], fill=color)
    return img


def _render_vertical(background: Image.Image, cover: Image.Image, track: dict, theme: Theme) -> bytes:
    canvas = background.convert("RGBA")
    _draw_player_vertical(canvas, cover, track, theme)
    result = canvas.convert("RGB")
    buf = io.BytesIO()
    result.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue()


def _render(background: Image.Image, cover: Image.Image, track: dict, theme: Theme) -> bytes:
    canvas = background.convert("RGBA")
    _draw_player(canvas, cover, track, theme)
    result = canvas.convert("RGB")
    buf = io.BytesIO()
    result.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue()


def generate_all_styles(track: dict, cover_bytes: bytes) -> dict[str, bytes]:
    cover = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    colors = _extract_dominant_colors(cover)

    return {
        "dark":     _render(Image.new("RGB", (CANVAS_W, CANVAS_H), DARK.bg),  cover, track, DARK),
        "light":    _render(Image.new("RGB", (CANVAS_W, CANVAS_H), LIGHT.bg), cover, track, LIGHT),
        "blur":     _render(_blur_background(cover),                            cover, track, BLUR),
        "gradient": _render(_gradient_background(colors),                       cover, track, GRADIENT),
    }


def generate_vertical_styles(track: dict, cover_bytes: bytes) -> dict[str, bytes]:
    cover = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
    colors = _extract_dominant_colors(cover)

    return {
        "dark":     _render_vertical(Image.new("RGB", (VERTICAL_W, VERTICAL_H), DARK.bg),  cover, track, DARK),
        "light":    _render_vertical(Image.new("RGB", (VERTICAL_W, VERTICAL_H), LIGHT.bg), cover, track, LIGHT),
        "blur":     _render_vertical(_blur_background_vertical(cover),                       cover, track, BLUR),
        "gradient": _render_vertical(_gradient_background_vertical(colors),                  cover, track, GRADIENT),
    }
