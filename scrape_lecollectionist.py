#!/usr/bin/env python3
"""
Scraper for lecollectionist.com -> Airtable
Uses public REST API at api.lecollectionist.com/api/v1/houses/{slug}
and api.lecollectionist.com/api/v1/houses/{id}/photos
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

API_BASE = 'https://api.lecollectionist.com/api/v1'
CDN_BASE = 'https://cdn.lecollectionist.com/__collectionist__/'

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
}

AIRTABLE_HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_TOKEN}',
    'Content-Type': 'application/json',
}


def api_get(path):
    req = urllib.request.Request(API_BASE + path, headers=HTTP_HEADERS)
    return json.loads(urllib.request.urlopen(req, timeout=20).read().decode('utf-8'))


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
    m = re.search(r'Source:\s*(https?://(?:www\.)?lecollectionist\.com\S+)', notes)
    return m.group(1).strip() if m else None


def slug_from_url(url):
    """Extract slug from /fr/location-luxe/{slug} or /en/luxury-rental/{slug}"""
    return url.rstrip('/').split('/')[-1]


def get_photos(house_id):
    """Fetch all photos for a house by numeric ID, paginated."""
    photos = []
    page = 1
    while True:
        resp = api_get(f'/houses/{house_id}/photos?per_page=50&page={page}')
        items = resp.get('data') or []
        for item in items:
            rel_url = (item.get('attributes') or {}).get('url', '')
            if rel_url and not (item.get('attributes') or {}).get('hidden', False):
                photos.append(CDN_BASE + rel_url)
        meta = resp.get('meta') or {}
        if page >= meta.get('last_page', 1):
            break
        page += 1
    return photos


def scrape_property(slug):
    resp = api_get(f'/houses/{slug}')
    data = resp.get('data') or {}
    attrs = data.get('attributes') or {}
    house_id = data.get('id')

    result = {
        'title': attrs.get('name', ''),
        'description': attrs.get('description', '').strip(),
        'bedrooms': int(attrs.get('bedrooms') or 0),
        'bathrooms': int(attrs.get('bathrooms') or 0),
        'guests': int(attrs.get('capacity') or 0),
        'surface_m2': int(attrs.get('surface') or 0) or None,
        'house_id': house_id,
        'photos': [],
    }

    if house_id:
        result['photos'] = get_photos(house_id)

    return result


def main():
    print('Fetching Airtable records...')
    records = get_all_records()

    seen_slugs = set()
    to_process = []
    for r in records:
        notes = r['fields'].get('Notes', '')
        url = extract_source_url(notes)
        if not url:
            continue
        slug = slug_from_url(url)
        if slug in seen_slugs:
            print(f'  Skipping duplicate slug: {slug}')
            continue
        seen_slugs.add(slug)
        has_gallery = bool(r['fields'].get('Gallery'))
        to_process.append({
            'id': r['id'],
            'name': r['fields'].get('Villa Name', ''),
            'url': url,
            'slug': slug,
            'has_gallery': has_gallery,
        })

    print(f'Found {len(to_process)} unique records with lecollectionist.com URLs')
    print()

    results = []
    for i, item in enumerate(to_process):
        print(f'[{i+1}/{len(to_process)}] {item["name"]} (slug: {item["slug"]})')
        try:
            data = scrape_property(item['slug'])

            fields = {}
            if data['description']:
                fields['Description'] = data['description']
            if data['bedrooms']:
                fields['Bedrooms'] = data['bedrooms']
            if data['guests']:
                fields['Guests max'] = data['guests']
            if data['bathrooms']:
                fields['Bathrooms'] = data['bathrooms']
            if data['surface_m2']:
                fields['Total Area m²'] = data['surface_m2']

            if data['photos'] and not item['has_gallery']:
                fields['Gallery'] = [{'url': u} for u in data['photos']]
                print(f'  -> {len(data["photos"])} photos')

            print(f'  -> {data["bedrooms"]} BR / {data["bathrooms"]} BA / {data["guests"]} guests')
            print(f'  -> Surface: {data["surface_m2"]} m²')
            print(f'  -> Description: {data["description"][:80]}...' if data['description'] else '  -> No description')

            if fields:
                airtable_patch(item['id'], fields)
                print(f'  ✅ Updated {len(fields)} fields')
            else:
                print(f'  ⚠️  No data to update')

            results.append({'name': item['name'], 'url': item['url'], 'slug': item['slug'],
                            'bedrooms': data['bedrooms'], 'bathrooms': data['bathrooms'],
                            'guests': data['guests'], 'surface_m2': data['surface_m2'],
                            'photo_count': len(data['photos'])})
            time.sleep(0.5)

        except Exception as e:
            print(f'  ❌ ERROR: {e}')
            results.append({'name': item['name'], 'url': item['url'], 'error': str(e)})
            time.sleep(1)
        print()

    with open('/home/user/ou7line-sitemaps/scrape_lecollectionist_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nDone! Results saved to scrape_lecollectionist_results.json')
    print(f'Processed: {len([r for r in results if "bedrooms" in r])}/{len(to_process)}')
    print(f'Errors: {len([r for r in results if "error" in r])}')


if __name__ == '__main__':
    main()
