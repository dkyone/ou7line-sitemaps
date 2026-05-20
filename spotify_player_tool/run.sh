#!/bin/bash

# Spotify Player Image Tool - Development Server

set -e

echo "🎵 Spotify Player Image Tool"
echo "────────────────────────────────"

# Check .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and fill in your Spotify credentials:"
    echo "  cp .env.example .env"
    echo ""
    echo "Get your credentials at: https://developer.spotify.com/dashboard"
    exit 1
fi

# Load environment
set -a
source .env
set +a

# Check credentials
if [ -z "$SPOTIFY_CLIENT_ID" ] || [ -z "$SPOTIFY_CLIENT_SECRET" ]; then
    echo "❌ Spotify credentials not configured in .env"
    exit 1
fi

echo "✅ Configuration loaded"
echo ""
echo "🚀 Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
