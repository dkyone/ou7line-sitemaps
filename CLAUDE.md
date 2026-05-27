# Project Notes for Claude

## Spotify Player Image Tool

### Generating images for a playlist URL

When the user shares a Spotify playlist URL, immediately generate all images without any OAuth discussion or workarounds explanation. Use this approach every time:

1. **Extract track IDs from the embed page** (bypasses the 403 on `/playlists/{id}/tracks`):
   ```python
   import requests, re, json
   embed_html = requests.get(
       f'https://open.spotify.com/embed/playlist/{pid}',
       headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
       timeout=15
   ).text
   scripts = re.findall(r'<script[^>]*>(.*?)</script>', embed_html, re.DOTALL)
   track_list = json.loads(scripts[14])['props']['pageProps']['state']['data']['entity']['trackList']
   track_ids = [t['uri'].split(':')[-1] for t in track_list]
   ```

2. **Fetch each track individually** via Client Credentials (works fine):
   ```python
   from spotify_client import get_track_info, download_cover
   track = get_track_info(f'https://open.spotify.com/track/{tid}', cid, cs)
   ```

3. **Generate all 12 images per track** (h/v/s × dark/light/blur/gradient) and send to user.

### Why this works
- `/playlists/{id}/tracks` → 403 with Client Credentials (Spotify restriction since 2023)
- `/playlists/{id}` → 200 but returns 0 items (also restricted)
- Embed page (`open.spotify.com/embed/playlist/{id}`) → 200, contains track URIs in `scripts[14]`
- `/tracks/{id}` individually → 200 with Client Credentials ✓

### Working directory
`/home/user/ou7line-sitemaps/spotify_player_tool/`

### Credentials
Loaded from `.env` via `python-dotenv`. Never commit `.env`.
