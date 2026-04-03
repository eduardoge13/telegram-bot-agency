# Blue Sky Travel Site

Phase 1 marketing site for `blueskytravelmx.com`.

## Stack

- Astro + TypeScript
- Static output
- nginx container
- Traefik routing on the VPS

## Local development

```bash
cd site
npm install
npm run dev
```

## Quality checks

```bash
cd site
npm run check
npm run build
```

## Deploy to VPS

Expected VPS target:

- code path: `/docker/blueskytravel-site`
- compose file: `/docker/blueskytravel-site/docker-compose.yml`
- shared Traefik network: `n8n_default`

Deployment sequence:

```bash
scp -r site root@72.60.228.135:/docker/blueskytravel-site
ssh root@72.60.228.135
cd /docker/blueskytravel-site
docker compose build
docker compose up -d
```

## Routes

- `/` Spanish homepage
- `/en/` English homepage
- `/privacy-policy`
- `/en/privacy-policy`
- `/terms`
- `/en/terms`
- `/data-deletion`
- `/en/data-deletion`

## Design guardrails

Before changing the homepage visual language, review:

- `../docs/BLUESKY_VISUAL_GUARDRAILS.md`

## Production blockers

Before Meta Live and production cutover, replace the legal placeholders in `src/config/site.ts`:

- legal entity
- business address
- privacy email if it changes
- sales email if it changes
- production-grade visual assets and proof
