# Yoga Verde Handoff - 2026-05-05

## Purpose

This handoff is for transferring the current Yoga Verde work to another developer, including the minimum project memory needed to continue without replaying the full chat history.

## Repository

- Primary repo: `https://github.com/eduardoge13/telegram-bot-agency`
- Secondary remote: `https://github.com/travel-agency-git/telegram-bot-agency`
- Working branch for this handoff: `codex/yoga-verde-transfer`

## What Yoga Verde Is

Yoga Verde is a separate preview experience living inside the same repository and the same Astro static site deployment used for Blue Sky Travel.

It is currently exposed on a neutral VPS hostname so the client does not see any Blue Sky Travel branding in the URL:

- Preview URL: `https://yoga-verde.srv1175749.hstgr.cloud/`

## Current Stack

- Frontend app root: `site/`
- Framework: Astro static site
- Runtime requirement: Node `>=22.12.0`
- Static serving: nginx container
- Edge routing: Traefik on the VPS

## Files Added or Changed for Yoga Verde

### Main implementation

- `site/public/yoga-verde/index.html`
- `site/public/yoga-verde/shop.js`

### Assets copied into the repo

- `site/public/yoga-verde/assets/shop/*`
- `site/public/yoga-verde/assets/*`

### Deployment glue

- `site/docker-compose.yml`
- `site/deploy/nginx.conf`

## How Yoga Verde Is Routed

The public host is routed by Traefik to the same site container as Blue Sky Travel.

### Traefik rule

In `site/docker-compose.yml` a dedicated router was added:

- Host: `yoga-verde.srv1175749.hstgr.cloud`

### nginx rewrite

In `site/deploy/nginx.conf`, requests for that host are internally rewritten so `/` resolves to `/yoga-verde/`.

That means the Yoga Verde build is still implemented as static files under `public/yoga-verde/`, but the user sees it at the root of the neutral subdomain.

## Current Product State

The current implementation is intentionally shop-first.

### Live features

- Shop-first landing instead of blog-first/editorial-first
- Hero based on the package's catalog screen
- Sustainability banner
- Filter sidebar
- Search input
- Product grid
- Product detail modal
- Interactive slide-out cart
- Quantity updates
- Remove item
- Running totals
- Mobile layout with working cart CTA

### Product behavior

- Cart state is stored in browser `localStorage`
- Storage key: `yogaVerdeCartV2`
- Shipping is currently hardcoded to `$5.00` when cart has items
- Tax is currently hardcoded to `8%`
- Checkout button is still a demo action only

## Verification Completed

The deployed page was checked after deployment.

### Functional checks

- Public URL responds with `HTTP 200`
- Catalog loads with `5` visible products
- Add-to-cart works
- Cart badge updates
- Cart total recalculates
- Cart drawer opens and shows correct line item

### Visual checks

- Desktop full-page screenshot reviewed
- Mobile full-page screenshot reviewed
- Cart-open screenshot reviewed

## Important Design Decision

The first attempt leaned too much toward editorial/blog presentation. That was rejected.

The corrected implementation makes the shop the primary experience:

- the catalog is above the philosophy block
- the cart is interactive
- all five products are visible by default
- no filter is active by default at first load

This point matters. If someone refactors the page, do not move Yoga Verde back toward a blog-first layout unless asked explicitly.

## Package Source Context

The original source package used during implementation existed locally on the Mac machine under:

- `/Users/eduardogaitan/Downloads/stitch_ra_ces_bot_nicas_ancestrales`

The important source references were:

- catalog screen
- cart screen
- editorial/home screen

Those local paths are not part of the repo, so the transfer should assume the repo is now the source of truth.

## How To Run Locally

From the repo root:

```bash
cd site
npm install
npm run dev
```

Open:

- `http://localhost:4321/yoga-verde/`

If the developer wants production-like behavior with the neutral host routing, they need the VPS Traefik/nginx setup. For normal frontend work, the path-based local URL is enough.

## How To Build

```bash
cd site
npm run build
```

## How It Was Deployed

Local repo contents were synced to:

- `/docker/blueskytravel-site/` on the VPS

Then the container was rebuilt with:

```bash
docker compose up -d --build
```

## Open Work

### Frontend / product

- Replace checkout demo with a real sales path
- Decide whether checkout goes to WhatsApp, Stripe, or another flow
- Decide whether the newsletter form should be real or remain visual-only
- Decide whether unused legacy Yoga Verde assets should be removed or kept as archive

### Domain / branding

- If a cleaner client-facing domain is needed, map a custom domain or subdomain instead of `srv1175749.hstgr.cloud`

## Broader Project Memory

This repo is not just the Yoga Verde site. It also contains work related to Blue Sky Travel, Meta WhatsApp API migration, and n8n bots.

### Blue Sky Travel site

- Main site work lives under the same `site/` app
- Production domain is Blue Sky Travel
- Legal/privacy pages were added earlier for Meta go-live support

### Meta / WhatsApp migration

- Twilio was archived for later use
- Active direction is Meta WhatsApp API, not Twilio
- Existing docs already in repo:
  - `docs/WHATSAPP_MIGRATION_STATUS.md`
  - `docs/WHATSAPP_PRIVACY_URL_SETUP.md`

### n8n / bot context

- There is an n8n deployment on the VPS
- Telegram and WhatsApp workflows exist there
- Telegram "Agente Pendientes Operativos" was made operational again using local persistence instead of depending on revoked Google OAuth
- Reminder logic now runs with an internal cron in n8n instead of relying on Google Calendar

## What Not To Assume

- Do not assume Yoga Verde has a real checkout yet
- Do not assume the Blue Sky Travel production domain should be reused for Yoga Verde branding
- Do not assume the original local design package will be available on the Windows machine
- Do not assume secrets are in the repo

## Recommended Next Step For The Receiving Developer

1. Pull branch `codex/yoga-verde-transfer`
2. Run the site locally
3. Review `site/public/yoga-verde/index.html` and `site/public/yoga-verde/shop.js`
4. Confirm whether the next milestone is:
   - real checkout
   - WhatsApp order handoff
   - visual polish
   - custom domain
