# Spike Agency Platform

## What This Is

A multi-business AI bot platform and e-commerce system. The platform serves different businesses through a shared AI engine (Gemini) with business-specific contexts. The first two businesses are Punto Clave MX (Mexican tech e-commerce) and a travel agency (flight search via Amadeus API). The customer-facing channels are a Next.js e-commerce website and a WhatsApp bot (via Twilio), both deployed on a Hostinger VPS.

## Core Value

Customers can interact with an AI-powered WhatsApp bot and a live e-commerce site to get product info, check flight prices, track orders, and make purchases — all with minimal manual intervention from the business owner.

## Requirements

### Validated

<!-- Existing capabilities from current codebase -->

- ✓ Telegram bot with Gemini AI integration — existing (`telegram-bot-agency`)
- ✓ Google Sheets integration for product/client data — existing (`telegram-bot-agency`)
- ✓ Field editing via inline keyboard buttons — existing (`telegram-bot-agency`)
- ✓ Next.js landing page with product catalog — existing (`spike-ecommerce-web`)
- ✓ Stripe and Mercado Pago SDK initialization — existing (`spike-ecommerce-web`)
- ✓ WhatsApp link-based sales flow — existing (`spike-ecommerce-web`)
- ✓ Product data model with prices in MXN cents — existing (`spike-ecommerce-web`)

### Active

- [ ] Complete payment gateway integration (Stripe + Mercado Pago checkout flows)
- [ ] Update WhatsApp number to canonical number (5572408666) across the web codebase
- [ ] Deploy Punto Clave MX website to Hostinger VPS (72.60.228.135)
- [ ] WhatsApp bot via Twilio with Gemini AI (shared engine from Telegram bot)
- [ ] Customer-facing order tracking via WhatsApp bot
- [ ] Field editing capabilities via WhatsApp bot (product info updates)
- [ ] General Q&A via WhatsApp bot (Gemini AI answering business/product questions)
- [ ] Amadeus API integration for flight price lookups (travel agency business)
- [ ] Multi-business context system — one bot engine serving different business contexts
- [ ] Deploy WhatsApp bot service to Hostinger VPS

### Out of Scope

- Telegram bot further development — current version is sufficient, focus shifts to WhatsApp
- Live chat widget embedded on website — separate channel for now
- Mobile app — web-first approach
- Database migration — keep Google Sheets for now
- Real-time inventory sync between bot and website — manual for MVP

## Context

**Two repos, two businesses, one platform:**
- `telegram-bot-agency` (this repo) — Node.js Telegram bot with Gemini AI + Google Sheets. Serves as the bot engine blueprint.
- `spike-ecommerce-web` (sibling repo at `/Users/eduardogaitan/Documents/projects/spike-ecommerce-web`) — Next.js 16 e-commerce site for Punto Clave MX. Currently a landing page with WhatsApp sales links. Payment SDKs initialized but no checkout flows.

**Infrastructure:**
- Hostinger VPS: 72.60.228.135 (root SSH access, public key configured)
- Will host: e-commerce site + WhatsApp bot service

**Key numbers:**
- Canonical WhatsApp: 5572408666 (replace placeholder 5215512345678)
- Twilio credentials: to be provided later
- Amadeus API credentials: to be provided later

**Codebase maps available:**
- `.planning/codebase/` — telegram-bot-agency analysis (7 documents, 1,184 lines)
- `.planning/codebase-web/` — spike-ecommerce-web analysis (7 documents, 293 lines)

## Constraints

- **Infrastructure:** Single Hostinger VPS for all deployments
- **Payment providers:** Stripe + Mercado Pago (Mexico market, MXN currency)
- **AI engine:** Google Gemini (already integrated in Telegram bot)
- **WhatsApp:** Must use Twilio (credentials pending)
- **Flight data:** Must use Amadeus API (credentials pending)
- **Repos:** Keep repos separate (best practice) — telegram-bot-agency and spike-ecommerce-web
- **Credentials:** Twilio and Amadeus API keys not yet available — build integration stubs

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| WhatsApp over Telegram for customers | Clients don't use Telegram, WhatsApp is ubiquitous in Mexico | — Pending |
| Twilio for WhatsApp | Industry standard WhatsApp Business API provider | — Pending |
| Shared AI engine across businesses | One Gemini-powered bot, multiple business contexts — reduces duplication | — Pending |
| Single VPS deployment | Cost-effective, sufficient for MVP traffic | — Pending |
| Keep repos separate | Best practice for independent deploy cycles and team scaling | — Pending |
| Amadeus for flights | Standard GDS API for flight data | — Pending |

---
*Last updated: 2026-03-14 after initialization*
