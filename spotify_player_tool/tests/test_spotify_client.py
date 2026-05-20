"""Tests for Spotify client utilities."""

import pytest

from spotify_client import _parse_url


class TestParseUrl:
    """Test Spotify URL parsing."""

    def test_parse_track_url(self):
        """Test parsing track URLs."""
        url = "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"
        kind, sid = _parse_url(url)
        assert kind == "track"
        assert sid == "3n3Ppam7vgaVa1iaRUc9Lp"

    def test_parse_album_url(self):
        """Test parsing album URLs."""
        url = "https://open.spotify.com/album/4VqSWnL3KL0u1vHx6q1D6T"
        kind, sid = _parse_url(url)
        assert kind == "album"
        assert sid == "4VqSWnL3KL0u1vHx6q1D6T"

    def test_parse_playlist_url(self):
        """Test parsing playlist URLs."""
        url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
        kind, sid = _parse_url(url)
        assert kind == "playlist"
        assert sid == "37i9dQZF1DXcBWIGoYBM5M"

    def test_parse_spotify_uri(self):
        """Test parsing Spotify URIs."""
        url = "spotify:track:3n3Ppam7vgaVa1iaRUc9Lp"
        kind, sid = _parse_url(url)
        assert kind == "track"
        assert sid == "3n3Ppam7vgaVa1iaRUc9Lp"

    def test_parse_invalid_url(self):
        """Test parsing invalid URL raises error."""
        with pytest.raises(ValueError):
            _parse_url("https://google.com")

    def test_parse_invalid_url_empty(self):
        """Test parsing empty URL raises error."""
        with pytest.raises(ValueError):
            _parse_url("")
