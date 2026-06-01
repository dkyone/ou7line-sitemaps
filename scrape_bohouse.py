#!/usr/bin/env python3
"""
Scraper for bo-house.com -> Airtable
Extracts: title, description, bedrooms, bathrooms, guests, photos, surface area
"""

import os
import re
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from bs4 import BeautifulSoup

AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN', 'YOUR_AIRTABLE_TOKEN_HERE')
AIRTABLE_BASE = 'appdnkhejvx5bE6IV'
AIRTABLE_TABLE = 'tblT6NLcBsuveFrV3'

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
}

AIRTABLE_HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_TOKEN}',
    'Content-Type': 'application/json',
}


def http_get(url, headers=None):
    h = {**HTTP_HEADERS, **(headers or {})}
    req = urllib.request.Request(url, headers=h)
    return urllib.request.urlopen(req, timeout=30).read().decode('utf-8')


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


def scrape_page(url):
    html = http_get(url)
    soup = BeautifulSoup(html, 'lxml')
    result = {'url': url, 'photos': []}

    # --- Title (h1) ---
    h1 = soup.find('h1')
    result['title'] = h1.text.strip() if h1 else ''

    # --- Description ---
    desc_el = soup.find(class_='desktop-description')
    result['description'] = desc_el.text.strip() if desc_el else ''

    # --- Guests (property-resume div) ---
    resume = soup.find(class_='property-resume')
    guests = 0
    if resume:
        m = re.search(r'(\d+)\s+voyageurs?', resume.text, re.I)
        if m:
            guests = int(m.group(1))
    result['guests'] = guests

    # --- Features: bedrooms, bathrooms, surface ---
    bedrooms = bathrooms = surface_m2 = 0
    for item in soup.find_all(class_='features-list_item'):
        text = item.text.strip()
        m = re.match(r'(\d+)\s+chambres?', text, re.I)
        if m:
            bedrooms = int(m.group(1))
        m = re.match(r'(\d+)\s+salles?\s+de\s+bains?', text, re.I)
        if m:
            bathrooms = int(m.group(1))
        m = re.match(r'([\d\s]+)\s*m²\s+de\s+surface', text, re.I)
        if m:
            surface_m2 = int(m.group(1).replace(' ', ''))
    result['bedrooms'] = bedrooms
    result['bathrooms'] = bathrooms
    result['surface_m2'] = surface_m2 if surface_m2 else None

    # --- Photos: villa-specific from bh2.imgix.net ---
    # Extract villa path from og:image
    og = soup.find('meta', property='og:image')
    villa_path = ''
    if og:
        m = re.search(r'bh2\.imgix\.net/([A-Za-z0-9]+)/', og.get('content', ''))
        if m:
            villa_path = m.group(1)

    if villa_path:
        seen = set()
        for m in re.finditer(r'bh2\.imgix\.net/' + re.escape(villa_path) + r'/([A-Za-z0-9]+\.jpeg)', html):
            filename = m.group(1)
            if filename not in seen:
                seen.add(filename)
                result['photos'].append(
                    f'https://bh2.imgix.net/{villa_path}/{filename}?auto=format&q=85&w=1920'
                )

    result['villa_path'] = villa_path
    return result


def main():
    print('Fetching Airtable records...')
    records = get_all_records()

    to_process = []
    for r in records:
        notes = r['fields'].get('Notes', '')
        url = extract_source_url(notes)
        has_gallery = bool(r['fields'].get('Gallery'))
        if url:
            to_process.append({
                'id': r['id'],
                'name': r['fields'].get('Villa Name', ''),
                'url': url,
                'has_gallery': has_gallery,
            })

    print(f'Found {len(to_process)} records with bo-house.com URLs')
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
            if data['guests']:
                fields['Guests max'] = data['guests']
            if data['bathrooms']:
                fields['Bathrooms'] = data['bathrooms']
            if data['surface_m2']:
                fields['Total Area m²'] = data['surface_m2']

            # Photos: only add if villa doesn't have gallery yet
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

            results.append({'name': item['name'], 'url': item['url'], 'data': {
                k: v for k, v in data.items() if k != 'photos'
            }, 'photo_count': len(data['photos'])})
            time.sleep(1)

        except Exception as e:
            print(f'  ❌ ERROR: {e}')
            results.append({'name': item['name'], 'url': item['url'], 'error': str(e)})
            time.sleep(2)
        print()

    with open('/home/user/ou7line-sitemaps/scrape_bohouse_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nDone! Results saved to scrape_bohouse_results.json')
    print(f'Processed: {len([r for r in results if "data" in r])}/{len(to_process)}')
    print(f'Errors: {len([r for r in results if "error" in r])}')


if __name__ == '__main__':
    main()
