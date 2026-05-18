from __future__ import annotations

import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from renderer import generate_all_styles
from spotify_client import download_cover, get_track_info

load_dotenv()

app = FastAPI(title="Spotify Player Image Tool")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class GenerateRequest(BaseModel):
    url: str


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/generate")
async def generate(req: GenerateRequest):
    client_id     = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=503,
            detail="SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are not configured.",
        )

    try:
        track = get_track_info(req.url, client_id, client_secret)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Spotify API error: {exc}") from exc

    try:
        cover_bytes = download_cover(track["cover_url"])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Cover download failed: {exc}") from exc

    images = generate_all_styles(track, cover_bytes)

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
async def download(style: str, url: str):
    """Direct download endpoint — ?url=<spotify_url>&style=dark|light|blur|gradient"""
    client_id     = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="Spotify credentials not configured.")

    if style not in ("dark", "light", "blur", "gradient"):
        raise HTTPException(status_code=400, detail="style must be dark | light | blur | gradient")

    try:
        track       = get_track_info(url, client_id, client_secret)
        cover_bytes = download_cover(track["cover_url"])
        images      = generate_all_styles(track, cover_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in track["title"])[:60]
    filename   = f"{safe_title}_{style}.jpg"

    return Response(
        content=images[style],
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
