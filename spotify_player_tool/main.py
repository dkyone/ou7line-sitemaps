from __future__ import annotations

import base64
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from renderer import generate_all_styles, generate_vertical_styles
from spotify_client import download_cover, get_track_info

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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
            logger.info(f"Generated {len(images)} vertical image styles")
        else:
            images = generate_all_styles(track, cover_bytes)
            logger.info(f"Generated {len(images)} horizontal image styles")
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
