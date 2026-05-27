"""Tests for image renderer."""

from PIL import Image

from renderer import (
    _extract_dominant_colors,
    _truncate,
    _rounded_art,
)
import io

from PIL import ImageDraw


class TestExtractDominantColors:
    """Test color extraction from images."""

    def test_extract_from_simple_image(self):
        """Test extracting colors from a simple colored image."""
        # Create a simple test image with a few colors
        img = Image.new("RGB", (80, 80), color=(255, 0, 0))  # Red image
        colors = _extract_dominant_colors(img)

        assert len(colors) <= 3
        assert all(isinstance(c, tuple) and len(c) == 3 for c in colors)

    def test_extract_returns_list_of_tuples(self):
        """Test that extraction returns list of RGB tuples."""
        img = Image.new("RGB", (100, 100), color=(100, 150, 200))
        colors = _extract_dominant_colors(img)

        assert isinstance(colors, list)
        assert len(colors) > 0
        assert all(len(c) == 3 for c in colors)


class TestTruncate:
    """Test text truncation."""

    def test_short_text_unchanged(self):
        """Test short text is unchanged."""
        img = Image.new("RGB", (200, 50))
        draw = ImageDraw.Draw(img)

        from renderer import _font
        font = _font(24)

        result = _truncate(draw, "Hello", font, 200)
        assert result == "Hello"

    def test_long_text_truncated(self):
        """Test long text gets truncated with ellipsis."""
        img = Image.new("RGB", (200, 50))
        draw = ImageDraw.Draw(img)

        from renderer import _font
        font = _font(24)

        result = _truncate(draw, "This is a very long text", font, 50)
        assert result.endswith("…")
        assert len(result) < len("This is a very long text")


class TestRoundedArt:
    """Test album art rounding."""

    def test_rounded_art_size(self):
        """Test rounded art has correct size."""
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        result = _rounded_art(img, 200, 20)

        assert result.size == (200, 200)

    def test_rounded_art_has_alpha(self):
        """Test rounded art has alpha channel."""
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        result = _rounded_art(img, 200, 20)

        assert result.mode == "RGBA"
