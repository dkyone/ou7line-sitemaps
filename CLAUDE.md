# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This repository contains XML sitemaps for the ou7line.com digital marketing agency website, which operates across three regional/language subdomains:

| File | Domain | hreflang |
|---|---|---|
| `sitemap-en.xml` | `ou7line.com` | `en` |
| `sitemap-fr.xml` | `fr.ou7line.com` | `fr` |
| `sitemap-ae.xml` | `ae.ou7line.com` | `en-AE` |

There is no build system, package manager, or test runner. All work is direct XML editing.

## Sitemap Structure and Conventions

All three files use the Sitemap Protocol with the `xhtml` namespace for hreflang alternate links:

```xml
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
```

Every `<url>` entry must include:
- `<loc>` — the canonical URL for that locale
- `<lastmod>` — date in `YYYY-MM-DD` format
- `<changefreq>weekly</changefreq>` — always `weekly`
- `<priority>` — `1.0` for the homepage, `0.8` for all other pages
- Three `<xhtml:link>` alternate tags (one per locale) plus an `x-default` tag that always points to the EN (`ou7line.com`) URL

## Critical Invariant: Cross-File Consistency

All three sitemaps must stay in sync. Every logical page must appear in all three files with matching alternate links. The hreflang block on every URL entry in every file must list all four variants:

```xml
<xhtml:link rel="alternate" hreflang="en"        href="https://ou7line.com/..."/>
<xhtml:link rel="alternate" hreflang="fr"        href="https://fr.ou7line.com/..."/>
<xhtml:link rel="alternate" hreflang="en-AE"     href="https://ae.ou7line.com/..."/>
<xhtml:link rel="alternate" hreflang="x-default" href="https://ou7line.com/..."/>
```

When adding or removing a page, the corresponding entry must be added or removed in **all three files** simultaneously, and the hreflang blocks in the existing entries of the other two files do not need to change (they already reference the full set of alternates).

## Adding a New Page

1. Add a `<url>` block to `sitemap-en.xml` with the EN slug and the matching FR and AE slugs in the `xhtml:link` alternates.
2. Add the corresponding `<url>` block to `sitemap-fr.xml` with the FR slug as `<loc>`.
3. Add the corresponding `<url>` block to `sitemap-ae.xml` with the AE slug as `<loc>`.
4. Update `<lastmod>` on all modified entries to today's date.

## Updating lastmod

When editing any URL entry, update its `<lastmod>` to the current date (`YYYY-MM-DD`). Do not bulk-update all entries unless all pages genuinely changed.

---

## Airtable — Maison Maysky Villas Database

**Base:** Maison Maysky Base — ID `appdnkhejvx5bE6IV`
**Table:** VILLAS — ID `tblT6NLcBsuveFrV3`
**Current count:** ~123 villa records

Use the Airtable MCP tools (`mcp__cc3a38fc-a210-46c4-8383-0b2a1265c671__*`) to read and write records. Never substitute human-readable names for IDs in API calls.

### Key Fields

| Field | Type | Notes |
|---|---|---|
| `Villa Name` | singleLineText | Primary display name |
| `ID` | formula | Auto-generated identifier |
| `Number` | autoNumber | Sequential number |
| `Location` | singleSelect | Town on the Riviera (see choices below) |
| `Status` | singleSelect | Available / Booked / On Hold / Off Market |
| `Featured` | checkbox | Highlighted listing |
| `Bedrooms` | number | |
| `Bathrooms` | number | |
| `Guests max` | number | |
| `Total Area m²` | number | |
| `Terrace m²` | number | |
| `Price Low Season €/week` | currency | |
| `Price High Season €/week` | currency | |
| `Price` | singleSelect | Price tier bucket |
| `Security Deposit €` | currency | |
| `Parking Spaces` | number | |
| `Year Built` | number | |
| `Year Renovated` | number | |
| `Address` | singleLineText | |
| `Google Maps URL` | url | |
| `Architectural Style` | singleSelect | e.g. Contemporary, Provençal, Belle Époque… |
| `Views` | multipleSelects | e.g. Sea, Sea Panoramic, Mountains, Hills… |
| `Exposure` | multipleSelects | Cardinal directions (North, South, South-West…) |
| `Services Included` | multipleSelects | Daily Housekeeping, Private Chef, Concierge… |
| `Events Allowed` | singleSelect | Yes / No / On Request |
| `Equipements` | multipleSelects | Interior: AC, Heating, Jacuzzi, Sauna, Wi-Fi… |
| `Building` | multipleSelects | Elevator, Wine cellar, Home cinema, Pool house… |
| `Security` | multipleSelects | Alarm, Guard, Electric gates, Video surveillance… |
| `Sport Facilities` | multipleSelects | Gym, Tennis, Spa, Golf, Helipad… |
| `Exterior Spaces` | multipleSelects | Pool, Heated pool, Infinity pool, Terrace, Garden… |
| `Title` | multilineText | EN listing title |
| `Description` | multilineText | EN listing description |
| `Title (FR)` / `Title FR` | multilineText | French translation of Title |
| `Title (RU)` / `Title RU` | multilineText | Russian translation of Title |
| `Description (FR)` / `Description FR` | multilineText | French translation |
| `Description (RU)` / `Description RU` | multilineText | Russian translation |
| `Notes` | multilineText | Internal notes |
| `Gallery` | multipleAttachments | Photos |
| `PDF EN` | multipleAttachments | `fldAuf1MJRB8CntSk` — FlexiPage staging for EN PDF (cleared after Drive upload) |
| `PDF FR` | multipleAttachments | `fld7z659DUwj8oQkk` — FlexiPage staging for FR PDF (cleared after Drive upload) |
| `PDF RU` | multipleAttachments | `fld7B6V3Q8Ea0RFMp` — FlexiPage staging for RU PDF (cleared after Drive upload) |
| `PDF Folder` | url | `fld9jNb2S7dBzkPTm` — Google Drive folder link with all 3 language PDFs |
| `▶ PDF` | checkbox | `fldSX4qaGci4XrFRa` — triggers 3-language PDF generation via Google Apps Script |
| `pdf_lock` | singleLineText | `fldN6rmI6wfAPFKvh` — distributed lock, do not write manually |

**Multilingual text fields (auto-translated by Google Apps Script):**

| Field | Type | Notes |
|---|---|---|
| `Title (FR)` | multilineText | `fldmXJtyKQCmPtoL6` — French title |
| `Title (RU)` | multilineText | `fldyP2mVnTwtlAq97` — Russian title |
| `Description (FR)` | multilineText | `fldpGTiZnyEK3tOXb` — French description |
| `Description (RU)` | multilineText | `fldryyVO80IwK5YSz` — Russian description |

**Formula fields (computed automatically — do not write to them):**

| Field | ID | Notes |
|---|---|---|
| `Description (truncated)` | `fldak4LCXI1OFeO43` | EN description capped at 1000 chars for FlexiPage |
| `Description (truncated) FR` | `fldy4RXcKpt6Rb593` | FR description capped at 1000 chars for FlexiPage |
| `Description (truncated) RU` | `fldN0cDUKSIYhD3MR` | RU description capped at 1000 chars for FlexiPage |
| `Equipements (formatted)` | — | EN, auto-formatted from multipleSelect |
| `Building (formatted)` | — | EN, auto-formatted from multipleSelect |
| `Security (formatted)` | — | EN, auto-formatted from multipleSelect |
| `Sport Facilities (formatted)` | — | EN, auto-formatted from multipleSelect |
| `Exterior Spaces (formatted)` | — | EN, auto-formatted from multipleSelect |

**Translated formatted fields (written by Google Apps Script for FR/RU PDFs):**

| Field | ID | Notes |
|---|---|---|
| `Equipements (formatted) FR` | `fldW0g6MsQ8oZogH0` | French translation of Equipements (formatted) |
| `Equipements (formatted) RU` | `fldFGmPNW6shj1FZx` | Russian translation |
| `Building (formatted) FR` | `fldjcnSm4vvWtnqEL` | French translation of Building (formatted) |
| `Building (formatted) RU` | `fldGcEjM1BHsf6BJj` | Russian translation |
| `Security (formatted) FR` | `fldlRspFKbH9SBDl1` | French translation of Security (formatted) |
| `Security (formatted) RU` | `fldrTYi1hzYXLJQvn` | Russian translation |
| `Sport Facilities (formatted) FR` | `fldkoSOtYZh3TDy0i` | French translation of Sport Facilities (formatted) |
| `Sport Facilities (formatted) RU` | `fldgehNtPyOpNvJXh` | Russian translation |
| `Exterior Spaces (formatted) FR` | `fldIdapMYx8nYyuTb` | French translation of Exterior Spaces (formatted) |
| `Exterior Spaces (formatted) RU` | `fldKKbFsR72YKIlaD` | Russian translation |

`Description (truncated)` fields are capped at **1000 characters** (tuned to fill the description column on page 1 of the FlexiPage PDF presentation without overflowing).

### Select Field Choices

**Location** (singleSelect)
Menton, Roquebrune-Cap-Martin, Monaco / Monte-Carlo, Cap-d'Ail, Èze-sur-Mer, Beaulieu-sur-Mer, Saint-Jean-Cap-Ferrat, Villefranche-sur-Mer, Nice, Saint-Laurent-du-Var, Cagnes-sur-Mer, Villeneuve-Loubet, Antibes, Juan-les-Pins, Cap d'Antibes, Golfe-Juan, Vallauris, Cannes, Mougins, Biot, Vence, Saint-Paul-de-Vence, Grasse, Tourrettes-sur-Loup, Saint-Tropez, Èze, Théoule-sur-Mer, Ramatuelle

**Status** (singleSelect): `Available` · `Booked` · `On Hold` · `Off Market`

**Price** (singleSelect — tier buckets): `up to €20k` · `€20k–30k` · `€30k–50k` · `€50k–100k` · `€100k–150k` · `€150k–250k` · `€250k+`

**Events Allowed** (singleSelect): `Yes` · `No` · `On Request`

**Architectural Style** (singleSelect — partial list): Contemporary, Provençal, Belle Époque, Mediterranean, Modern Minimalist, Modern, Minimalist, Classic, Traditional, Renovated, Luxury, Neo-Provençal, Château, Waterfront Domain, Provençal Bastide, Architectural Masterpiece, Contemporary Mediterranean, and many more.

**Views** (multipleSelects — partial list): Sea, Sea view, Sea Panoramic, Mountains, Hills, Hills Panoramic, Countryside, Garden, Forest, Port, Panoramic, Waterfront, Monaco, Bay of Cannes, Lerins Islands, Cap d'Antibes.

**Exposure** (multipleSelects): North, North-East, East, South-East, South, South-West, West, North-West.

**Services Included** (multipleSelects): Daily Housekeeping, Private Chef, Concierge, Security, Gardener, Pool Service, Laundry, Chef, Breakfast, Yoga instructor, Butler, Daily Cleaning, Chauffeur, Night Security.

**Equipements** (multipleSelects — interior): Air conditioning, Heating, Fireplace, Internet / Wi-Fi, Smart house, Spa bath, Jacuzzi, Sauna, Hammam, Furnished, TV, Washing machine, Dryer, Safe, King size bed, Electric vehicle charging, Lift, and more.

**Building** (multipleSelects): Elevator, Access for disabled people, Fiber optics, Home cinema, Wine cellar, Private cinema, Pool house.

**Security** (multipleSelects): Alarm, Safe, Digicode, Guard, Interphone, Electric gates, Armored door, Video surveillance, Security guard, Gated estate.

**Sport Facilities** (multipleSelects): Gym, Tennis, Sauna, Spa, Ping-pong, Playground, Golf, Lawn bowls, Steam room, Jacuzzi, Massage room, Helipad.

**Exterior Spaces** (multipleSelects): Garden, Patio, Barbeque, Barbecue, Pool, Swimming pool, Heated pool, Infinity pool, Terrace, Rooftop terrace, Pool house, Direct sea access, Fountain, Irrigation, Heliport, Pétanque court.

### Working with Records

When reading records, use `fieldIds` to limit response size. When writing singleSelect/multipleSelects values, pass the plain string name (e.g. `"Available"`), not the choice object. Before filtering on a select field without knowing the choice name, call `get_table_schema` to retrieve the choice IDs.

To filter Active listings: filter `Status` = `"Available"`.

Pagination: if the response includes a `nextCursor`, pass it as `cursor` in the next call to retrieve the remaining records.
