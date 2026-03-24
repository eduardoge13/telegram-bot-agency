---
phase: 02-whatsapp-bot-platform
plan: 03
subsystem: infra
tags: [docker, traefik, vps, docker-compose, python, fastapi, uvicorn, hostinger]

# Dependency graph
requires:
  - phase: 01-site-infrastructure
    provides: Traefik + n8n_default network pattern on VPS, wildcard DNS at srv1175749.hstgr.cloud
  - phase: 02-whatsapp-bot-platform-01
    provides: WhatsApp bot FastAPI app (app/main.py) with /health and /webhook endpoints
  - phase: 02-whatsapp-bot-platform-02
    provides: Multi-tenant architecture and dispatcher, all handler modules
provides:
  - Dockerfile for Python 3.12-slim multi-stage bot image with healthcheck
  - docker-compose.yml with Traefik labels routing bot.srv1175749.hstgr.cloud to port 3001
  - .dockerignore excluding dev/test artifacts from Docker context
  - Bot service live on VPS at https://bot.srv1175749.hstgr.cloud with auto-SSL and auto-restart
affects: [future-phases, twilio-webhook-setup, credentials-provisioning]

# Tech tracking
tech-stack:
  added: [docker, docker-compose, traefik-labels, uvicorn]
  patterns: [multi-stage-docker-build, traefik-docker-label-routing, n8n_default-network-attachment]

key-files:
  created:
    - whatsapp-bot/Dockerfile
    - whatsapp-bot/docker-compose.yml
    - whatsapp-bot/.dockerignore
  modified: []

key-decisions:
  - "GeminiClient initialization deferred to first request — container starts healthy without GEMINI_API_KEY in .env, enabling incremental credential provisioning"
  - "No host port binding in docker-compose.yml — Traefik discovers container via Docker socket over n8n_default network, same as Phase 1 shop service"
  - "Multi-stage Docker build (builder + runner stages) keeps final image lean by excluding build tools"

patterns-established:
  - "New VPS services: add to n8n_default network, attach Traefik labels, no host port binding"
  - "Bot credentials provisioned post-deploy: container starts without credentials, activates when .env is populated on VPS"

requirements-completed: [INFRA-05]

# Metrics
duration: 45min
completed: 2026-03-24
---

# Phase 02 Plan 03: Containerization and VPS Deployment Summary

**Python 3.12-slim multi-stage Docker image deployed to Hostinger VPS at https://bot.srv1175749.hstgr.cloud via Traefik routing on n8n_default network, /health returning 200 with auto-restart enabled**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-03-24
- **Completed:** 2026-03-24
- **Tasks:** 2 (1 auto + 1 human-verify)
- **Files modified:** 3

## Accomplishments

- Multi-stage Dockerfile built for Python 3.12-slim with curl healthcheck (interval 30s, retries 3, start-period 40s)
- docker-compose.yml follows exact Phase 1 Traefik pattern: n8n_default network, TLS via certresolver=myresolver, no host port binding
- Bot deployed to VPS, container running healthy, /health returning `{"status":"ok","service":"whatsapp-bot"}` over HTTPS
- Container configured with `restart: unless-stopped` — survives crashes and VPS reboots
- Human verification checkpoint passed: SSL valid, container healthy on `docker ps`

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Dockerfile, docker-compose.yml, .dockerignore and deploy to VPS** - `574be9c` (feat)
2. **Auto-fix: Defer GeminiClient init to allow startup without GEMINI_API_KEY** - `fce2034` (fix)
3. **Task 2: Human-verify VPS deployment** - APPROVED (no commit — verification only)

## Files Created/Modified

- `whatsapp-bot/Dockerfile` - Multi-stage Python 3.12-slim image; builder stage installs deps, runner stage copies packages + app; CMD uvicorn on port 3001; curl HEALTHCHECK
- `whatsapp-bot/docker-compose.yml` - Service with Traefik labels for bot.srv1175749.hstgr.cloud, n8n_default network, env_file .env, healthcheck, restart: unless-stopped
- `whatsapp-bot/.dockerignore` - Excludes tests/, __pycache__/, .env, .git/, *.md, .pytest_cache/, .mypy_cache/, *.pyc

## Decisions Made

- GeminiClient deferred init: the original code instantiated GeminiClient at import time which caused startup failure when GEMINI_API_KEY was absent. Changed to lazy init on first use so the container starts and /health returns 200 immediately. Credentials are added to .env on VPS when ready.
- Followed Phase 1 Traefik pattern exactly (n8n_default external network, certresolver=myresolver, no exposed host ports) — consistent with shop service deployment.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Deferred GeminiClient instantiation to allow graceful startup without credentials**
- **Found during:** Task 1 (deploy to VPS)
- **Issue:** GeminiClient was instantiated at module import time; container exited immediately on VPS because GEMINI_API_KEY was not yet in .env
- **Fix:** Moved GeminiClient construction inside the method that first uses it (lazy init), so the process starts and /health is reachable without any AI credentials present
- **Files modified:** whatsapp-bot/app/ (GeminiClient usage site)
- **Verification:** Container started healthy on VPS; `curl https://bot.srv1175749.hstgr.cloud/health` returned `{"status":"ok","service":"whatsapp-bot"}`
- **Committed in:** `fce2034`

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug: startup crash without optional credential)
**Impact on plan:** Fix was required for the /health success criterion. No scope creep. Bot will activate for real traffic once credentials are added to /opt/telegram-bot-agency/whatsapp-bot/.env on VPS.

## Issues Encountered

- Container failed to start on first deploy because GeminiClient init required GEMINI_API_KEY at import time. Resolved via lazy init (see deviation above).

## User Setup Required

External services require manual configuration before end-to-end WhatsApp messaging works:

**Twilio:**
- `TWILIO_ACCOUNT_SID` — Twilio Console -> Account -> Account SID
- `TWILIO_AUTH_TOKEN` — Twilio Console -> Account -> Auth Token
- Webhook URL: set `https://bot.srv1175749.hstgr.cloud/webhook` in Twilio Console -> Messaging -> Sandbox Settings (or active number config)

**Google AI (Gemini):**
- `GEMINI_API_KEY` — https://aistudio.google.com/apikey

**Google Sheets:**
- `GOOGLE_CREDENTIALS_JSON` — GCP Console -> IAM -> Service Accounts -> Keys -> JSON (paste entire JSON as single-line string)

**Amadeus (flights):**
- `AMADEUS_CLIENT_ID` — Amadeus for Developers -> My Apps -> API Key
- `AMADEUS_CLIENT_SECRET` — Amadeus for Developers -> My Apps -> API Secret

**Where to add:** SSH into VPS, edit `/opt/telegram-bot-agency/whatsapp-bot/.env`, then run `docker compose restart` in that directory.

## Next Phase Readiness

- Bot service is live and healthy at https://bot.srv1175749.hstgr.cloud/webhook — Twilio can deliver webhooks to this URL now
- End-to-end WhatsApp messaging is blocked only on Twilio credentials and Twilio Console webhook config (listed above)
- Phase 2 complete — all three plans executed. Platform is production-ready pending credential provisioning.

---
*Phase: 02-whatsapp-bot-platform*
*Completed: 2026-03-24*
