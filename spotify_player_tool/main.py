from __future__ import annotations

import base64
import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlencode

import requests as _requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from renderer import generate_all_styles, generate_vertical_styles, generate_square_styles
from spotify_client import download_cover, get_track_info, get_playlist_tracks_with_token

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ── OAuth state store (in-memory, single-user) ────────────────────────────────
_oauth_state:        str | None = None
_oauth_access_token: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🎵 Spotify Player Image Tool starting up...")
    logger.info("API documentation available at: http://localhost:8000/docs")
    yield
    logger.info("Spotify Player Image Tool shutting down")


app = FastAPI(
    title="Spotify Player Image Tool",
    description="Generate Spotify player card images with album art and track info",
    version="1.0.0",
    lifespan=lifespan,
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class GenerateRequest(BaseModel):
    url: str
    format: str = "horizontal"  # "horizontal" or "vertical"


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
async def health():
    logger.debug("Health check")
    return {"ok": True}


@app.post("/generate")
async def generate(req: GenerateRequest):
    logger.info(f"Generate request for URL: {req.url}")

    client_id     = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        logger.error("Spotify credentials not configured")
        raise HTTPException(
            status_code=503,
            detail="SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are not configured.",
        )

    try:
        track = get_track_info(req.url, client_id, client_secret)
        logger.info(f"Track found: {track['title']} by {track['artist']}")
    except ValueError as exc:
        logger.warning(f"Invalid Spotify URL: {req.url}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Spotify API error: {exc}")
        raise HTTPException(status_code=502, detail=f"Spotify API error: {exc}") from exc

    try:
        cover_bytes = download_cover(track["cover_url"])
        logger.info(f"Cover downloaded: {len(cover_bytes)} bytes")
    except Exception as exc:
        logger.error(f"Cover download failed: {exc}")
        raise HTTPException(status_code=502, detail=f"Cover download failed: {exc}") from exc

    try:
        if req.format == "vertical":
            images = generate_vertical_styles(track, cover_bytes)
        elif req.format == "square":
            images = generate_square_styles(track, cover_bytes)
        else:
            images = generate_all_styles(track, cover_bytes)
        logger.info(f"Generated {len(images)} {req.format} image styles")
    except Exception as exc:
        logger.error(f"Image generation failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {exc}") from exc

    def b64(data: bytes) -> str:
        return "data:image/jpeg;base64," + base64.b64encode(data).decode()

    total_s = track["duration_ms"] // 1000
    duration_fmt = f"{total_s // 60}:{total_s % 60:02d}"

    return {
        "track": {
            "title":    track["title"],
            "artist":   track["artist"],
            "album":    track["album"],
            "duration": duration_fmt,
        },
        "images": {style: b64(data) for style, data in images.items()},
    }


@app.get("/download/{style}")
async def download(style: str, url: str, format: str = "horizontal"):
    """Direct download endpoint — ?url=<spotify_url>&style=dark|light|blur|gradient&format=horizontal|vertical"""
    logger.info(f"Download request: style={style}, format={format}, url={url}")

    client_id     = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        logger.error("Spotify credentials not configured for download")
        raise HTTPException(status_code=503, detail="Spotify credentials not configured.")

    if style not in ("dark", "light", "blur", "gradient"):
        logger.warning(f"Invalid style requested: {style}")
        raise HTTPException(status_code=400, detail="style must be dark | light | blur | gradient")

    try:
        track       = get_track_info(url, client_id, client_secret)
        cover_bytes = download_cover(track["cover_url"])

        if format == "vertical":
            images = generate_vertical_styles(track, cover_bytes)
        elif format == "square":
            images = generate_square_styles(track, cover_bytes)
        else:
            images = generate_all_styles(track, cover_bytes)

        logger.info(f"Successfully generated {format}/{style} image for: {track['title']}")
    except ValueError as exc:
        logger.warning(f"Invalid Spotify URL for download: {url}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Download generation error: {exc}")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in track["title"])[:60]
    filename   = f"{safe_title}_{style}.jpg"

    return Response(
        content=images[style],
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Spotify OAuth ─────────────────────────────────────────────────────────────

@app.get("/login")
async def login():
    """Redirect to Spotify authorization page."""
    global _oauth_state
    client_id    = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/callback")

    if not client_id:
        raise HTTPException(status_code=503, detail="SPOTIFY_CLIENT_ID not configured.")

    _oauth_state = secrets.token_urlsafe(16)
    params = urlencode({
        "client_id":     client_id,
        "response_type": "code",
        "redirect_uri":  redirect_uri,
        "scope":         "playlist-read-private playlist-read-collaborative",
        "state":         _oauth_state,
    })
    url = f"https://accounts.spotify.com/authorize?{params}"
    logger.info("Redirecting to Spotify OAuth")
    return RedirectResponse(url)


@app.get("/callback")
async def callback(code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    """Spotify OAuth callback — exchange code for access token."""
    global _oauth_state, _oauth_access_token

    if error:
        raise HTTPException(status_code=400, detail=f"Spotify auth error: {error}")
    if state != _oauth_state:
        raise HTTPException(status_code=400, detail="OAuth state mismatch.")

    client_id     = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
    redirect_uri  = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/callback")

    from base64 import b64encode as _b64
    creds = _b64(f"{client_id}:{client_secret}".encode()).decode()
    resp = _requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {creds}"},
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
        timeout=10,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Token exchange failed: {resp.text}")

    _oauth_access_token = resp.json()["access_token"]
    logger.info("OAuth token obtained successfully")
    return HTMLResponse("""
        <html><body style="font-family:sans-serif;padding:40px;background:#121212;color:#fff">
        <h2 style="color:#1ED760">✓ Авторизация успешна!</h2>
        <p>Spotify аккаунт подключён. Теперь можно генерировать плейлисты.</p>
        <p style="color:#aaa">Можно закрыть эту вкладку.</p>
        </body></html>
    """)


# ── Playlist generation ───────────────────────────────────────────────────────

class PlaylistRequest(BaseModel):
    url: str
    format: str = "all"   # "horizontal" | "vertical" | "square" | "all"


@app.post("/generate-playlist")
async def generate_playlist(req: PlaylistRequest):
    """Generate images for every track in a Spotify playlist (requires /login first)."""
    if not _oauth_access_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Visit /login to authorize with Spotify.",
        )

    logger.info(f"Playlist generate request: {req.url}")
    try:
        tracks = get_playlist_tracks_with_token(req.url, _oauth_access_token)
    except Exception as exc:
        logger.error(f"Playlist fetch error: {exc}")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not tracks:
        raise HTTPException(status_code=404, detail="Playlist is empty or inaccessible.")

    logger.info(f"Generating images for {len(tracks)} tracks")
    results = []
    for track in tracks:
        try:
            cover_bytes = download_cover(track["cover_url"])
            fns = []
            if req.format in ("horizontal", "all"):
                fns.append(("horizontal", generate_all_styles(track, cover_bytes)))
            if req.format in ("vertical", "all"):
                fns.append(("vertical",   generate_vertical_styles(track, cover_bytes)))
            if req.format in ("square", "all"):
                fns.append(("square",     generate_square_styles(track, cover_bytes)))

            def b64(d): return "data:image/jpeg;base64," + base64.b64encode(d).decode()
            images = {f"{fmt}_{s}": b64(d) for fmt, styles in fns for s, d in styles.items()}
            results.append({"title": track["title"], "artist": track["artist"], "images": images})
        except Exception as exc:
            logger.warning(f"Skipping {track['title']}: {exc}")
            results.append({"title": track["title"], "artist": track["artist"], "error": str(exc)})

    return {"total": len(tracks), "tracks": results}
