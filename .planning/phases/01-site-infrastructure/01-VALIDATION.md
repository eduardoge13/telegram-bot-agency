---
phase: 1
slug: site-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None (infrastructure phase — smoke tests only) |
| **Config file** | none — no test framework needed |
| **Quick run command** | `cd /path/to/spike-ecommerce-web && npm run build` |
| **Full suite command** | Build + container start + curl smoke tests |
| **Estimated runtime** | ~30 seconds (build) |

---

## Sampling Rate

- **After every task commit:** Run `npm run build`
- **After every plan wave:** Run full smoke test suite (build + container + curl checks)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | ECOM-01 | smoke | `grep -r "5215512345678" app/ components/` returns empty | N/A | ⬜ pending |
| 01-01-02 | 01 | 1 | ECOM-02 | build | `npm run build` exits 0 | N/A | ⬜ pending |
| 01-01-03 | 01 | 1 | ECOM-03 | smoke | `curl -s http://localhost:3000` returns 200 | N/A | ⬜ pending |
| 01-02-01 | 02 | 1 | INFRA-01 | smoke | `curl -s http://localhost` returns 200 via nginx | N/A | ⬜ pending |
| 01-02-02 | 02 | 1 | INFRA-02 | smoke | `openssl s_client -connect domain:443` (blocked on domain) | N/A | ⬜ pending |
| 01-02-03 | 02 | 1 | INFRA-03 | smoke | `docker ps` shows container after reboot | N/A | ⬜ pending |
| 01-02-04 | 02 | 1 | INFRA-04 | smoke | `docker-compose ps` + `curl http://localhost:3000` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `spike-ecommerce-web/Dockerfile` — multi-stage Next.js standalone build
- [ ] `spike-ecommerce-web/docker-compose.yml` — service definition
- [ ] `spike-ecommerce-web/lib/constants.ts` — WhatsApp number + CLABE constants
- [ ] nginx site config on VPS — `/etc/nginx/sites-available/puntoclavemx`

*These files are created during plan execution, not as test stubs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WhatsApp links open correct conversation | ECOM-01 | Requires mobile device/WhatsApp | Click WhatsApp link on site, verify opens chat with 5572408666 |
| Site visually correct after design improvements | ECOM-03 | Visual/subjective | Load site in browser, check layout, typography, SPEI section |
| HTTPS cert valid and auto-renews | INFRA-02 | Requires domain + VPS access | Run certbot renew --dry-run on VPS |
| Container survives VPS reboot | INFRA-03 | Requires VPS reboot | SSH into VPS, reboot, wait, check docker ps |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
