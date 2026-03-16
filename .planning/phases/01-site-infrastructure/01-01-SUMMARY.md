---
phase: 01-site-infrastructure
plan: 01
subsystem: ui
tags: [nextjs, tailwind, docker, whatsapp, spei, ecommerce]

# Dependency graph
requires: []
provides:
  - "lib/constants.ts with centralized WHATSAPP_NUMBER (5572408666) and SPEI_CLABE"
  - "Next.js standalone output configuration for containerized deployment"
  - "Multi-stage Dockerfile and docker-compose.yml for VPS deployment"
  - "SpeiPaymentSection component with CLABE display and copy-to-clipboard"
  - "Homepage with ProductCard grid, SPEI section, and consolidated product data"
affects:
  - 01-02-deploy (needs Dockerfile and docker-compose.yml from this plan)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Centralized constants pattern: all config values (WA number, CLABE) in lib/constants.ts"
    - "Multi-stage Docker build: deps -> builder -> runner with node:22-alpine"
    - "Product data sourced from getAllProducts() — no hardcoded duplication on homepage"

key-files:
  created:
    - "spike-ecommerce-web/lib/constants.ts"
    - "spike-ecommerce-web/components/SpeiPaymentSection.tsx"
    - "spike-ecommerce-web/Dockerfile"
    - "spike-ecommerce-web/docker-compose.yml"
    - "spike-ecommerce-web/.dockerignore"
  modified:
    - "spike-ecommerce-web/app/page.tsx"
    - "spike-ecommerce-web/components/ProductCard.tsx"
    - "spike-ecommerce-web/next.config.ts"

key-decisions:
  - "WHATSAPP_NUMBER and SPEI_CLABE centralized in lib/constants.ts to prevent future drift"
  - "Carousel slides derived from getAllProducts() to eliminate data duplication between page.tsx and products.json"
  - "SpeiPaymentSection uses 'use client' for clipboard API; CLABE displayed with copy button and 3-step instructions"
  - "SPEI_CLABE set to placeholder 000000000000000000 with TODO comment — client must provide real CLABE before launch"
  - "Trust bar updated: removed Stripe/MercadoPago (deferred to v2), kept authentic products, WhatsApp, shipping"

patterns-established:
  - "Constants pattern: import from @/lib/constants, never hardcode config values inline"
  - "Docker pattern: node:22-alpine multi-stage, non-root nextjs user, copy standalone + static + public"

requirements-completed: [ECOM-01, ECOM-02, ECOM-03]

# Metrics
duration: 5min
completed: 2026-03-16
---

# Phase 1 Plan 01: Site Infrastructure Summary

**Next.js e-commerce site containerized for VPS deployment with correct WhatsApp number, SPEI payment section, consolidated product grid, and multi-stage Dockerfile**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-16T14:56:10Z
- **Completed:** 2026-03-16T15:00:44Z
- **Tasks:** 2
- **Files modified:** 8 (5 created, 3 modified)

## Accomplishments
- Replaced hardcoded WhatsApp placeholder (5215512345678) with centralized constant (5572408666) across all components
- Created SpeiPaymentSection with CLABE display, copy-to-clipboard, and 3-step payment instructions in Spanish
- Refactored homepage to derive carousel slides from `getAllProducts()` — no more hardcoded duplicate data
- Integrated ProductCard component in a product grid section (was unused before)
- Configured Next.js standalone output and created production-ready multi-stage Dockerfile

## Task Commits

Each task was committed atomically (in spike-ecommerce-web repo):

1. **Task 1: Fix WhatsApp number, add constants, configure standalone and Docker** - `205d479` (feat)
2. **Task 2: Add SPEI payment section and improve homepage design** - `52e4e16` (feat)

## Files Created/Modified
- `spike-ecommerce-web/lib/constants.ts` - WHATSAPP_NUMBER and SPEI_CLABE constants
- `spike-ecommerce-web/components/SpeiPaymentSection.tsx` - SPEI payment trust section with copy-to-clipboard
- `spike-ecommerce-web/Dockerfile` - Multi-stage build: deps/builder/runner on node:22-alpine
- `spike-ecommerce-web/docker-compose.yml` - Service definition with restart: unless-stopped
- `spike-ecommerce-web/.dockerignore` - Excludes node_modules, .next, .git, *.md, docs/
- `spike-ecommerce-web/app/page.tsx` - Full homepage refactor: product grid, SPEI section, data from products.json
- `spike-ecommerce-web/components/ProductCard.tsx` - Updated to import WHATSAPP_NUMBER from constants
- `spike-ecommerce-web/next.config.ts` - Added output: 'standalone'

## Decisions Made
- Carousel slides are now derived dynamically from `getAllProducts()` rather than a hardcoded `slides` array — eliminates data duplication and ensures carousel always reflects products.json
- SPEI_CLABE is a placeholder (`000000000000000000`) with a TODO comment. Client must provide their real CLABE before the site goes live
- Trust bar updated to remove Stripe and Mercado Pago references (those payment processors are deferred to v2); replaced with "Productos originales" and "Compra segura"
- ProductCard component (previously unused on the homepage) is now rendered in a full product grid section

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created SpeiPaymentSection before Task 1 build check**
- **Found during:** Task 1 verification (npm run build)
- **Issue:** page.tsx imports SpeiPaymentSection (Task 2 component) which didn't exist yet, causing build failure
- **Fix:** Created SpeiPaymentSection.tsx before running the final build verification; both tasks were still committed separately with correct Task 1 / Task 2 split
- **Files modified:** components/SpeiPaymentSection.tsx
- **Verification:** npm run build succeeds with exit 0
- **Committed in:** 52e4e16 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (blocking import dependency between tasks)
**Impact on plan:** Necessary — page.tsx changes span both tasks. Tasks still committed as separate commits. No scope creep.

## Issues Encountered
- Build order dependency: page.tsx was modified in Task 1 to import SpeiPaymentSection (Task 2), making the Task 1 standalone build check fail. Resolved by creating SpeiPaymentSection first, then committing tasks in correct order.

## User Setup Required
- **SPEI_CLABE:** Replace `'000000000000000000'` in `spike-ecommerce-web/lib/constants.ts` with the client's real CLABE interbancaria before launch.

## Next Phase Readiness
- Site code is complete and builds successfully with `npm run build`
- Dockerfile and docker-compose.yml are ready for Plan 02 (VPS deployment)
- All WhatsApp links point to 5572408666
- Plan 02 only needs to: clone repo, `docker compose up -d`, configure Nginx reverse proxy

---
## Self-Check: PASSED

- lib/constants.ts: FOUND
- components/SpeiPaymentSection.tsx: FOUND
- Dockerfile: FOUND
- docker-compose.yml: FOUND
- SUMMARY.md: FOUND
- Task 1 commit 205d479: FOUND
- Task 2 commit 52e4e16: FOUND

*Phase: 01-site-infrastructure*
*Completed: 2026-03-16*
