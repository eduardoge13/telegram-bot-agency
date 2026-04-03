# WhatsApp Privacy Policy URL Setup

This document is the canonical handoff for the Meta privacy-policy requirement.

## Canonical URL

Use this URL in **Meta Developers -> App Settings -> Basic -> Privacy Policy URL**:

`https://blueskytravelmx.com/privacy-policy`

Current implementation source:

- Astro site: `site/`
- privacy page route: `site/src/pages/privacy-policy.astro`
- deployed VPS path: `/docker/blueskytravel-site`

## Why this URL

- `blueskytravelmx.com` is the primary branded domain.
- Keep one canonical page for Meta.
- If `blueskytravelmx.online` and `blueskytravelmx.info` are live, point them to the same page or redirect them to the canonical `.com` page.

## What The Page Must Do

- Serve over HTTPS.
- Return a real HTML page with the privacy policy content.
- Be publicly accessible without login.
- Include the business name and a contact method.
- Stay stable once Meta has accepted it.

## Current Hosting Path

The new site is already deployed on the VPS behind Traefik. The remaining work is DNS cutover, not page creation.

Current VPS target:

- `72.60.228.135`

Current public DNS still points elsewhere, so Meta should not be updated until the production domain resolves to the VPS.

## GoDaddy DNS Update Path

1. Open the GoDaddy DNS manager for `blueskytravelmx.com`.
2. Change the apex `A` record to:
   - `72.60.228.135`
3. Change `www` to match the apex or configure it to resolve to the same host.
4. Save changes.
5. Wait for propagation.
6. Confirm `https://blueskytravelmx.com/privacy-policy` returns `200`.

## Access Checklist

If you need to edit the page later:

1. Open the GoDaddy DNS manager for `blueskytravelmx.com`.
2. Confirm the A record points to `72.60.228.135`.
3. Open `https://blueskytravelmx.com/privacy-policy`.
4. If legal details change, edit the Astro site under `site/src/config/site.ts`, redeploy to the VPS, and re-check the public URL.

## Meta Update Path

After the page is live:

1. Open **Meta Developers**.
2. Go to **App Settings -> Basic**.
3. Paste `https://blueskytravelmx.com/privacy-policy` into **Privacy Policy URL**.
4. Save changes.
5. Switch the app from **Development** to **Live**.

## Notes

- Keep this URL stable; Meta may re-check it.
- If the page moves, update Meta immediately.
- If you use the `.online` domain for staging, do not make it the canonical URL in Meta.
- Before Meta Live, replace the legal placeholders in `site/src/config/site.ts` with final business details.
