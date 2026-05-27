"""
Run this script on your LOCAL machine (not on the server).

Usage:
    python3 generate_playlist_local.py <playlist_url> [output_dir]

It will:
  1. Open Spotify login in your browser
  2. Catch the OAuth callback automatically on localhost:8888
  3. Fetch all playlist tracks
  4. Generate horizontal / vertical / square × dark / light / blur / gradient
  5. Save everything to output_dir (default: ./playlist_output)

Requirements (install once):
    pip install requests pillow python-dotenv

Setup (one-time):
  In your Spotify Developer Dashboard (https://developer.spotify.com/dashboard),
  open your app and add http://localhost:8888/callback to Redirect URIs.
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import threading
import webbrowser
from base64 import b64encode
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

# ── Config ────────────────────────────────────────────────────────────────────
CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID",     "44a6b0584c2d425d8d4ddae826a8edca")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "38943d781f1447379210a2f5d64f3e5e")
REDIRECT_URI  = "http://localhost:8888/callback"
PORT          = 8888


# ── OAuth ─────────────────────────────────────────────────────────────────────
_auth_code: list[str] = []

class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        code = qs.get("code", [None])[0]
        if code:
            _auth_code.append(code)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorization successful! You can close this tab.</h2>")
        else:
            self.send_response(400); self.end_headers()
    def log_message(self, *_): pass


def _get_access_token() -> str:
    state = secrets.token_urlsafe(10)
    params = urlencode({
        "client_id":     CLIENT_ID,
        "response_type": "code",
        "redirect_uri":  REDIRECT_URI,
        "scope":         "playlist-read-private playlist-read-collaborative",
        "state":         state,
    })
    auth_url = f"https://accounts.spotify.com/authorize?{params}"

    server = HTTPServer(("localhost", PORT), _Handler)
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()

    print(f"\nOpening browser for Spotify login…\n{auth_url}\n")
    webbrowser.open(auth_url)
    print("Waiting for authorization (authorize in the browser)…")
    while not _auth_code:
        pass
    server.shutdown()
    code = _auth_code[0]

    creds = b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {creds}"},
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


# ── Spotify ───────────────────────────────────────────────────────────────────
def _fetch_playlist(playlist_url: str, token: str) -> list[dict]:
    import re
    m = re.search(r"playlist/([A-Za-z0-9]+)", playlist_url)
    if not m:
        sys.exit("Cannot parse playlist URL")
    pid = m.group(1)

    headers  = {"Authorization": f"Bearer {token}"}
    tracks, endpoint = [], f"https://api.spotify.com/v1/playlists/{pid}/tracks?limit=100"
    while endpoint:
        page = requests.get(endpoint, headers=headers, timeout=15).json()
        for item in page.get("items", []):
            t = item.get("track")
            if not t or not t.get("name"): continue
            imgs = t.get("album", {}).get("images", [])
            if not imgs: continue
            tracks.append({
                "title":       t["name"],
                "artist":      ", ".join(a["name"] for a in t.get("artists", [])),
                "album":       t.get("album", {}).get("name", ""),
                "duration_ms": t.get("duration_ms", 180_000),
                "cover_url":   imgs[0]["url"],
            })
        endpoint = page.get("next")
    return tracks


# ── Renderer (inline, no server dependency) ───────────────────────────────────
def _generate(track: dict, cover_bytes: bytes, out_dir: Path):
    # Import renderer from the same directory
    sys.path.insert(0, str(Path(__file__).parent))
    from renderer import generate_all_styles, generate_vertical_styles, generate_square_styles

    cover_bytes_dl = requests.get(track["cover_url"], timeout=15).content
    safe = "".join(c if c.isalnum() or c in " -" else "_" for c in track["title"])[:40].strip()
    folder = out_dir / safe
    folder.mkdir(parents=True, exist_ok=True)

    for prefix, fn in [
        ("h", generate_all_styles),
        ("v", generate_vertical_styles),
        ("s", generate_square_styles),
    ]:
        for style, data in fn(track, cover_bytes_dl).items():
            (folder / f"{prefix}_{style}.jpg").write_bytes(data)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 generate_playlist_local.py <playlist_url> [output_dir]")

    playlist_url = sys.argv[1]
    out_dir      = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("playlist_output")
    out_dir.mkdir(exist_ok=True)

    print("Step 1: Authorizing with Spotify…")
    token = _get_access_token()
    print("✓ Authorized\n")

    print("Step 2: Fetching playlist tracks…")
    tracks = _fetch_playlist(playlist_url, token)
    print(f"✓ Found {len(tracks)} tracks\n")

    for i, track in enumerate(tracks, 1):
        print(f"[{i}/{len(tracks)}] {track['title']} — {track['artist']}")
        _generate(track, b"", out_dir)

    print(f"\n✓ Done! Images saved to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
