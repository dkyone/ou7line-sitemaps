#!/usr/bin/env python3
"""
Scraper for michaelzingraf.com -> Airtable
Extracts structured data from the ProductJs.initFavorite() JSON embedded in the page.
"""

import os
import re
import json
import time
import urllib.request
import urllib.parse

AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN', 'YOUR_AIRTABLE_TOKEN_HERE')
AIRTABLE_BASE = 'appdnkhejvx5bE6IV'
AIRTABLE_TABLE = 'tblT6NLcBsuveFrV3'

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

AIRTABLE_HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_TOKEN}',
    'Content-Type': 'application/json',
}


def http_get(url):
    req = urllib.request.Request(url, headers=HTTP_HEADERS)
    return urllib.request.urlopen(req, timeout=20).read().decode('utf-8')


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
    m = re.search(r'Source:\s*(https?://(?:www\.)?michaelzingraf\.com\S+)', notes)
    return m.group(1).strip() if m else None


def extract_json_payload(html, fn_name):
    """Extract the first argument object from a JS function call like fn_name({...})."""
    marker = f'{fn_name}('
    idx = html.find(marker)
    if idx == -1:
        return None
    start = idx + len(marker)
    depth = 0
    for i, ch in enumerate(html[start:]):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[start:start + i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def scrape_page(url):
    html = http_get(url)
    result = {'url': url, 'photos': []}

    data = extract_json_payload(html, 'ProductJs.initFavorite')
    if not data:
        raise ValueError('Could not find ProductJs.initFavorite() in page')

    result['title'] = (data.get('translate') or {}).get('title', '')
    result['description'] = (data.get('translate') or {}).get('comment', '').replace('\r\n', '\n').strip()
    result['bedrooms'] = int(data.get('bedrooms') or 0)
    result['surface_m2'] = int(data.get('surface_totale') or 0) or None

    # Bathrooms: try to parse from description text
    m = re.search(r'(\d+)\s+(?:bathroom|salle de bain|bath)', result['description'], re.I)
    result['bathrooms'] = int(m.group(1)) if m else 0

    # Photos: sorted by rank, use apimo CDN URLs (already full-res)
    images = sorted(data.get('images') or [], key=lambda x: x.get('rank', 999))
    result['photos'] = [img['url'] for img in images if img.get('url')]
    # Fallback to michaelzingraf.com mirror
    if not result['photos']:
        result['photos'] = [
            f"https://www.michaelzingraf.com/storage/properties/{img['filename']}"
            for img in images if img.get('filename')
        ]

    return result


def main():
    print('Fetching Airtable records...')
    records = get_all_records()

    seen_urls = set()
    to_process = []
    for r in records:
        notes = r['fields'].get('Notes', '')
        url = extract_source_url(notes)
        if not url:
            continue
        if url in seen_urls:
            print(f'  Skipping duplicate URL: {url}')
            continue
        seen_urls.add(url)
        has_gallery = bool(r['fields'].get('Gallery'))
        to_process.append({
            'id': r['id'],
            'name': r['fields'].get('Villa Name', ''),
            'url': url,
            'has_gallery': has_gallery,
        })

    print(f'Found {len(to_process)} unique records with michaelzingraf.com URLs')
    print()

    results = []
    for i, item in enumerate(to_process):
        print(f'[{i+1}/{len(to_process)}] {item["name"]}')
        try:
            data = scrape_page(item['url'])

            fields = {}
            if data['description']:
                fields['Description'] = data['description']
            if data['bedrooms']:
                fields['Bedrooms'] = data['bedrooms']
            if data['bathrooms']:
                fields['Bathrooms'] = data['bathrooms']
            if data['surface_m2']:
                fields['Total Area m²'] = data['surface_m2']

            if data['photos'] and not item['has_gallery']:
                fields['Gallery'] = [{'url': u} for u in data['photos']]
                print(f'  -> {len(data["photos"])} photos')

            print(f'  -> {data["bedrooms"]} BR / {data["bathrooms"]} BA')
            print(f'  -> Surface: {data["surface_m2"]} m²')
            print(f'  -> Description: {data["description"][:80]}...' if data['description'] else '  -> No description')

            if fields:
                airtable_patch(item['id'], fields)
                print(f'  ✅ Updated {len(fields)} fields')
            else:
                print(f'  ⚠️  No data to update')

            results.append({'name': item['name'], 'url': item['url'],
                            'bedrooms': data['bedrooms'], 'bathrooms': data['bathrooms'],
                            'surface_m2': data['surface_m2'], 'photo_count': len(data['photos'])})
            time.sleep(1)

        except Exception as e:
            print(f'  ❌ ERROR: {e}')
            results.append({'name': item['name'], 'url': item['url'], 'error': str(e)})
            time.sleep(2)
        print()

    with open('/home/user/ou7line-sitemaps/scrape_michaelzingraf_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nDone! Results saved to scrape_michaelzingraf_results.json')
    print(f'Processed: {len([r for r in results if "bedrooms" in r])}/{len(to_process)}')
    print(f'Errors: {len([r for r in results if "error" in r])}')


if __name__ == '__main__':
    main()
