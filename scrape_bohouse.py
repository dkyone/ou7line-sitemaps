#!/usr/bin/env python3
"""
Scraper for bo-house.com -> Airtable
Photos: download from imgix (signed URL) -> upload to Cloudinary -> store in Gallery
SSL verification disabled for bo-house.com (cert issue in this environment)
"""

import os
import re
import json
import time
import ssl
import urllib.request
import urllib.parse
import urllib.error
from bs4 import BeautifulSoup

AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN', 'YOUR_AIRTABLE_TOKEN_HERE')
AIRTABLE_BASE = 'appdnkhejvx5bE6IV'
AIRTABLE_TABLE = 'tblT6NLcBsuveFrV3'
CLOUDINARY_CLOUD = os.environ.get('CLOUDINARY_CLOUD', 'dmnly140t')
CLOUDINARY_PRESET = 'maison-maysky'

# SSL context that skips certificate verification (for bo-house.com)
NO_VERIFY_CTX = ssl.create_default_context()
NO_VERIFY_CTX.check_hostname = False
NO_VERIFY_CTX.verify_mode = ssl.CERT_NONE

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
}

AIRTABLE_HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_TOKEN}',
    'Content-Type': 'application/json',
}


def http_get_nossl(url, extra_headers=None):
    h = {**HTTP_HEADERS, **(extra_headers or {})}
    req = urllib.request.Request(url, headers=h)
    return urllib.request.urlopen(req, timeout=30, context=NO_VERIFY_CTX).read()


def download_image(url):
    """Download image bytes from imgix with bo-house Referer."""
    req = urllib.request.Request(url, headers={
        'User-Agent': HTTP_HEADERS['User-Agent'],
        'Referer': 'https://bo-house.com/',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    })
    return urllib.request.urlopen(req, timeout=30).read()


def upload_to_cloudinary(img_bytes):
    """Upload image bytes to Cloudinary via multipart, return delivery URL."""
    boundary = 'CloudinaryBoundary1234'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="upload_preset"\r\n\r\n'
        f'{CLOUDINARY_PRESET}\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="photo.jpg"\r\n'
        f'Content-Type: image/jpeg\r\n\r\n'
    ).encode('utf-8') + img_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

    req = urllib.request.Request(
        f'https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD}/image/upload',
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
        method='POST',
    )
    result = json.loads(urllib.request.urlopen(req, timeout=60).read().decode('utf-8'))
    if not result.get('public_id'):
        raise ValueError(f'Cloudinary error: {result}')
    return f'https://res.cloudinary.com/{CLOUDINARY_CLOUD}/image/upload/q_auto,f_auto/{result["public_id"]}'


def airtable_patch(record_id, fields):
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}/{record_id}'
    data = json.dumps({'fields': fields}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=AIRTABLE_HEADERS, method='PATCH')
    return json.loads(urllib.request.urlopen(req, timeout=15).read().decode('utf-8'))


def get_all_records():
    records, offset = [], None
    while True:
        params = [('fields[]', 'Villa Name'), ('fields[]', 'Notes'), ('fields[]', 'Gallery')]
        if offset:
            params.append(('offset', offset))
        url = f'https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=AIRTABLE_HEADERS)
        data = json.loads(urllib.request.urlopen(req, timeout=15).read().decode('utf-8'))
        records += data.get('records', [])
        offset = data.get('offset')
        if not offset:
            break
    return records


def extract_source_url(notes):
    if not notes:
        return None
    m = re.search(r'Source:\s*(https://bo-house\.com\S+)', notes)
    return m.group(1).strip() if m else None


def scrape_photos(url):
    """Scrape villa page (SSL-bypass) and return list of exact signed imgix URLs."""
    html = http_get_nossl(url).decode('utf-8')
    soup = BeautifulSoup(html, 'lxml')

    from collections import Counter
    paths = re.findall(r'bh2\.imgix\.net/([A-Za-z0-9]+)/', html)
    villa_path = Counter(paths).most_common(1)[0][0] if paths else ''

    if not villa_path:
        return []

    seen_bases = set()
    photos = []
    # Match full signed URL from the page HTML
    pattern = r'(https://bh2[.]imgix[.]net/' + re.escape(villa_path) + r'/[A-Za-z0-9]+[.]jpeg[?][^\s"\']+)'
    for m in re.finditer(pattern, html):
        full_url = m.group(1)
        base = full_url.split('?')[0]
        if base not in seen_bases:
            seen_bases.add(base)
            photos.append(full_url)

    return photos


def main():
    print('Fetching Airtable records...')
    records = get_all_records()

    to_process = []
    for r in records:
        notes = r['fields'].get('Notes', '')
        url = extract_source_url(notes)
        has_gallery = bool(r['fields'].get('Gallery'))
        if url and not has_gallery:
            to_process.append({
                'id': r['id'],
                'name': r['fields'].get('Villa Name', ''),
                'url': url,
            })

    print(f'Found {len(to_process)} bo-house villas without gallery')
    print()

    results = []
    for i, item in enumerate(to_process):
        print(f'[{i+1}/{len(to_process)}] {item["name"]}')
        try:
            signed_urls = scrape_photos(item['url'])
            if not signed_urls:
                print(f'  ⚠️  No photos found on page')
                results.append({'name': item['name'], 'error': 'no photos'})
                continue

            print(f'  -> Found {len(signed_urls)} signed imgix URLs')

            cloud_urls = []
            for j, img_url in enumerate(signed_urls):
                try:
                    img_bytes = download_image(img_url)
                    cloud_url = upload_to_cloudinary(img_bytes)
                    cloud_urls.append({'url': cloud_url})
                    print(f'  -> [{j+1}/{len(signed_urls)}] uploaded ✓', end='\r')
                    time.sleep(0.3)
                except Exception as e:
                    print(f'\n  ⚠️  Photo {j+1} failed: {e}')

            print()
            if cloud_urls:
                airtable_patch(item['id'], {'Gallery': cloud_urls})
                print(f'  ✅ Gallery: {len(cloud_urls)}/{len(signed_urls)} photos saved')
                results.append({'name': item['name'], 'url': item['url'],
                                'uploaded': len(cloud_urls), 'total': len(signed_urls)})
            else:
                print(f'  ❌ All photos failed')
                results.append({'name': item['name'], 'error': 'all photos failed'})

            time.sleep(1)

        except Exception as e:
            print(f'  ❌ ERROR: {e}')
            results.append({'name': item['name'], 'url': item['url'], 'error': str(e)})
            time.sleep(2)
        print()

    with open('/home/user/ou7line-sitemaps/scrape_bohouse_photos_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nDone!')
    print(f'OK: {len([r for r in results if "uploaded" in r])}/{len(to_process)}')
    print(f'Errors: {len([r for r in results if "error" in r])}')


if __name__ == '__main__':
    main()
