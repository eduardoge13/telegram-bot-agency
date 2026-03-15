# Phase 1: Site + Infrastructure - Research

**Researched:** 2026-03-15
**Domain:** Next.js containerized deployment, nginx reverse proxy, Certbot SSL, site code changes
**Confidence:** HIGH (codebase directly inspected, no external library lookups needed for known-stable tools)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Use Docker (docker-compose) — consistent with existing clinic system on the VPS
- Plan for nginx possibly already running (check on VPS) — add site config either way
- Next.js configured with `output: 'standalone'` for containerized deployment
- Dockerfile for Next.js standalone build
- Push to GitHub, SSH into VPS, git pull, docker-compose up
- Build happens inside Docker container on VPS (or multi-stage Dockerfile)
- No CI/CD for MVP — manual deploy is fine
- Replace placeholder `5215512345678` with `5572408666` in:
  - `app/page.tsx` (line 6)
  - `components/ProductCard.tsx` (line 5)
- Add a "Pago por Transferencia" section with SPEI logo for trust
- Display a placeholder CLABE account number for the client's bank account
- SPEI is widely trusted in Mexico — showing the logo builds credibility
- Act as a professional web designer — make improvements that increase conversion and trust
- Improve overall selling points, visual hierarchy, and call-to-action effectiveness
- Ensure the site looks premium and trustworthy for a Mexican tech e-commerce brand
- Fix any UX issues found during implementation (product data duplication, unused components, etc.)

### Claude's Discretion
- Exact Docker/docker-compose configuration
- nginx site config details
- SSL/Certbot setup approach
- Specific design improvements (typography, spacing, sections, layout refinements)
- Whether to extract homepage sections into reusable components
- How to handle the SPEI/CLABE display (modal, section, footer, etc.)

### Deferred Ideas (OUT OF SCOPE)
- Stripe/Mercado Pago checkout flows — v2 (payment accounts not set up yet)
- Cart functionality — v2
- Product detail pages — v2
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ECOM-01 | Fix WhatsApp number to 5572408666 in all site files (replace placeholder 5215512345678) | Two exact file locations confirmed via code inspection: `app/page.tsx` line 6, `components/ProductCard.tsx` line 5 |
| ECOM-02 | Configure Next.js standalone output for VPS deployment | `next.config.ts` is currently empty — needs `output: 'standalone'` added; Next.js 16.1.6 is installed |
| ECOM-03 | Site is accessible via public URL on Hostinger VPS | Requires Dockerfile + docker-compose + nginx config pointing to port 3000 |
| INFRA-01 | nginx configured as reverse proxy routing to Next.js and WhatsApp bot services | nginx server block pattern documented below; port 3000 for this phase, port 3001 reserved for Phase 2 |
| INFRA-02 | SSL/HTTPS enabled via Certbot with auto-renewal (requires domain) | BLOCKER: No domain acquired yet — cert cannot be issued to raw IP; standalone Certbot flow documented |
| INFRA-03 | Process management via PM2 or Docker with auto-restart | docker-compose `restart: unless-stopped` is the correct approach given existing VPS patterns |
| INFRA-04 | Next.js site running on VPS port 3000 | Docker exposes port 3000; nginx proxies inbound 80/443 to it |
</phase_requirements>

---

## Summary

This phase has two distinct workstreams that can proceed in parallel: (1) source code changes to the e-commerce site and (2) VPS infrastructure setup. The code changes are surgical and low-risk — two WhatsApp number replacements, one next.config.ts edit, a new SPEI section, and design improvements. The infrastructure work is the heavier lift: writing a multi-stage Dockerfile, a docker-compose.yml, and an nginx server block, then configuring Certbot on the VPS.

There is one hard blocker: **INFRA-02 (HTTPS) requires a domain name**. Certbot cannot issue certificates for raw IP addresses. Everything else in this phase can be completed and verified without a domain. The recommended approach is to complete all code changes and infrastructure setup first, then activate HTTPS the moment a domain is pointed at 72.60.228.135. A separate task for HTTPS should be scoped as "ready to run on demand."

The VPS already has an existing system (clinica_guarneros) using docker-compose with the same `restart: unless-stopped` pattern. This confirms the infrastructure approach and means Docker Engine is already installed. nginx may already be running as a host process serving the clinic system — this must be verified on the VPS before deciding whether to run nginx in a container or add a site config to the existing host nginx.

**Primary recommendation:** Build a multi-stage Dockerfile for Next.js standalone, docker-compose for the ecommerce service, and add an nginx upstream block to whatever nginx instance is already present on the VPS (or install nginx if absent). Structure HTTPS as a final unlock task once a domain is available.

---

## Standard Stack

### Core
| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| Next.js | 16.1.6 (installed) | Site framework | Already installed in repo |
| React | 19.2.3 (installed) | UI runtime | Already installed |
| Tailwind CSS | 4.x (installed) | Styling | Already used throughout site |
| Docker Engine | Latest stable | Container runtime | Already on VPS (clinic system uses it) |
| docker-compose | v2 plugin | Service orchestration | Consistent with clinica_guarneros pattern |
| nginx | Latest stable (host) | Reverse proxy + SSL termination | Standard for VPS; likely already running |
| Certbot | Latest | Let's Encrypt SSL certificates | Industry standard; free; auto-renewal via systemd timer |

### Supporting
| Library / Tool | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| node:22-alpine | Docker base | Node.js runtime for build stage | Smallest image for Next.js |
| TypeScript | 5.x (installed) | Type safety | Already configured |
| Google Fonts (Syne + Outfit) | via next/font | Typography | Already integrated in layout.tsx |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| docker-compose host build | GitHub Actions CI/CD | CI/CD is deferred for MVP; manual deploy is faster to set up |
| host nginx | nginx in Docker container | Host nginx is simpler when VPS may already have it running |
| Certbot standalone | Caddy (auto-HTTPS) | Certbot is standard; Caddy would require replacing nginx |

**Installation (on VPS, if nginx not present):**
```bash
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx
```

---

## Architecture Patterns

### Recommended Project Structure (spike-ecommerce-web additions)

```
spike-ecommerce-web/
├── Dockerfile                  # Multi-stage Next.js standalone build (NEW)
├── docker-compose.yml          # Service definition (NEW)
├── .env.example                # Env var template (NEW)
├── app/
│   ├── page.tsx                # EDIT: fix WhatsApp number + design improvements
│   └── layout.tsx              # Existing — unchanged
├── components/
│   ├── ProductCard.tsx         # EDIT: fix WhatsApp number
│   └── SpeiPaymentSection.tsx  # NEW: SPEI/CLABE trust section
├── next.config.ts              # EDIT: add output: 'standalone'
└── lib/
    └── constants.ts            # NEW: WHATSAPP_NUMBER + CLABE constant
```

### Pattern 1: Next.js Standalone Multi-Stage Dockerfile

**What:** A two-stage Docker build that produces a minimal production image using Next.js `output: 'standalone'`. Stage 1 installs deps and builds; Stage 2 copies only the `.next/standalone` directory and static assets.

**When to use:** Containerizing any Next.js app for VPS deployment.

```dockerfile
# Source: Next.js official docs — standalone output
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Copy only standalone output (no node_modules, no source)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

### Pattern 2: docker-compose.yml for ecommerce service

**What:** Defines the Next.js container with port binding and auto-restart policy.

```yaml
services:
  ecommerce:
    build: .
    container_name: spike_ecommerce
    ports:
      - "3000:3000"
    restart: unless-stopped
    environment:
      - NODE_ENV=production
```

**Note:** `restart: unless-stopped` means the container restarts after VPS reboot automatically. This satisfies INFRA-03 without PM2.

### Pattern 3: nginx Reverse Proxy Config

**What:** nginx server block that proxies port 80 (and later 443) to localhost:3000.

```nginx
# /etc/nginx/sites-available/puntoclavemx
server {
    listen 80;
    server_name YOUR_DOMAIN_HERE;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

After domain is acquired:
```bash
sudo certbot --nginx -d yourdomain.com
```
Certbot modifies the server block in place to add `listen 443 ssl` and HTTP→HTTPS redirect, and installs a systemd timer for auto-renewal.

### Pattern 4: WhatsApp Number as a Module Constant

**What:** Extract the phone number to a single constant file so it can never drift between files again.

```typescript
// lib/constants.ts
export const WHATSAPP_NUMBER = '5572408666';
export const SPEI_CLABE = '000000000000000000'; // placeholder from client
```

Both `app/page.tsx` and `components/ProductCard.tsx` import from here. This eliminates the duplication identified in the code review.

### Pattern 5: SPEI Section Design

**What:** A trust-building section placed after the "Cómo funciona" section or inside the existing trust bar. Displays CLABE and bank transfer instructions.

**Implementation approach:** Inline SVG or `<img>` for the SPEI logo (publicly available), visible CLABE number with a copy-to-clipboard button, brief instruction copy in Spanish.

```typescript
// components/SpeiPaymentSection.tsx
// Displays SPEI logo + CLABE for direct bank transfer
// Positioned in the trust/credibility section of page.tsx
```

### Anti-Patterns to Avoid

- **Building on VPS without `output: 'standalone'`:** Default Next.js build requires `node_modules` in production. Standalone mode outputs a self-contained server.js — do not skip this.
- **Using PM2 inside Docker:** PM2 is a process manager; Docker's restart policy replaces it. Running PM2 inside a container adds complexity with no benefit.
- **Binding nginx directly to port 3000:** nginx should listen on 80/443 (host) and proxy to 3000. Do not try to make nginx and Next.js both listen on 3000.
- **Committing .env files:** Keep secrets out of git; use .env.example as the template.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSL certificate + renewal | Custom cert generation scripts | Certbot + Let's Encrypt | Handles ACME challenge, renewal cron, nginx integration |
| Process restart on reboot | Startup scripts | docker-compose `restart: unless-stopped` | Docker daemon handles this natively |
| Static file serving | Custom Next.js routes | nginx serves `/public` assets directly | Faster; offloads static traffic from Node |
| Next.js production server | Custom Express wrapper | Next.js standalone `server.js` | Already generated by `output: 'standalone'` |

**Key insight:** The entire process management story is solved by `restart: unless-stopped` in docker-compose — the container restarts when Docker daemon starts (which itself starts on boot via systemd). No PM2 needed.

---

## Common Pitfalls

### Pitfall 1: Next.js standalone missing static files
**What goes wrong:** The container starts but CSS/images return 404. The standalone output does NOT automatically copy `/public` or `.next/static`.
**Why it happens:** `output: 'standalone'` only copies the server — static files must be explicitly copied in the Dockerfile.
**How to avoid:** Always include these two COPY lines in the runner stage:
```dockerfile
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
```
**Warning signs:** Site loads HTML but images/styles are broken.

### Pitfall 2: Port conflicts with existing VPS services
**What goes wrong:** `docker-compose up` fails because port 3000 is already bound by the clinic system or another process.
**Why it happens:** Multiple services competing for the same host port.
**How to avoid:** SSH into VPS first and run `ss -tlnp | grep 3000` before deploying. If a conflict exists, use a different host port (e.g., `3002:3000`) and update the nginx upstream.
**Warning signs:** "bind: address already in use" error on docker-compose up.

### Pitfall 3: nginx already running as host process
**What goes wrong:** Installing nginx via Docker conflicts with a host nginx already serving other virtual hosts (clinic system).
**Why it happens:** The clinica_guarneros system may use host nginx. Adding a containerized nginx creates a port 80 conflict.
**How to avoid:** Check VPS first (`systemctl status nginx`). If nginx is running on the host, add a new `sites-available` config and `sites-enabled` symlink — do NOT containerize nginx for this project.
**Warning signs:** Port 80 already in use when trying to start a containerized nginx.

### Pitfall 4: Certbot requires domain name (not IP)
**What goes wrong:** `certbot --nginx -d 72.60.228.135` fails — Let's Encrypt does not issue certs for IP addresses.
**Why it happens:** The ACME protocol requires domain validation.
**How to avoid:** Do not attempt Certbot until a domain is pointed at the VPS IP. Plan the HTTPS task as a conditional unlock: "run after domain is configured."
**Warning signs:** Certbot error "The ACME protocol only allows domains."

### Pitfall 5: Google Fonts blocked in containers / CSP issues
**What goes wrong:** Fonts fail to load in production due to Content Security Policy headers.
**Why it happens:** nginx may add restrictive headers; Google Fonts CDN requests are blocked.
**How to avoid:** Do not add `Content-Security-Policy` headers in nginx config for this phase. Next.js already handles font optimization via `next/font/google`.
**Warning signs:** Font fallback in production; console CSP errors.

### Pitfall 6: HOSTNAME not set for Next.js standalone
**What goes wrong:** Container runs but is not reachable — Next.js binds to `127.0.0.1` (localhost only) instead of `0.0.0.0`.
**Why it happens:** Standalone server defaults to localhost binding in some Next.js versions.
**How to avoid:** Always set `ENV HOSTNAME=0.0.0.0` in the Dockerfile runner stage.
**Warning signs:** nginx proxy returns "502 Bad Gateway" even though the container is running.

---

## Code Examples

### next.config.ts — standalone output
```typescript
// Source: Next.js docs — self-hosting with Docker
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
};

export default nextConfig;
```

### WhatsApp number fix — app/page.tsx line 6
```typescript
// Before (line 6):
const WHATSAPP_NUMBER = '5215512345678';

// After:
const WHATSAPP_NUMBER = '5572408666';
```

### WhatsApp number fix — components/ProductCard.tsx line 5
```typescript
// Before (line 5):
const WHATSAPP_NUMBER = '5215512345678';

// After:
const WHATSAPP_NUMBER = '5572408666';
```

**Better long-term (Claude's discretion):** Extract to `lib/constants.ts` and import in both files. Eliminates future drift.

### nginx enable site
```bash
sudo ln -s /etc/nginx/sites-available/puntoclavemx /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Certbot SSL (run after domain is live)
```bash
sudo certbot --nginx -d puntoclavemx.com
# Auto-renewal is configured automatically via systemd timer
# Verify: sudo systemctl status certbot.timer
```

### Deploy workflow (manual MVP)
```bash
# On local machine:
git push origin main

# SSH into VPS:
ssh user@72.60.228.135
cd /path/to/spike-ecommerce-web
git pull origin main
docker-compose up -d --build
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PM2 for process management with Docker | docker-compose `restart: unless-stopped` | Docker Compose v2 (stable) | Simpler; no PM2 installed in container |
| `next export` (static HTML) | `output: 'standalone'` | Next.js 13+ | Supports server components, API routes, dynamic rendering |
| `node_modules` copied into production container | Multi-stage build — standalone output only | Next.js 12.1+ | Much smaller image; no source code in production |
| Separate cron job for Certbot | systemd timer (installed by Certbot automatically) | Ubuntu 20.04+ | No manual cron needed |

**Deprecated/outdated:**
- `next export`: Static-only export, does not support App Router dynamic features. Do NOT use — `output: 'standalone'` is the correct mode.
- PM2 inside Docker: Anti-pattern. Docker handles process supervision.

---

## Open Questions

1. **Is nginx already running on the VPS?**
   - What we know: clinica_guarneros uses docker-compose but its docker-compose.yml does NOT include nginx — the backend binds directly to `HOST_PORT` (default 5000). nginx may be on the host.
   - What's unclear: Whether a host nginx process exists and has an active config.
   - Recommendation: First task on VPS must be `systemctl status nginx` and `ss -tlnp`. This determines whether we add a site-available config or install nginx fresh.

2. **What GitHub repo does the ecommerce site push to?**
   - What we know: The project is at `/Users/eduardogaitan/Documents/projects/spike-ecommerce-web` locally. No git remote URL was found in inspection.
   - What's unclear: Whether a GitHub remote exists and what the VPS pull path will be.
   - Recommendation: The planner should include a task to verify/add a GitHub remote and record the VPS clone path.

3. **Domain name status**
   - What we know: No domain acquired per STATE.md. INFRA-02 is blocked.
   - What's unclear: When the domain will be acquired.
   - Recommendation: Scope INFRA-02 as a standalone task that runs when triggered — not blocking other tasks. All other phase work completes independently.

4. **CLABE account number**
   - What we know: A placeholder CLABE is needed; the real one comes from the client.
   - What's unclear: Whether the client has provided a real CLABE yet.
   - Recommendation: Use an explicit placeholder string (`000000000000000000`) in `lib/constants.ts` with a TODO comment. The client replaces it via a simple constant update.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None currently in spike-ecommerce-web repo |
| Config file | None — see Wave 0 gaps |
| Quick run command | `cd /path/to/spike-ecommerce-web && npm run build` (build succeeds = no TypeScript/Next.js errors) |
| Full suite command | Manual browser smoke test against running container |

**Note:** This phase is primarily infrastructure + code edits with no business logic to unit test. The meaningful validation is: (a) `npm run build` succeeds, (b) container starts and responds on port 3000, (c) nginx proxies correctly, (d) WhatsApp links open with correct number.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ECOM-01 | WhatsApp number is 5572408666 everywhere | smoke | `grep -r "5215512345678" app/ components/` returns empty | N/A (grep check) |
| ECOM-02 | Next.js standalone build succeeds | build | `npm run build` exits 0 | ❌ Wave 0: verify next.config.ts edit |
| ECOM-03 | Site accessible on VPS | smoke | `curl -s http://72.60.228.135 -o /dev/null -w "%{http_code}"` returns 200 | N/A |
| INFRA-01 | nginx proxies port 80 to 3000 | smoke | `curl -s http://localhost -H "Host: domain"` returns 200 from container | N/A |
| INFRA-02 | HTTPS cert valid, expiry 89+ days | smoke (blocked) | `echo | openssl s_client -connect domain:443 2>/dev/null | openssl x509 -noout -dates` | N/A (blocked on domain) |
| INFRA-03 | Container restarts after reboot | smoke | VPS reboot + `docker ps` shows container running | N/A |
| INFRA-04 | Next.js on port 3000 | smoke | `docker-compose ps` + `curl http://localhost:3000` | N/A |

### Sampling Rate
- **Per task commit:** `npm run build` (ecommerce site) — catches TypeScript errors and config mistakes
- **Per wave merge:** Full smoke test: build succeeds + container runs + nginx proxies + WhatsApp number correct
- **Phase gate:** All smoke tests green + HTTPS active (or INFRA-02 explicitly deferred pending domain) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `spike-ecommerce-web/Dockerfile` — does not exist, must be created in first task
- [ ] `spike-ecommerce-web/docker-compose.yml` — does not exist, must be created
- [ ] `spike-ecommerce-web/lib/constants.ts` — does not exist (optional but recommended for clean WHATSAPP_NUMBER extraction)
- [ ] `spike-ecommerce-web/components/SpeiPaymentSection.tsx` — does not exist, created during design task
- [ ] nginx site config `/etc/nginx/sites-available/puntoclavemx` — does not exist on VPS

---

## Sources

### Primary (HIGH confidence)
- Direct inspection of `/Users/eduardogaitan/Documents/projects/spike-ecommerce-web/` — all file paths, line numbers, current code state
- Direct inspection of `/Users/eduardogaitan/Documents/projects/clinica_guarneros/docker-compose.yml` — existing VPS Docker pattern
- `.planning/phases/01-site-infrastructure/01-CONTEXT.md` — user-locked decisions
- `.planning/REQUIREMENTS.md` — requirement IDs and descriptions
- `.planning/STATE.md` — blocker documentation (no domain)

### Secondary (MEDIUM confidence)
- Next.js `output: 'standalone'` Docker pattern — well-established, in official Next.js docs (https://nextjs.org/docs/app/building-your-application/deploying#docker-image)
- nginx reverse proxy pattern for Node.js — industry standard configuration

### Tertiary (LOW confidence)
- nginx existing on VPS — assumed from typical VPS setups; must verify with `systemctl status nginx` on the actual server before implementing

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools are already installed or are VPS-standard; no new library decisions needed
- Architecture: HIGH — patterns confirmed by inspecting the existing codebase and the clinic system's docker-compose
- Pitfalls: HIGH — derived from direct code inspection (port 3000 binding, standalone static file omission, HOSTNAME env var)
- HTTPS/Certbot: MEDIUM — standard approach but actual VPS state unknown until SSH inspection

**Research date:** 2026-03-15
**Valid until:** 2026-06-15 (stable tools; Next.js 16, Docker, nginx, Certbot all stable APIs)
