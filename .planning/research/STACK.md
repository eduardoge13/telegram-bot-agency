# Stack Research — Spike Agency Platform

**Researched:** 2026-03-14
**Confidence:** MEDIUM (training data + codebase analysis; no live web verification)

## Current Stack (Existing)

### telegram-bot-agency
- **Runtime:** Node.js 18+
- **Language:** JavaScript (CommonJS)
- **Bot framework:** node-telegram-bot-api
- **AI:** Google Gemini API (@google/generative-ai)
- **Data:** Google Sheets (googleapis)
- **Caching:** node-cache

### spike-ecommerce-web
- **Runtime:** Node.js
- **Language:** TypeScript 5.x
- **Framework:** Next.js 16.1.6 (App Router)
- **React:** 19.2.3
- **Styling:** Tailwind CSS 4.x
- **Payments:** stripe ^20.4.0, @stripe/stripe-js ^8.9.0, mercadopago ^2.12.0

## New Stack Additions

### 1. Twilio WhatsApp Integration
| Component | Recommendation | Confidence |
|-----------|---------------|------------|
| SDK | `twilio` ^5.x | HIGH |
| Webhook server | `express` ^4.19 | HIGH |
| Language | TypeScript (align with web repo) | HIGH |

**Why Express over raw HTTP:** Twilio webhooks send form-encoded POST data. Express with `urlencoded` middleware handles this natively. Also needed for webhook signature validation (`twilio.webhook()` middleware).

**Why not Fastify/Hono:** Express is Twilio's documented framework. All official examples use Express. Not worth the divergence risk for an MVP.

### 2. Stripe Checkout (Complete Existing)
| Component | Recommendation | Confidence |
|-----------|---------------|------------|
| Flow | Stripe Checkout Sessions (redirect) | HIGH |
| API route | Next.js Route Handler (`app/api/checkout/stripe/route.ts`) | HIGH |
| Webhook | `app/api/webhooks/stripe/route.ts` | HIGH |
| API version | Update to match SDK version (remove @ts-expect-error) | HIGH |

**Why Checkout Sessions over Elements:** Simpler integration, PCI compliance handled by Stripe, supports all payment methods. Stripe Elements is overkill for MVP.

### 3. Mercado Pago Checkout (Complete Existing)
| Component | Recommendation | Confidence |
|-----------|---------------|------------|
| Flow | Checkout Pro (redirect to MP) | HIGH |
| API route | Next.js Route Handler (`app/api/checkout/mercadopago/route.ts`) | HIGH |
| Webhook (IPN) | `app/api/webhooks/mercadopago/route.ts` | HIGH |
| Config | Ensure Mexico marketplace configuration | CRITICAL |

**Why Checkout Pro:** Redirect-based flow is simplest. Handles all Mexican payment methods (cards, OXXO, SPEI). MP's Checkout Bricks is newer but more complex.

**PITFALL:** MercadoPago defaults to Argentina. Must verify access token is for Mexico marketplace. Wrong country = wrong currency + wrong payment methods.

### 4. Amadeus Flight Search
| Component | Recommendation | Confidence |
|-----------|---------------|------------|
| SDK | `amadeus` npm package ^10.x | MEDIUM |
| API | Flight Offers Search v2 | MEDIUM |
| Environment | Sandbox (test) until credentials confirmed | HIGH |

**Why npm SDK over raw REST:** Handles authentication (OAuth2 token refresh), pagination, and error mapping. Direct REST requires manual token management.

**Integration point:** Lives in the WhatsApp bot service (not in Next.js). Flight search is a conversational flow, not a web page.

### 5. VPS Deployment
| Component | Recommendation | Confidence |
|-----------|---------------|------------|
| Reverse proxy | nginx | HIGH |
| Process manager | PM2 ^5 | HIGH |
| SSL | Certbot (Let's Encrypt) | HIGH |
| Next.js mode | `output: 'standalone'` in next.config.ts | HIGH |
| Node version | Node.js 20 LTS | HIGH |

**Why PM2 over Docker:** Single VPS, single developer, two services. PM2 is simpler to debug, restart, and monitor. Docker adds orchestration overhead with no benefit at this scale.

**Why nginx:** Routes traffic by path/domain to different ports. Handles SSL termination. Required for Twilio webhook HTTPS.

**VPS layout:**
- Port 3000: Next.js (Punto Clave MX site)
- Port 3001: WhatsApp bot (Express + Twilio)
- nginx: ports 80/443 → reverse proxy to 3000/3001

## What NOT to Use

| Technology | Why Not |
|-----------|---------|
| Docker/K8s | Overkill for single VPS with 2 services |
| Fastify/Hono | Twilio docs and examples all use Express |
| Stripe Elements | More complex than Checkout Sessions for MVP |
| MP Checkout Bricks | Newer but more complex than Checkout Pro |
| Database (Postgres/MongoDB) | Google Sheets is sufficient for MVP; adding a DB adds migration complexity |
| Vercel | VPS already procured; Vercel would split infrastructure |

---
*Researched: 2026-03-14*
