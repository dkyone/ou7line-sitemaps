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
