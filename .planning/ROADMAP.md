# Roadmap: Spike Agency Platform

## Overview

Two delivery moments: first, the Punto Clave MX e-commerce site goes live on the VPS with the correct WhatsApp number and HTTPS; second, the WhatsApp bot comes online as a multi-tenant platform serving Gemini AI responses and product lookups. Everything needed to operate the platform as an MVP is complete after Phase 2.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Site + Infrastructure** - E-commerce site fixed, deployed, and accessible over HTTPS on the VPS
- [ ] **Phase 2: WhatsApp Bot Platform** - Multi-tenant WhatsApp bot live on VPS, handling AI responses and product lookups

## Phase Details

### Phase 1: Site + Infrastructure
**Goal**: The Punto Clave MX site is accessible over HTTPS on the VPS with the correct WhatsApp number and all traffic routed through nginx
**Depends on**: Nothing (first phase)
**Requirements**: ECOM-01, ECOM-02, ECOM-03, INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. Visiting the VPS domain in a browser loads the Punto Clave MX site over HTTPS with a valid certificate
  2. All WhatsApp links on the site open a conversation with 5572408666 (not the old placeholder number)
  3. nginx serves the site on port 3000 and the process survives a VPS reboot via PM2
  4. Certbot auto-renewal is configured and the cert expiry is at least 89 days out
**Plans**: TBD

Plans:
- [ ] 01-01: Fix WhatsApp number and configure Next.js standalone output
- [ ] 01-02: Provision VPS — nginx, PM2, Certbot, deploy Next.js site

### Phase 2: WhatsApp Bot Platform
**Goal**: A multi-tenant WhatsApp bot is live on the VPS, receiving Twilio webhooks, responding in Spanish via Gemini AI, and looking up products from Google Sheets — with architecture that supports adding a second business via config only
**Depends on**: Phase 1
**Requirements**: INFRA-05, BOT-01, BOT-02, BOT-03, BOT-04, PLAT-01, PLAT-02, PLAT-03, PLAT-04
**Success Criteria** (what must be TRUE):
  1. Sending a WhatsApp message to the Twilio number receives a Spanish-language AI response within 10 seconds
  2. Asking about a product by name returns that product's name, price, and availability from Google Sheets
  3. Two customers messaging simultaneously get isolated responses with no cross-contamination of conversation context
  4. Adding a second business requires only a new entry in the config file — no code changes
  5. The bot service on port 3001 restarts automatically after a crash or VPS reboot
**Plans**: TBD

Plans:
- [ ] 02-01: Build WhatsApp bot service — Twilio webhook, Gemini AI, product lookup
- [ ] 02-02: Implement multi-tenant platform architecture — business registry, modular handlers, context isolation
- [ ] 02-03: Deploy bot service to VPS port 3001 and wire nginx routing

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Site + Infrastructure | 0/2 | Not started | - |
| 2. WhatsApp Bot Platform | 0/3 | Not started | - |
