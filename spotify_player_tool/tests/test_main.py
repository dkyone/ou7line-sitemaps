"""Tests for the Spotify Player Image Tool API."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_index():
    """Test index page loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Spotify Player Card Generator" in response.text or "<!DOCTYPE" in response.text


def test_generate_missing_credentials():
    """Test generate endpoint without Spotify credentials."""
    # This will likely fail with 503 if env vars aren't set
    response = client.post(
        "/generate",
        json={"url": "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"}
    )
    # Should be 503 (Service Unavailable) or 400 (Bad Request)
    assert response.status_code in (400, 503)


def test_generate_invalid_url():
    """Test generate endpoint with invalid URL."""
    response = client.post(
        "/generate",
        json={"url": "not-a-spotify-url"}
    )
    # Should be 400 due to validation error
    assert response.status_code in (400, 503)


def test_download_invalid_style():
    """Test download endpoint with invalid style."""
    response = client.get(
        "/download/invalid_style",
        params={"url": "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"}
    )
    # Could be 400 (invalid style) or 503 (no credentials) depending on config
    assert response.status_code in (400, 503)
    data = response.json()
    assert "detail" in data
