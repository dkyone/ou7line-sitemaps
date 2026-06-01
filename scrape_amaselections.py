#!/usr/bin/env python3
"""
Scraper for amaselections.com -> Airtable
Uses the public GraphQL API at api.amaselections.com/graphql
"""

import os
import re
import json
import time
import urllib.request
import urllib.parse
from html.parser import HTMLParser

AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN', 'YOUR_AIRTABLE_TOKEN_HERE')
AIRTABLE_BASE = 'appdnkhejvx5bE6IV'
AIRTABLE_TABLE = 'tblT6NLcBsuveFrV3'

AIRTABLE_HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_TOKEN}',
    'Content-Type': 'application/json',
}

GRAPHQL_URL = 'https://api.amaselections.com/graphql'
GRAPHQL_HEADERS = {
    'Content-Type': 'application/json',
    'Origin': 'https://www.amaselections.com',
    'Referer': 'https://www.amaselections.com/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
}

PROPERTY_QUERY = '''
{
  property(slug: "%s") {
    id title sub_heading description
    bedrooms bathrooms guests house_sq garden_sq
    main_image { id name url file_name }
    images { id name url file_name }
  }
}
'''


def strip_html(html_str):
    class Stripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []
        def handle_data(self, data):
            self.parts.append(data)
    s = Stripper()
    s.feed(html_str or '')
    return ' '.join(s.parts).strip()


def graphql_query(query):
    data = json.dumps({'query': query}).encode('utf-8')
    req = urllib.request.Request(GRAPHQL_URL, data=data, headers=GRAPHQL_HEADERS, method='POST')
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
    m = re.search(r'Source:\s*(https?://(?:www\.)?amaselections\.com\S+)', notes)
    return m.group(1).strip() if m else None


def slug_from_url(url):
    return url.rstrip('/').split('/')[-1]


def main():
    print('Fetching Airtable records...')
    records = get_all_records()

    to_process = []
    seen_slugs = set()
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

    print(f'Found {len(to_process)} unique records with amaselections.com URLs')
    print()

    results = []
    for i, item in enumerate(to_process):
        print(f'[{i+1}/{len(to_process)}] {item["name"]} (slug: {item["slug"]})')
        try:
            resp = graphql_query(PROPERTY_QUERY % item['slug'])
            prop = resp.get('data', {}).get('property')
            if not prop:
                print(f'  ⚠️  Not found in API (slug: {item["slug"]})')
                results.append({'name': item['name'], 'url': item['url'], 'error': 'not found'})
                continue

            fields = {}
            desc = strip_html(prop.get('description', ''))
            if desc:
                fields['Description'] = desc
            if prop.get('bedrooms'):
                fields['Bedrooms'] = prop['bedrooms']
            if prop.get('guests'):
                fields['Guests max'] = prop['guests']
            if prop.get('bathrooms'):
                fields['Bathrooms'] = int(prop['bathrooms'])
            if prop.get('house_sq'):
                fields['Total Area m²'] = prop['house_sq']

            # Build photo list: main_image first, then images
            photos = []
            if prop.get('main_image') and prop['main_image'].get('url'):
                photos.append(prop['main_image']['url'])
            for img in (prop.get('images') or []):
                if img.get('url') and img['url'] not in photos:
                    photos.append(img['url'])

            if photos and not item['has_gallery']:
                fields['Gallery'] = [{'url': u} for u in photos]
                print(f'  -> {len(photos)} photos')

            print(f'  -> {prop.get("bedrooms", 0)} BR / {prop.get("bathrooms", 0)} BA / {prop.get("guests", 0)} guests')
            print(f'  -> Surface: {prop.get("house_sq")} m²')
            print(f'  -> Description: {desc[:80]}...' if desc else '  -> No description')

            if fields:
                airtable_patch(item['id'], fields)
                print(f'  ✅ Updated {len(fields)} fields')
            else:
                print(f'  ⚠️  No data to update')

            results.append({'name': item['name'], 'url': item['url'], 'slug': item['slug'],
                            'bedrooms': prop.get('bedrooms'), 'bathrooms': prop.get('bathrooms'),
                            'guests': prop.get('guests'), 'house_sq': prop.get('house_sq'),
                            'photo_count': len(photos)})
            time.sleep(0.5)

        except Exception as e:
            print(f'  ❌ ERROR: {e}')
            results.append({'name': item['name'], 'url': item['url'], 'error': str(e)})
            time.sleep(1)
        print()

    with open('/home/user/ou7line-sitemaps/scrape_amaselections_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nDone! Results saved to scrape_amaselections_results.json')
    print(f'Processed: {len([r for r in results if "bedrooms" in r])}/{len(to_process)}')
    print(f'Errors: {len([r for r in results if "error" in r])}')


if __name__ == '__main__':
    main()
