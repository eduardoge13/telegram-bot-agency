# Integrations — spike-ecommerce-web

## Payment Providers

### Stripe
- **Config:** `lib/stripe.ts`
- **Status:** SDK initialized, no checkout flow implemented yet
- **API Version:** 2024-12-18.acacia (with ts-expect-error for version mismatch)
- **Usage:** Server-side only via `STRIPE_SECRET_KEY`
- **Missing:** Checkout session creation, webhook handler, success/cancel pages

### Mercado Pago
- **Config:** `lib/mercadopago.ts`
- **Status:** SDK initialized with Preference client, no checkout flow implemented
- **Usage:** Server-side via `MERCADOPAGO_ACCESS_TOKEN`
- **Missing:** Preference creation endpoint, webhook handler, IPN notifications

## WhatsApp (Primary Sales Channel)
- **Type:** Direct links via `wa.me` API
- **Number:** Hardcoded `5215512345678` (placeholder) in both `app/page.tsx` and `components/ProductCard.tsx`
- **Flow:** Product-specific pre-filled messages → WhatsApp conversation
- **Status:** Active and working as primary conversion channel

## Data Sources
- **Products:** Static JSON file (`data/products.json`) — no database
- **Product helpers:** `lib/products.ts` — getAllProducts, getProductById, getProductsByCategory

## External APIs
- No external API calls beyond payment SDK initialization
- No database connections
- No auth providers
- No webhooks configured yet

## Missing Integrations (from dev log roadmap)
- Stripe checkout session API route
- Mercado Pago preference API route
- Webhook handlers for both payment providers
- Order confirmation flow
- Analytics
