#!/bin/bash

# Spotify Player Image Tool - Batch Playlist Processor

set -e

if [ $# -lt 1 ]; then
    echo "🎵 Spotify Batch Playlist Processor"
    echo "────────────────────────────────────"
    echo ""
    echo "Usage:"
    echo "  ./batch.sh <spotify_playlist_url> [style]"
    echo ""
    echo "Styles:"
    echo "  dark     - Dark background"
    echo "  light    - Light background"
    echo "  blur     - Blurred album art background"
    echo "  gradient - Gradient from album colors"
    echo "  all      - All styles (default)"
    echo ""
    echo "Examples:"
    echo "  ./batch.sh https://open.spotify.com/playlist/37i9dQZF1DX... all"
    echo "  ./batch.sh https://open.spotify.com/playlist/37i9dQZF1DX... dark"
    exit 1
fi

# Load environment
if [ ! -f .env ]; then
    echo "❌ .env file not found! Create it with your Spotify credentials."
    exit 1
fi

set -a
source .env
set +a

if [ -z "$SPOTIFY_CLIENT_ID" ] || [ -z "$SPOTIFY_CLIENT_SECRET" ]; then
    echo "❌ Spotify credentials not configured in .env"
    exit 1
fi

PLAYLIST_URL="$1"
STYLE="${2:-all}"

echo "🎵 Spotify Batch Playlist Processor"
echo "────────────────────────────────────"
echo ""
echo "Playlist URL: $PLAYLIST_URL"
echo "Style:        $STYLE"
echo ""
echo "Processing..."
echo ""

python batch_playlist.py "$PLAYLIST_URL" --style "$STYLE"
