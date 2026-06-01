#!/usr/bin/env python3
"""
Scraper for residences-immobilier.com -> Airtable
Extracts: title, description, bedrooms, bathrooms, guests, photos, surface area
"""

import re
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from bs4 import BeautifulSoup

AIRTABLE_TOKEN = 'YOUR_AIRTABLE_TOKEN_HERE'  # Set via env: export AIRTABLE_TOKEN=pat...
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
    return urllib.request.urlopen(req, timeout=20).read().decode('utf-8')


def airtable_get(endpoint, params=None):
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}'
    if endpoint:
        url += f'/{endpoint}'
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=AIRTABLE_HEADERS)
    return json.loads(urllib.request.urlopen(req, timeout=15).read().decode('utf-8'))


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
    m = re.search(r'Source:\s*(https://www\.residences-immobilier\.com\S+)', notes)
    return m.group(1).strip() if m else None


def scrape_page(url):
    html = http_get(url)
    soup = BeautifulSoup(html, 'lxml')
    result = {'url': url, 'photos': [], 'raw_html_length': len(html)}

    # --- Title (h2 inside the description row) ---
    h2 = soup.find('h2')
    result['title'] = h2.text.strip() if h2 else ''

    # --- Description (p tag after h2) ---
    if h2:
        desc_p = h2.find_next_sibling('p')
        result['description'] = desc_p.text.strip() if desc_p else ''
    else:
        result['description'] = ''

    # --- Stats: bedrooms, guests, bathrooms ---
    stats = {}
    for p in soup.find_all('p', class_='nbInfosComplementaires'):
        value = p.text.strip()
        label_el = p.find_next_sibling('p')
        if label_el:
            label = label_el.text.strip().lower()
            stats[label] = value
    result['bedrooms'] = int(stats.get('chambres', 0) or 0)
    result['guests'] = int(stats.get('personnes', 0) or 0)
    result['bathrooms'] = int(stats.get('salles de bain', 0) or 0)

    # --- Surface area from description ---
    surface_match = re.search(r'surface\s+d[\'e]+environ\s+(\d[\d\s]*)\s*m²', result['description'], re.I)
    if not surface_match:
        surface_match = re.search(r'(\d[\d\s]+)\s*m²\s+(?:habitable|de surface|de villa)', result['description'], re.I)
    result['surface_m2'] = int(surface_match.group(1).replace(' ', '')) if surface_match else None

    # --- Land area from description ---
    land_match = re.search(r'(?:parc|terrain|jardin)[^,\.]*?(\d[\d\s]*)\s*m²', result['description'], re.I)
    if not land_match:
        land_match = re.search(r'(\d[\d\s]*)\s*m².*?(?:parc|terrain)', result['description'], re.I)
    result['land_m2'] = int(land_match.group(1).replace(' ', '')) if land_match else None

    # --- Photos (js-smartPhoto links at full resolution) ---
    seen = set()
    for a in soup.find_all('a', class_='js-smartPhoto'):
        href = a.get('href', '')
        if href and href not in seen and 'medias.maisonsetappartements.fr' in href:
            # Use f1200x800 resolution
            href = re.sub(r'/f\d+x\d+/', '/f1200x800/', href)
            seen.add(href)
            result['photos'].append(href)

    # Also get from img tags in case js-smartPhoto is missing
    if not result['photos']:
        for img in soup.find_all('img', src=re.compile(r'medias\.maisonsetappartements\.fr')):
            src = img.get('src', '')
            src = re.sub(r'/f\d+x\d+/', '/f1200x800/', src)
            if src not in seen:
                seen.add(src)
                result['photos'].append(src)

    # --- Agency (from hidden input) ---
    agence_input = soup.find('input', {'name': 'agence_id'})
    result['agence_id'] = agence_input.get('value', '') if agence_input else ''

    # --- Location from URL ---
    loc_match = re.search(r'location-villa-([a-z-]+)-\d+', url)
    result['location_from_url'] = loc_match.group(1).replace('-', ' ').title() if loc_match else ''

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

    print(f'Found {len(to_process)} records with residences-immobilier.com URLs')
    print()

    results = []
    for i, item in enumerate(to_process):
        print(f'[{i+1}/{len(to_process)}] {item["name"]}')
        try:
            data = scrape_page(item['url'])

            # Build Airtable update fields
            fields = {}

            if data['description']:
                fields['Description'] = data['description']
            if data['title'] and data['title'] != item['name']:
                # Only update title if different and looks valid
                pass  # Keep existing Villa Name, title goes to Description title
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
                fields['Gallery'] = [{'url': url} for url in data['photos']]
                print(f'  -> {len(data["photos"])} photos')

            print(f'  -> {data["bedrooms"]} BR / {data["bathrooms"]} BA / {data["guests"]} guests')
            print(f'  -> Surface: {data["surface_m2"]} m²')
            print(f'  -> Description: {data["description"][:80]}...' if data['description'] else '  -> No description')

            if fields:
                airtable_patch(item['id'], fields)
                print(f'  ✅ Updated {len(fields)} fields')
            else:
                print(f'  ⚠️  No data to update')

            results.append({'name': item['name'], 'url': item['url'], 'data': data})
            time.sleep(1)  # Polite delay

        except Exception as e:
            print(f'  ❌ ERROR: {e}')
            results.append({'name': item['name'], 'url': item['url'], 'error': str(e)})
            time.sleep(2)
        print()

    # Save full results
    with open('/home/user/ou7line-sitemaps/scrape_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nDone! Results saved to scrape_results.json')
    print(f'Processed: {len([r for r in results if "data" in r])}/{len(to_process)}')
    print(f'Errors: {len([r for r in results if "error" in r])}')


if __name__ == '__main__':
    main()
