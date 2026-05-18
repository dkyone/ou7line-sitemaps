from __future__ import annotations

import re
from base64 import b64encode

import requests

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE  = "https://api.spotify.com/v1"


def _token(client_id: str, client_secret: str) -> str:
    creds = b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        SPOTIFY_TOKEN_URL,
        headers={"Authorization": f"Basic {creds}"},
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _parse_url(url: str) -> tuple[str, str]:
    """Return (type, id) where type is 'track' or 'album'."""
    for pattern in [
        r"spotify\.com/(track|album)/([A-Za-z0-9]+)",
        r"spotify:(track|album):([A-Za-z0-9]+)",
    ]:
        m = re.search(pattern, url)
        if m:
            return m.group(1), m.group(2)
    raise ValueError(f"Cannot parse Spotify URL: {url!r}")


def get_track_info(url: str, client_id: str, client_secret: str) -> dict:
    kind, sid = _parse_url(url)
    token = _token(client_id, client_secret)
    headers = {"Authorization": f"Bearer {token}"}

    if kind == "track":
        data = requests.get(
            f"{SPOTIFY_API_BASE}/tracks/{sid}", headers=headers, timeout=10
        ).json()
        return {
            "title":       data["name"],
            "artist":      ", ".join(a["name"] for a in data["artists"]),
            "album":       data["album"]["name"],
            "duration_ms": data["duration_ms"],
            "cover_url":   data["album"]["images"][0]["url"],
        }

    if kind == "album":
        data = requests.get(
            f"{SPOTIFY_API_BASE}/albums/{sid}", headers=headers, timeout=10
        ).json()
        first_track = data["tracks"]["items"][0] if data["tracks"]["items"] else {}
        return {
            "title":       data["name"],
            "artist":      ", ".join(a["name"] for a in data["artists"]),
            "album":       data["name"],
            "duration_ms": first_track.get("duration_ms", 180_000),
            "cover_url":   data["images"][0]["url"],
        }

    raise ValueError(f"Unsupported Spotify resource type: {kind!r}")


def download_cover(url: str) -> bytes:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.content
