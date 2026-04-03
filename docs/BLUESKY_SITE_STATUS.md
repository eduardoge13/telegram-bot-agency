# Blue Sky Travel Site Status

Date: 2026-04-02

This document tracks the current state of the new Blue Sky Travel Phase 1 website.

## What Is Already Done

- Built a new Astro + TypeScript static site under `site/`.
- Implemented bilingual routes:
  - `/`
  - `/en/`
  - `/privacy-policy`
  - `/en/privacy-policy`
  - `/terms`
  - `/en/terms`
  - `/data-deletion`
  - `/en/data-deletion`
- Added sitemap support, robots configuration, canonical tags, alternate-language tags, and social metadata.
- Replaced the generic hero treatment with real destination photography extracted from the current live site and packaged locally under:
  - `site/public/images/hero-summit.jpg`
  - `site/public/images/hero-social.jpg`
- Refined the homepage layout to reduce repeated-card sections and create a more editorial sales flow.
- Polished the Spanish homepage and legal copy to read closer to production quality.
- Deployed the new site to the VPS at:
  - `/docker/blueskytravel-site`
- Brought up the Docker service:
  - `blueskytravel-site-bluesky-site-1`
- Verified Traefik routing internally on the VPS for:
  - `blueskytravelmx.online`
  - `blueskytravelmx.com`
  - `blueskytravelmx.info`

## Verified Runtime State

- `npm run check` passes locally.
- `npm run build` passes locally.
- Internal Traefik HTTPS verification on the VPS returns `200` for:
  - `https://blueskytravelmx.online/`
  - `https://blueskytravelmx.com/`
- Staging host currently returns:
  - `X-Robots-Tag: noindex, nofollow, noarchive`

## Current Blockers

### 1. DNS is not pointed at the VPS yet

Current public DNS still points elsewhere:

- `blueskytravelmx.com -> 172.66.0.70`
- `blueskytravelmx.online -> 15.197.148.33, 3.33.130.190`
- `blueskytravelmx.info -> 15.197.148.33, 3.33.130.190`

The VPS target should be:

- `72.60.228.135`

### 2. Legal placeholders are still present

These values still need final production values in `site/src/config/site.ts`:

- `brand.legalEntity`
- `brand.legalAddress`
- `brand.privacyEmail` if it changes
- `brand.salesEmail` if it changes

### 3. Production visual assets are still incomplete

The site is materially better now, but production polish still benefits from:

- final logo or wordmark
- one or more real brand-approved hero/support images
- real proof sources or partner credibility marks

## Immediate Next Steps

1. Replace the legal placeholders in `site/src/config/site.ts`.
2. Point `blueskytravelmx.online` A record to `72.60.228.135`.
3. Verify the public `.online` site over HTTPS.
4. Use `https://blueskytravelmx.online/privacy-policy` as staging review for the Meta/legal pass.
5. Once approved, point `blueskytravelmx.com` to `72.60.228.135`.
6. Update Meta App Settings with:
   - `https://blueskytravelmx.com/privacy-policy`
7. Switch the Meta app to `Live`.
8. Re-test the WhatsApp flow in n8n with a real inbound message.

## GoDaddy DNS Cutover Targets

Recommended order:

1. Lower TTL on the existing A records.
2. Update `blueskytravelmx.online` apex A record to `72.60.228.135`.
3. Update `www.blueskytravelmx.online` to match.
4. Validate staging publicly.
5. Update `blueskytravelmx.com` apex A record to `72.60.228.135`.
6. Update `www.blueskytravelmx.com` to match.
7. Point `blueskytravelmx.info` to `72.60.228.135` so Traefik can perform the redirect to `.com`.
