# Features Research — Spike Agency Platform

**Researched:** 2026-03-14
**Confidence:** MEDIUM (codebase analysis HIGH; ecosystem claims MEDIUM)

## E-commerce Checkout

### Table Stakes
| Feature | Complexity | Notes |
|---------|-----------|-------|
| Stripe checkout flow (card payments) | Medium | SDK initialized, need API routes + webhook |
| Mercado Pago checkout (cards, OXXO, SPEI) | Medium | SDK initialized, need API routes + IPN |
| Order confirmation page | Low | Success/cancel redirect pages |
| Payment webhook handlers | Medium | Confirm payment, update order status |
| Order storage (Google Sheets log) | Low | Minimal order record for tracking |
| Correct WhatsApp number (5572408666) | Trivial | Replace placeholder in 2 files |

### Differentiators
| Feature | Complexity | Notes |
|---------|-----------|-------|
| Payment link via WhatsApp bot | Medium | Bot sends Stripe/MP checkout URL in chat |
| Dual payment provider (Stripe + MP) | Low | Already have both SDKs; Mexico loves options |
| Product availability check via bot | Low | Bot queries Sheets for stock |

### Anti-Features (Do NOT Build)
| Feature | Why Not |
|---------|---------|
| In-chat card collection | PCI compliance nightmare — always redirect to Stripe/MP |
| Custom payment form | Stripe Checkout and MP Checkout Pro handle this securely |
| Inventory sync (real-time) | Manual updates via bot field editing is sufficient for MVP |

## WhatsApp Bot

### Table Stakes
| Feature | Complexity | Notes |
|---------|-----------|-------|
| Twilio webhook receiving messages | Medium | Express server, webhook validation |
| Gemini AI responses (Spanish) | Low | Port from Telegram bot — same API |
| Product lookup from Sheets | Low | Port from Telegram bot |
| Greeting / welcome message | Low | First-time customer detection |
| Working-hours awareness | Low | Auto-reply outside business hours |

### Differentiators
| Feature | Complexity | Notes |
|---------|-----------|-------|
| Order status inquiry | Medium | Requires order storage first |
| Field editing via WhatsApp | Medium | Port inline keyboard pattern to text-based flow |
| Flight price search (Amadeus) | High | New integration, conversational flow |
| Multi-business context routing | Medium | Different system prompts per business number |

### Anti-Features
| Feature | Why Not |
|---------|---------|
| Shared WhatsApp number across businesses | UX confusion, context bleed risk |
| Conversation transcript storage | Privacy law surface area (Mexico LFPDPPP) |
| Voice message processing | High complexity, low MVP value |

## Flight Search (Amadeus)

### Table Stakes
| Feature | Complexity | Notes |
|---------|-----------|-------|
| Search flights by origin/destination/date | High | Amadeus API + NLP to extract params |
| Display top 3-5 results with prices | Medium | Format for WhatsApp message |
| Handle "no flights found" gracefully | Low | Friendly message, suggest alternatives |

### Differentiators
| Feature | Complexity | Notes |
|---------|-----------|-------|
| Price alerts ("notify me if cheaper") | High | Requires scheduled checks — v2 |
| Multi-city search | High | Complex Amadeus query — v2 |

### Anti-Features
| Feature | Why Not |
|---------|---------|
| Flight booking | Requires airline partnerships, complex liability |
| Seat selection | Way beyond MVP scope |

## Multi-Tenant Platform

### Table Stakes
| Feature | Complexity | Notes |
|---------|-----------|-------|
| Business context config (prompt, Sheets ID, features) | Medium | JSON/env-based config per business |
| One Twilio number per business | Low | Simplest routing — webhook per number |
| Isolated conversation contexts | Medium | Key on (businessId, customerPhone) |

### Differentiators
| Feature | Complexity | Notes |
|---------|-----------|-------|
| Self-service business onboarding | High | Admin panel — v2+ |
| Per-business analytics | Medium | Message counts, response times — v2 |

## Feature Dependencies

```
Order Storage (Sheets) ──→ Order Status via Bot
                       ──→ Payment Webhook Confirmation
                       ──→ Payment Link via Bot

Stripe/MP Checkout ────→ Payment Link via WhatsApp Bot

Twilio Webhook ────────→ Gemini AI Responses
                       ──→ Product Lookup
                       ──→ Flight Search
                       ──→ Multi-Business Context

VPS + HTTPS ───────────→ Twilio Webhooks
                       ──→ Payment Webhooks
                       ──→ Next.js Site
```

---
*Researched: 2026-03-14*
