# Blue Sky Travel Site + Yoga Verde

Phase 1 marketing site for `blueskytravelmx.com`.

The same Astro/nginx release also serves the Yoga Verde storefront at
`/yoga-verde`. Yoga Verde is a premium natural-cosmetics storefront; its active
visual rules and Claude/Opus handoff are documented in
[`../docs/AGENT_INSTRUCTIONS.md`](../docs/AGENT_INSTRUCTIONS.md).

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
breaking the build on the server. The canonical path is a single tarball with a
verified SHA-256 checksum. The tarball is validated in a staging release before
the active directory is touched; publication then replaces the complete
directory instead of applying an additive overlay.

### What the script does, and why each step exists

1. `npm run check` and `npm run build` — nothing that fails to compile ships.
2. Packs `site/` into one `.tar.gz`, excluding `node_modules`, `.git`,
   `.astro`, `dist`, `.env*`, keys and credentials, then **aborts** if anything
   sensitive still matched.
3. Copies that one file and compares SHA-256 on both ends.
4. Extracts to a staging release beside the active directory and asserts the
   package and build manifest are complete **before** production is modified.
   It also aborts if the active server root contains secrets or operational
   files that the full-release replacement would delete.
5. Replaces `/docker/blueskytravel-site` with the complete staging release,
   keeping the previous release aside while Docker rebuilds with `--no-cache`.
   Trivy must then report zero fixable `HIGH`/`CRITICAL` vulnerabilities before
   the container is recreated. This also removes files deleted from the repo;
   it is not an additive tar overlay.
6. Polls both live URLs until they answer 200, then verifies
   `/yoga-verde/deploy-manifest.json` against the current build ID. Build,
   startup, interruption, or live-check failures trigger a state-aware rollback
   to the previous release. The old release is deleted only after verification.

### Two traps specific to this server

- `/docker/blueskytravel-site/site/` may exist as an **orphan copy** from an old
  deployment. Docker builds from the parent directory. Deploying into `site/`
  looks like it works and changes nothing. The full-release replacement removes
  that orphan intentionally; do not store secrets or runtime state under the
  active root.
- `ufw` rate-limits port 2222: more than ~6 SSH connections in 30s gets you
  temporarily refused. Don't loop retries tightly.

### CI/CD

`.github/workflows/site-ci.yml` runs the locked install, Astro check and static
build for site pull requests and pushes to `main`. Production deployment is
still intentionally performed with this script: GitHub does not yet have the
least-privilege SSH key and known-host secret required to call it safely. Any
future CD job must invoke `site/scripts/deploy.sh`; it must not duplicate the
tarball, rollback or live-verification logic.

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

### Yoga Verde release guardrails

- Deploy through `./scripts/deploy.sh` only; never use `rsync` or `scp -r`.
- Use the normalized `public/yoga-verde/assets/products/display/*.webp`
  derivatives with `contain`/centered placement.
- Keep warm white/cream surfaces dominant; reserve forest green and terracotta
  for text, active states and actions.
- Validate mobile detail scroll/close behavior and horizontal overflow before
  publishing.
- Yoga Verde is a multipage storefront. The home is a visual entry point;
  catalog, collections, kits and every product have dedicated URLs under
  `/yoga-verde/`. Do not collapse them back into one scroll-driven page.
- Keep product and price data centralized in
  `src/data/yoga-verde-store.js`; shared route helpers and visual curation live
  in `src/lib/yoga-verde.ts`.
- Product and kit cards must link to their dedicated pages. `shop.js` owns the
  shared cart and catalog filters, and the cart must persist across navigation.
