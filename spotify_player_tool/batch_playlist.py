#!/usr/bin/env python3
"""
Batch-render Spotify playlist tracks as player card images.

Usage:
    SPOTIFY_CLIENT_ID=xxx SPOTIFY_CLIENT_SECRET=yyy \
        python3 batch_playlist.py <spotify_playlist_url> [--style dark|light|blur|gradient]

Output folder: ./output/<playlist_id>/
"""
from __future__ import annotations

import io
import os
import re
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from renderer import (
    DARK, LIGHT, BLUR, GRADIENT,
    _render, _extract_dominant_colors,
    _blur_background, _gradient_background,
    generate_all_styles,
)
from spotify_client import get_playlist_tracks, download_cover

CANVAS_W, CANVAS_H = 1200, 630

STYLE_MAP = {
    "dark":     (DARK,     lambda _bg, _c: Image.new("RGB", (CANVAS_W, CANVAS_H), DARK.bg)),
    "light":    (LIGHT,    lambda _bg, _c: Image.new("RGB", (CANVAS_W, CANVAS_H), LIGHT.bg)),
    "blur":     (BLUR,     lambda bg, _c: _blur_background(bg)),
    "gradient": (GRADIENT, lambda _bg, c: _gradient_background(c)),
}


def _safe_name(title: str, artist: str, idx: int) -> str:
    raw = f"{idx:03d}_{artist} - {title}"
    return re.sub(r'[^\w\s\-]', '_', raw)[:100].strip()


def run(playlist_url: str, chosen_styles: list[str]):
    client_id     = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        sys.exit("ERROR: Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars.")

    print(f"Fetching playlist tracks…")
    tracks = get_playlist_tracks(playlist_url, client_id, client_secret)
    if not tracks:
        sys.exit("No tracks found in playlist.")

    print(f"Found {len(tracks)} tracks  |  styles: {chosen_styles}\n")

    pid = re.search(r"playlist/([A-Za-z0-9]+)", playlist_url)
    folder_name = pid.group(1) if pid else "playlist"
    out_dir = Path("output") / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)

    cover_cache: dict[str, bytes] = {}

    for idx, track in enumerate(tracks, start=1):
        label = f"[{idx:>3}/{len(tracks)}]  {track['artist']} — {track['title']}"
        print(label)

        cover_url = track["cover_url"]
        if cover_url not in cover_cache:
            try:
                cover_cache[cover_url] = download_cover(cover_url)
            except Exception as exc:
                print(f"          ⚠ cover download failed: {exc}")
                continue

        cover_bytes = cover_cache[cover_url]
        cover_img   = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
        colors      = _extract_dominant_colors(cover_img)

        for style in chosen_styles:
            theme, bg_fn = STYLE_MAP[style]
            bg = bg_fn(cover_img, colors)
            data = _render(bg, cover_img, track, theme)

            suffix = f"_{style}" if len(chosen_styles) > 1 else ""
            fname  = _safe_name(track["title"], track["artist"], idx) + suffix + ".jpg"
            (out_dir / fname).write_bytes(data)

        time.sleep(0.3)  # stay polite to the API

    total = len(tracks) * len(chosen_styles)
    print(f"\nDone!  {total} image(s) saved to  {out_dir.resolve()}/")
    return out_dir


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]

    style_arg = "gradient"
    if "--style" in sys.argv:
        i = sys.argv.index("--style")
        style_arg = sys.argv[i + 1] if i + 1 < len(sys.argv) else "gradient"

    if style_arg == "all":
        styles = ["dark", "light", "blur", "gradient"]
    elif style_arg in STYLE_MAP:
        styles = [style_arg]
    else:
        sys.exit(f"Unknown style '{style_arg}'. Choose: dark light blur gradient all")

    run(url, styles)
