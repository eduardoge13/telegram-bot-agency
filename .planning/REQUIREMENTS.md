# Requirements: Spike Agency Platform

**Defined:** 2026-03-14
**Core Value:** Customers interact with an AI WhatsApp bot for product info, while a live e-commerce site showcases products — both deployed on a single VPS.

## v1 Requirements

### E-commerce Site

- [x] **ECOM-01**: Fix WhatsApp number to 5572408666 in all site files (replace placeholder 5215512345678)
- [x] **ECOM-02**: Configure Next.js standalone output for VPS deployment
- [x] **ECOM-03**: Site is accessible via public URL on Hostinger VPS

### VPS Infrastructure

- [ ] **INFRA-01**: nginx configured as reverse proxy routing to Next.js and WhatsApp bot services
- [ ] **INFRA-02**: SSL/HTTPS enabled via Certbot with auto-renewal (requires domain)
- [ ] **INFRA-03**: Process management via PM2 or Docker (consistent with existing VPS setup) with auto-restart
- [ ] **INFRA-04**: Next.js site running on VPS port 3000
- [ ] **INFRA-05**: WhatsApp bot service running on VPS port 3001

### WhatsApp Bot (Twilio)

- [ ] **BOT-01**: Express server receives Twilio WhatsApp webhook messages with signature validation
- [ ] **BOT-02**: Gemini AI generates contextual responses in Spanish based on business system prompt
- [ ] **BOT-03**: Bot looks up product info from Google Sheets when customer asks about products
- [ ] **BOT-04**: Bot sends formatted product details (name, price, availability) via WhatsApp

### Bot Platform Architecture

- [ ] **PLAT-01**: Business context registry — config-driven system where each business is defined by: Twilio number, system prompt, Google Sheets ID, enabled features
- [ ] **PLAT-02**: Message handler architecture is modular (separate handlers for product lookup, Q&A, etc.) so new capabilities can be plugged in per business
- [ ] **PLAT-03**: Conversation context isolation — state keyed on (businessId, customerPhone), no cross-business bleed
- [ ] **PLAT-04**: New business onboarding requires only config changes (no code changes) for basic Q&A + product lookup

## v2 Requirements

### Payments

- **PAY-01**: Stripe Checkout Sessions for card payments (redirect flow)
- **PAY-02**: Mercado Pago Checkout Pro for Mexican payment methods (cards, OXXO, SPEI)
- **PAY-03**: Payment webhook handlers that confirm payments and log orders to Google Sheets
- **PAY-04**: Order confirmation and cancellation pages
- **PAY-05**: Bot sends payment links to customers via WhatsApp

### Advanced Bot Features

- **ADV-01**: Amadeus API flight search via WhatsApp conversation
- **ADV-02**: Order status tracking via WhatsApp bot
- **ADV-03**: Field editing capabilities via WhatsApp (admin commands)
- **ADV-04**: Working-hours awareness with auto-reply
- **ADV-05**: Second business context (travel agency) fully configured

## Out of Scope

| Feature | Reason |
|---------|--------|
| Telegram bot changes | Current version is sufficient; focus shifts to WhatsApp |
| In-chat payment collection | PCI compliance risk — always redirect to Stripe/MP |
| Voice message processing | High complexity, low MVP value |
| Conversation transcript storage | Privacy law risk (Mexico LFPDPPP) |
| Database (Postgres/MongoDB) | Google Sheets sufficient for MVP scale |
| Mobile app | Web-first approach |
| Real-time inventory sync | Manual updates via bot editing is fine for MVP |
| Self-service business onboarding | Config-based for now; admin panel is v2+ |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ECOM-01 | Phase 1: Site + Infrastructure | Complete |
| ECOM-02 | Phase 1: Site + Infrastructure | Complete |
| ECOM-03 | Phase 1: Site + Infrastructure | Complete |
| INFRA-01 | Phase 1: Site + Infrastructure | Pending |
| INFRA-02 | Phase 1: Site + Infrastructure | Pending |
| INFRA-03 | Phase 1: Site + Infrastructure | Pending |
| INFRA-04 | Phase 1: Site + Infrastructure | Pending |
| INFRA-05 | Phase 2: WhatsApp Bot Platform | Pending |
| BOT-01 | Phase 2: WhatsApp Bot Platform | Pending |
| BOT-02 | Phase 2: WhatsApp Bot Platform | Pending |
| BOT-03 | Phase 2: WhatsApp Bot Platform | Pending |
| BOT-04 | Phase 2: WhatsApp Bot Platform | Pending |
| PLAT-01 | Phase 2: WhatsApp Bot Platform | Pending |
| PLAT-02 | Phase 2: WhatsApp Bot Platform | Pending |
| PLAT-03 | Phase 2: WhatsApp Bot Platform | Pending |
| PLAT-04 | Phase 2: WhatsApp Bot Platform | Pending |

**Coverage:**
- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-14*
*Last updated: 2026-03-14 after roadmap creation — phase names finalized*
