#!/usr/bin/env python3
"""
Force-add photos to villas that have exactly 1 photo.
Handles: residences-immobilier.com, lecollectionist.com, valmontriviera.com
"""

import os
import re
import json
import time
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN', 'YOUR_AIRTABLE_TOKEN_HERE')
AIRTABLE_BASE = 'appdnkhejvx5bE6IV'
AIRTABLE_TABLE = 'tblT6NLcBsuveFrV3'
API_BASE = 'https://api.lecollectionist.com/api/v1'
CDN_BASE = 'https://cdn.lecollectionist.com/__collectionist__/'

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
}

AIRTABLE_HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_TOKEN}',
    'Content-Type': 'application/json',
}


def http_get(url, extra=None):
    req = urllib.request.Request(url, headers={**HTTP_HEADERS, **(extra or {})})
    return urllib.request.urlopen(req, timeout=20).read().decode('utf-8')


def airtable_patch(record_id, fields):
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}/{record_id}'
    data = json.dumps({'fields': fields}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=AIRTABLE_HEADERS, method='PATCH')
    return json.loads(urllib.request.urlopen(req, timeout=15).read().decode('utf-8'))


# --- residences-immobilier.com ---
def photos_residences(url):
    html = http_get(url)
    soup = BeautifulSoup(html, 'lxml')
    seen = set()
    photos = []
    for a in soup.find_all('a', class_='js-smartPhoto'):
        href = a.get('href', '')
        if href and 'medias.maisonsetappartements.fr' in href:
            href = re.sub(r'/f\d+x\d+/', '/f1200x800/', href)
            if href not in seen:
                seen.add(href)
                photos.append(href)
    if not photos:
        for img in soup.find_all('img', src=re.compile(r'medias\.maisonsetappartements\.fr')):
            src = re.sub(r'/f\d+x\d+/', '/f1200x800/', img.get('src', ''))
            if src not in seen:
                seen.add(src)
                photos.append(src)
    return photos


# --- lecollectionist.com ---
def photos_lecollectionist(slug):
    api_headers = {**HTTP_HEADERS, 'Accept': 'application/json'}
    resp_data = json.loads(urllib.request.urlopen(
        urllib.request.Request(f'{API_BASE}/houses/{slug}', headers=api_headers), timeout=20
    ).read())
    house_id = (resp_data.get('data') or {}).get('id')
    if not house_id:
        return []
    photos = []
    page = 1
    while True:
        resp = json.loads(urllib.request.urlopen(
            urllib.request.Request(f'{API_BASE}/houses/{house_id}/photos?per_page=50&page={page}', headers=api_headers), timeout=20
        ).read())
        for item in resp.get('data') or []:
            rel = (item.get('attributes') or {}).get('url', '')
            if rel and not (item.get('attributes') or {}).get('hidden', False):
                photos.append(CDN_BASE + rel)
        if page >= (resp.get('meta') or {}).get('last_page', 1):
            break
        page += 1
    return photos


# --- valmontriviera.com ---
def photos_valmontriviera(url):
    html = http_get(url)
    # Extract all full-res WP photos (no thumbnail size suffix)
    all_photos = list(dict.fromkeys(
        p for p in re.findall(
            r'https?://www\.valmontriviera\.com/wp-content/uploads/[^\s"\']+\.(?:jpg|jpeg|webp)', html, re.I
        ) if not re.search(r'-\d+x\d+\.', p)
    ))
    if not all_photos:
        return []
    # Find the most frequent villa ID (4+ digits before -0 or -1 in filename)
    from collections import Counter
    ids = re.findall(r'-(\d{4,})-\d+\.(?:jpg|jpeg|webp)', ' '.join(all_photos))
    if not ids:
        return all_photos
    villa_id = Counter(ids).most_common(1)[0][0]
    villa_photos = [p for p in all_photos if f'-{villa_id}-' in p]
    return villa_photos if villa_photos else all_photos


VILLAS = [
    # residences-immobilier.com
    {'id': 'recAEAJGd1HHSlfww', 'name': 'Architect Villa Vallauris', 'source': 'residences', 'url': 'https://www.residences-immobilier.com/locations-saisonnieres/fr/detail/location-villa-vallauris-3642812.html'},
    {'id': 'recKhtjIwQXzzQrHB', 'name': 'Villa Laura Cannes', 'source': 'residences', 'url': 'https://www.residences-immobilier.com/locations-saisonnieres/fr/detail/location-villa-cannes-4143982.html'},
    {'id': 'recNIbDqLh7OA8Y26', 'name': "Contemporary Villa Cap d'Eze", 'source': 'residences', 'url': 'https://www.residences-immobilier.com/locations-saisonnieres/fr/detail/location-villa-eze-4106755.html'},
    {'id': 'recmt3eW0Xwrbq6eq', 'name': 'Contemporary 5BR Villa Cannes Californie', 'source': 'residences', 'url': 'https://www.residences-immobilier.com/locations-saisonnieres/fr/detail/location-villa-cannes-4152148.html'},
    {'id': 'reczGuirYBpDzreao', 'name': 'Domain 11BR Mougins', 'source': 'residences', 'url': 'https://www.residences-immobilier.com/locations-saisonnieres/fr/detail/location-villa-mougins-2895185.html'},
    # lecollectionist.com
    {'id': 'recoUwSN2qINYfyhF', 'name': 'Villa Dalya', 'source': 'lecollectionist', 'url': 'https://www.lecollectionist.com/fr/location-luxe/villa-dalya-mougins'},
    # valmontriviera.com
    {'id': 'rec7DJtaELRJcgo7a', 'name': 'Brand New Contemporary Villa Cap Ferrat', 'source': 'valmontriviera', 'url': 'https://www.valmontriviera.com/fr/propriete/une-villa-contemporaine-neuve-a-saint-jean-cap-ferrat'},
    {'id': 'rec83AoZdsaOrIBCl', 'name': 'Luxurious Villa Tip of Cap Ferrat', 'source': 'valmontriviera', 'url': 'https://www.valmontriviera.com/fr/propriete/luxueuse-villa-a-la-pointe-de-cap-ferrat'},
    {'id': 'recOHjbNqWhOvvBW3', 'name': 'Peaceful Villa with Sea View', 'source': 'valmontriviera', 'url': 'https://www.valmontriviera.com/fr/propriete/villa-paisible-avec-vue-sur-la-mer'},
]


def main():
    results = []
    for i, v in enumerate(VILLAS):
        print(f'[{i+1}/{len(VILLAS)}] {v["name"]} ({v["source"]})')
        try:
            if v['source'] == 'residences':
                photos = photos_residences(v['url'])
            elif v['source'] == 'lecollectionist':
                slug = v['url'].rstrip('/').split('/')[-1]
                photos = photos_lecollectionist(slug)
            elif v['source'] == 'valmontriviera':
                photos = photos_valmontriviera(v['url'])
            else:
                photos = []

            print(f'  -> {len(photos)} photos found')
            if photos:
                airtable_patch(v['id'], {'Gallery': [{'url': u} for u in photos]})
                print(f'  ✅ Gallery updated')
                results.append({'name': v['name'], 'photo_count': len(photos)})
            else:
                print(f'  ⚠️  No photos found')
                results.append({'name': v['name'], 'error': 'no photos'})

            time.sleep(1)
        except Exception as e:
            print(f'  ❌ ERROR: {e}')
            results.append({'name': v['name'], 'error': str(e)})
            time.sleep(2)
        print()

    print('Done!')
    for r in results:
        status = f'{r.get("photo_count", 0)} photos' if 'photo_count' in r else f'ERROR: {r.get("error")}'
        print(f'  {r["name"]}: {status}')


if __name__ == '__main__':
    main()
