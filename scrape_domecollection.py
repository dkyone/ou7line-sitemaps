#!/usr/bin/env python3
"""
Scraper for dome-collection.com -> Airtable
Extracts: description, bedrooms, bathrooms, guests, surface area, photos
from /hebergement/{slug}/ pages (Divi WordPress theme)
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

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
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
    m = re.search(r'Source:\s*(https?://(?:www\.)?dome-collection\.com\S+)', notes)
    return m.group(1).strip() if m else None


def scrape_page(url):
    html = http_get(url)
    soup = BeautifulSoup(html, 'lxml')
    result = {'url': url, 'photos': []}

    # --- Title ---
    h1 = soup.find('h1')
    result['title'] = h1.text.strip() if h1 else ''

    # --- Description ---
    desc_block = soup.find('div', class_='et_pb_post_content_0_tb_body')
    if desc_block:
        p = desc_block.find('p')
        result['description'] = p.text.strip() if p else desc_block.text.strip()
    else:
        result['description'] = ''

    # --- Stats: guests, bedrooms, bathrooms, surface ---
    row = soup.find('div', class_='et_pb_row_1_tb_body')
    cells_text = ''
    if row:
        cells = [c.get_text(' ', strip=True) for c in row.find_all('div', class_='et_pb_text_inner')]
        cells_text = ' '.join(cells)

    m = re.search(r'(\d+)\s+voyageurs?', cells_text, re.I)
    result['guests'] = int(m.group(1)) if m else 0
    m = re.search(r'(\d+)\s+chambres?', cells_text, re.I)
    result['bedrooms'] = int(m.group(1)) if m else 0
    m = re.search(r'(\d+)\s+[Ss]alles?\s+de\s+bain', cells_text, re.I)
    result['bathrooms'] = int(m.group(1)) if m else 0
    m = re.search(r'[Ss]urface\s*[:\-]?\s*(\d+)', cells_text, re.I)
    result['surface_m2'] = int(m.group(1)) if m else None

    # --- Photos from gallery lightbox div ---
    gallery = soup.find('div', id='gallery-lightbox-2')
    if not gallery:
        # Fallback: try any gallery lightbox
        gallery = soup.find('div', id=re.compile(r'gallery-lightbox'))
    seen = set()
    if gallery:
        for img in gallery.find_all('img'):
            src = img.get('src', '')
            if 'wp-content/uploads' in src:
                # Strip thumbnail suffix -WIDTHxHEIGHT to get full-res
                full_res = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', src)
                if full_res not in seen:
                    seen.add(full_res)
                    result['photos'].append(full_res)

    # Fallback: og:image
    if not result['photos']:
        og = soup.find('meta', property='og:image')
        if og and og.get('content'):
            result['photos'].append(og['content'])

    return result


def main():
    print('Fetching Airtable records...')
    records = get_all_records()

    to_process = []
    for r in records:
        notes = r['fields'].get('Notes', '')
        url = extract_source_url(notes)
        if not url:
            continue
        has_gallery = bool(r['fields'].get('Gallery'))
        to_process.append({
            'id': r['id'],
            'name': r['fields'].get('Villa Name', ''),
            'url': url,
            'has_gallery': has_gallery,
        })

    print(f'Found {len(to_process)} records with dome-collection.com URLs')
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

            results.append({'name': item['name'], 'url': item['url'],
                            'bedrooms': data['bedrooms'], 'bathrooms': data['bathrooms'],
                            'guests': data['guests'], 'surface_m2': data['surface_m2'],
                            'photo_count': len(data['photos'])})
            time.sleep(1)

        except Exception as e:
            print(f'  ❌ ERROR: {e}')
            results.append({'name': item['name'], 'url': item['url'], 'error': str(e)})
            time.sleep(2)
        print()

    with open('/home/user/ou7line-sitemaps/scrape_domecollection_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nDone! Results saved to scrape_domecollection_results.json')
    print(f'Processed: {len([r for r in results if "bedrooms" in r])}/{len(to_process)}')
    print(f'Errors: {len([r for r in results if "error" in r])}')


if __name__ == '__main__':
    main()
