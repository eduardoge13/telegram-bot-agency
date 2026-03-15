# Research Summary — Spike Agency Platform

**Synthesized:** 2026-03-14
**Sources:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

## Key Findings

### Stack
- **WhatsApp bot:** Twilio ^5.x + Express ^4.19 + TypeScript (new service on port 3001)
- **Checkout:** Stripe Checkout Sessions (redirect) + Mercado Pago Checkout Pro (redirect) via Next.js API routes
- **Flights:** Amadeus npm SDK ^10.x (stub-first, credentials pending)
- **VPS:** nginx reverse proxy + PM2 + Certbot. Build Next.js locally, deploy standalone. No Docker needed.
- **Don't use:** Docker, Fastify, Stripe Elements, MP Checkout Bricks, any database (Sheets is enough for MVP)

### Table Stakes Features
- **E-commerce:** Stripe + MP checkout flows, payment webhooks, order confirmation, order storage in Sheets
- **WhatsApp bot:** Twilio webhook, Gemini AI responses (Spanish), product lookup, welcome message, business hours
- **Platform:** One Twilio number per business, isolated conversation contexts

### Architecture
- Two services on one VPS: Next.js (:3000) + Express WhatsApp bot (:3001)
- nginx routes traffic, handles SSL termination
- Multi-tenant via phone number → business context registry
- Telegram bot stays on current hosting (unchanged)
- Shared: Gemini API (called independently), Google Sheets (shared data)

### Critical Pitfalls (Top 5)
1. **Twilio WhatsApp production approval** — start Meta Business Manager verification on day 1 (1-7+ day wait)
2. **MercadoPago Mexico misconfiguration** — verify access token is MLM (Mexico), not MLA (Argentina)
3. **SSL/domain required** — need a domain name for Let's Encrypt cert; raw IP won't work for HTTPS
4. **Next.js standalone output** — must configure `output: 'standalone'` before VPS deploy; build locally, not on VPS
5. **Multi-tenant context bleed** — key all state on `${businessId}:${customerPhone}` from the start

### Immediate Fixes (Already Broken)
- Replace WhatsApp number `5215512345678` → `5572408666` in both `app/page.tsx` and `components/ProductCard.tsx`
- Fix Stripe API version mismatch (`@ts-expect-error` in `lib/stripe.ts`)

## Recommended Phase Order

Based on dependency analysis across all research:

1. **VPS Infrastructure + E-commerce Deploy** — nginx, PM2, HTTPS, fix WhatsApp number, complete checkout flows, deploy site
2. **WhatsApp Bot Foundation** — Twilio webhook, Gemini AI, product lookup, multi-tenant config
3. **Advanced Features** — Amadeus flight search, order tracking via bot, payment links via bot

## Open Questions Requiring User Input
- Domain name for VPS? (Required for SSL)
- Twilio sandbox or production? (Affects development workflow)
- WhatsApp bot code: same repo or new repo?

---
*Synthesized: 2026-03-14*
