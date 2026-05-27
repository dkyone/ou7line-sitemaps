"""
One-shot helper: prints auth URL → user pastes redirect URL back → prints tracks.
Run: python3 get_playlist_oauth.py <playlist_url>
"""
import os, sys, re, requests
from base64 import b64encode
from urllib.parse import urlencode, urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI  = "http://localhost:8888/callback"
SCOPES        = "playlist-read-private playlist-read-collaborative"

playlist_url = sys.argv[1] if len(sys.argv) > 1 else ""
m = re.search(r"playlist/([A-Za-z0-9]+)", playlist_url)
if not m:
    sys.exit("Pass a Spotify playlist URL as argument")
playlist_id = m.group(1)

# Step 1 — generate auth URL
params = urlencode({
    "client_id":     CLIENT_ID,
    "response_type": "code",
    "redirect_uri":  REDIRECT_URI,
    "scope":         SCOPES,
})
print("\n1. Open this URL in your browser and log in:\n")
print(f"   https://accounts.spotify.com/authorize?{params}\n")
print("2. After login Spotify will redirect to localhost:8888/callback?code=...")
print("   (The page won't load — that's fine.)")
print("   Paste the FULL redirect URL here:\n")
redirect = input(">>> ").strip()

# Step 2 — extract code
code = parse_qs(urlparse(redirect).query).get("code", [None])[0]
if not code:
    sys.exit("Could not find 'code' in the URL")

# Step 3 — exchange code for token
tok_resp = requests.post(
    "https://accounts.spotify.com/api/token",
    headers={"Authorization": "Basic " + b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()},
    data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI},
    timeout=10,
).json()
access_token = tok_resp.get("access_token")
if not access_token:
    sys.exit(f"Token exchange failed: {tok_resp}")

# Step 4 — fetch all tracks
headers = {"Authorization": f"Bearer {access_token}"}
tracks, endpoint = [], f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=100"
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

print(f"\nFound {len(tracks)} tracks:")
for i, t in enumerate(tracks, 1):
    print(f"  {i}. {t['title']} — {t['artist']}")

# save to file for the generator
import json
out = f"/tmp/playlist_{playlist_id}.json"
with open(out, "w") as f:
    json.dump(tracks, f, ensure_ascii=False, indent=2)
print(f"\nSaved to {out}")
