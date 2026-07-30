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

**Use `./scripts/deploy.sh`. It is the only supported deployment path.**

```bash
cd site
./scripts/deploy.sh              # check + build + deploy + verify
./scripts/deploy.sh --no-check   # skip `npm run check`
```

Target:

- code path: `/docker/blueskytravel-site` — **the repo root, not the `site/`
  subdirectory inside it**
- compose file: `/docker/blueskytravel-site/docker-compose.yml`
- shared Traefik network: `n8n_default`
- SSH: host alias `vps-n8n`, **port 2222** (port 22 times out)

### Never use `rsync` or `scp -r` for this

Both were used here before and failed *silently*: they reported success with a
half-copied tree, which left `src/` empty and deleted `scripts/run-astro.mjs`,
breaking the build on the server. A single tarball with a verified checksum is
atomic and can be checked before anything in production is touched.

### What the script does, and why each step exists

1. `npm run check` and `npm run build` — nothing that fails to compile ships.
2. Packs `site/` into one `.tar.gz`, excluding `node_modules`, `.git`,
   `.astro`, `dist`, `.env*`, keys and credentials, then **aborts** if anything
   sensitive still matched.
3. Copies that one file and compares md5 on both ends.
4. Extracts to a staging directory on the server and asserts the package is
   complete (`run-astro.mjs`, `package.json`, the Astro page, the store data)
   **before** production is modified. This is the check that was missing when
   deploys landed half-applied.
5. Publishes to `/docker/blueskytravel-site`, rebuilds with `--no-cache` and
   recreates the container.
6. Polls both live URLs until they answer 200, then greps the served HTML to
   confirm it is *this* build — a 200 alone can come from a stale image.

### Two traps specific to this server

- `/docker/blueskytravel-site/site/` exists but is an **orphan copy**. Docker
  builds from the parent directory. Deploying into `site/` looks like it works
  and changes nothing. The script excludes it deliberately.
- `ufw` rate-limits port 2222: more than ~6 SSH connections in 30s gets you
  temporarily refused. Don't loop retries tightly.

### CI/CD

There is none yet. If it is added later it must call this same script (or
reproduce these steps exactly) so the deployment path stays single. A pipeline
would need an SSH key with access to `vps-n8n:2222` stored as a secret.

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
