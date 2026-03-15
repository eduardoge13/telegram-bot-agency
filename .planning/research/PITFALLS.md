# Pitfalls Research — Spike Agency Platform

**Researched:** 2026-03-14
**Confidence:** MEDIUM (training knowledge; verify critical claims against official docs)

## Critical Pitfalls

### 1. Twilio WhatsApp Production Approval Delay
**What:** Meta Business Manager verification for WhatsApp Business API takes 1-7+ days. Cannot send messages to non-sandbox numbers without it.
**Warning signs:** "Your WhatsApp sender is not approved" errors in production.
**Prevention:** Start the Twilio WhatsApp sender approval process on day 1, not at launch. Use sandbox for development in parallel.
**Phase:** Phase 1 (start immediately)

### 2. WhatsApp 24-Hour Session Window
**What:** Twilio/WhatsApp only allows free-form messages within 24 hours of customer's last message. After that, only pre-approved template messages can be sent.
**Warning signs:** "Message delivery failed" for returning customers after 24h.
**Prevention:** Design for template messages for proactive outreach (order updates, flight alerts). Free-form only within active conversations.
**Phase:** Phase 1 (WhatsApp bot design)

### 3. Twilio Webhook Signature Validation
**What:** Without validating `X-Twilio-Signature`, anyone can POST fake messages to your webhook endpoint.
**Warning signs:** Unexpected messages appearing, potential abuse.
**Prevention:** Use `twilio.webhook()` Express middleware on all webhook routes from day 1.
**Phase:** Phase 1 (WhatsApp bot)

### 4. MercadoPago Argentina vs Mexico Misconfiguration
**What:** MercadoPago ecosystem defaults to Argentina. A wrong-country access token routes payments to wrong account and shows wrong currency (ARS instead of MXN).
**Warning signs:** Prices showing in ARS, payment methods missing OXXO/SPEI, wrong merchant account.
**Prevention:** Verify access token is from Mexico marketplace. Test with a small real transaction early. Check `site_id` in API responses = `MLM` (Mexico).
**Phase:** Phase 2 (Payment checkout)

### 5. Stripe + MP Webhook Race Conditions
**What:** Both payment providers send webhooks for the same logical event. If both are active on one product, duplicate order fulfillment can occur.
**Warning signs:** Duplicate order entries in Google Sheets, customer charged twice.
**Prevention:** Idempotent webhook handlers. Use order ID as dedup key. Each order should only be fulfilled by one provider. Lock on checkout session ID.
**Phase:** Phase 2 (Payment webhooks)

### 6. Next.js Standalone Output Not Configured
**What:** Without `output: 'standalone'` in `next.config.ts`, Next.js expects the full `node_modules` directory. Deployment to VPS becomes a 500MB+ upload.
**Warning signs:** `next start` works locally but fails on VPS, or deployment is extremely slow.
**Prevention:** Add `output: 'standalone'` to `next.config.ts` before first VPS deploy. The standalone build is ~50MB.
**Phase:** Phase 2 (VPS deployment)

### 7. VPS Build Memory Exhaustion
**What:** `next build` on a VPS with limited RAM (512MB-1GB) can OOM kill the process.
**Warning signs:** Build process killed, exit code 137.
**Prevention:** Build locally or in CI, then `scp` the standalone build to VPS. Never build on production VPS.
**Phase:** Phase 2 (VPS deployment)

### 8. No PM2 Process Manager
**What:** Running `node` directly means services die on crash and don't restart. SSH session disconnect kills the process.
**Warning signs:** Services stop after SSH disconnect, no automatic restart after crashes.
**Prevention:** PM2 ecosystem file with `pm2 startup` for systemd integration. Auto-restart on crash.
**Phase:** Phase 2 (VPS deployment)

### 9. Multi-Tenant Context Bleed
**What:** If conversation routing is not keyed on `(businessId, customerPhone)` from the start, one business's context leaks into another's responses.
**Warning signs:** Tech store bot answering with travel agency context, or vice versa.
**Prevention:** Key all conversation state on composite key `${businessId}:${customerPhone}`. Never use global conversation state. Pass business context explicitly to every handler.
**Phase:** Phase 1 (WhatsApp bot architecture)

### 10. SSL Certificate Auto-Renewal Failure
**What:** Certbot certificates expire every 90 days. If auto-renewal fails, Twilio webhooks, Stripe webhooks, and MP webhooks ALL stop working simultaneously.
**Warning signs:** HTTPS errors start appearing after ~90 days.
**Prevention:** Certbot with `--deploy-hook` to reload nginx. Test renewal with `certbot renew --dry-run`. Set calendar reminder for 60-day check.
**Phase:** Phase 2 (VPS infrastructure)

## Moderate Pitfalls

### 11. Hardcoded Wrong WhatsApp Number (EXISTING)
**What:** `5215512345678` is hardcoded in `app/page.tsx:6` and `components/ProductCard.tsx:5`. This is a placeholder, not the real number.
**Prevention:** Replace with `5572408666` immediately. Consider moving to environment variable.
**Phase:** Immediate fix

### 12. Stripe API Version Mismatch (EXISTING)
**What:** `lib/stripe.ts` uses `@ts-expect-error` to suppress API version type error. The configured version may not match the SDK.
**Prevention:** Update API version string to match installed `stripe` package version, or remove the explicit version and let SDK use its default.
**Phase:** Phase 2 (Stripe checkout)

### 13. In-Memory Conversation State Lost on Restart
**What:** If WhatsApp bot stores conversation context in memory, PM2 restarts or deployments wipe all active conversations.
**Warning signs:** Customers get "I don't remember what we were talking about" after deploys.
**Prevention:** Use a simple file-based or Sheets-based conversation cache with TTL. Accept that some state loss on restart is OK for MVP.
**Phase:** Phase 1 (WhatsApp bot)

### 14. Google Sheets Rate Limits Under Multi-Channel Load
**What:** Google Sheets API allows ~100 requests/100 seconds per user. With both web (checkout) and bot (lookups) hitting Sheets, rate limits become real.
**Warning signs:** 429 errors from Google Sheets API.
**Prevention:** Add caching (node-cache, already used in Telegram bot). Batch reads where possible. Consider read replicas or local cache refresh interval.
**Phase:** Phase 1-2 (cross-cutting)

### 15. Nginx Timeout Too Short for AI/Amadeus
**What:** Default nginx `proxy_read_timeout` is 60s. Gemini API responses and Amadeus searches can take longer under load.
**Warning signs:** 504 Gateway Timeout errors on bot responses.
**Prevention:** Set `proxy_read_timeout 120s` for bot service routes in nginx config.
**Phase:** Phase 2 (VPS deployment)

### 16. MercadoPago Webhook Blocked by VPS Firewall
**What:** Hostinger VPS may have firewall rules that block incoming webhook POSTs from MP's IP ranges.
**Warning signs:** Payments succeed but webhook never arrives, orders never confirmed.
**Prevention:** Check Hostinger firewall settings. Allow inbound HTTPS from all IPs (or MP's documented IP ranges). Test webhook delivery with MP's webhook testing tool.
**Phase:** Phase 2 (Payments + VPS)

## Minor Pitfalls

### 17. Twilio Message Status Callbacks Not Handled
**What:** Twilio sends status updates (delivered, read, failed) but if not handled, you can't detect failed message delivery.
**Prevention:** Log status callbacks. Alert on repeated failures.
**Phase:** Phase 1 (nice-to-have)

### 18. Amadeus Access Token Expiry
**What:** Amadeus OAuth tokens expire every 30 minutes. SDK should handle refresh, but custom implementations may not.
**Prevention:** Use official `amadeus` npm SDK which handles token refresh automatically.
**Phase:** Phase 3-4 (Amadeus)

### 19. Next.js NEXT_PUBLIC_ Env Var Exposure
**What:** Any env var prefixed with `NEXT_PUBLIC_` is bundled into client JavaScript and visible to users.
**Warning signs:** Secret keys visible in browser dev tools.
**Prevention:** Only prefix with `NEXT_PUBLIC_` for truly public values (Stripe publishable key). Never for secret keys.
**Phase:** Phase 2 (Checkout)

### 20. Domain Required for SSL
**What:** Let's Encrypt can't issue certificates for raw IP addresses. Twilio and payment webhooks require HTTPS.
**Warning signs:** Certbot fails with "no domain name" error.
**Prevention:** Need a domain name pointing to VPS IP before setting up HTTPS. Can use a subdomain of an existing domain.
**Phase:** Phase 2 (VPS — must resolve before webhook setup)

---
*Researched: 2026-03-14*
