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

Deployment rule: deploy the site as a single `.tar.gz` tarball. Do not use
`rsync` or recursive directory copies such as `scp -r`. `scp` is allowed only
to transfer the tarball itself. Never include `.env`, tokens, credentials,
`node_modules`, `.git`, or generated `dist` files in the archive.

Example deployment sequence from the repository root:

```bash
set -euo pipefail

ARCHIVE="/tmp/yoga-verde-site-$(git rev-parse --short HEAD)-$(date -u +%Y%m%d%H%M%S).tar.gz"
tar \
  --exclude='site/.git' \
  --exclude='site/node_modules' \
  --exclude='site/dist' \
  --exclude='site/.astro' \
  --exclude='site/.env' \
  --exclude='site/**/*.env' \
  -czf "$ARCHIVE" site

scp "$ARCHIVE" root@72.60.228.135:/tmp/
ARCHIVE_NAME="$(basename "$ARCHIVE")"
ssh root@72.60.228.135 "set -euo pipefail
  mkdir -p /docker/blueskytravel-site/.incoming
  tar -xzf /tmp/$ARCHIVE_NAME -C /docker/blueskytravel-site/.incoming --strip-components=1
  cp -a /docker/blueskytravel-site/.incoming/. /docker/blueskytravel-site/
  rm -rf /docker/blueskytravel-site/.incoming
  rm -f /tmp/$ARCHIVE_NAME
  cd /docker/blueskytravel-site
  docker compose build
  docker compose up -d
"
rm -f "$ARCHIVE"
```

After every deployment, verify both the container and the Yoga Verde route:

```bash
ssh root@72.60.228.135 'cd /docker/blueskytravel-site && docker compose ps'
curl -fsS https://yoga-verde.srv1175749.hstgr.cloud/ >/dev/null
```

For the complete agent-facing rule and rollback expectations, read
`../docs/AGENT_INSTRUCTIONS.md`. For the active visual implementation brief,
use `../docs/YOGA_VERDE_OPUS5_MOBILE_PREMIUM_PROMPT.md`; the Opus Plan document
is historical.

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
