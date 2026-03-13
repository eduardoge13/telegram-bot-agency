# Concerns — spike-ecommerce-web

## Critical

### 1. No Checkout Flow Exists
- Stripe and Mercado Pago SDKs are initialized but **no checkout routes or flows exist**
- No API routes for creating payment sessions
- No webhook handlers for payment confirmations
- No order confirmation or success/failure pages
- **Impact:** The site cannot process payments — WhatsApp is the only sales channel

### 2. Hardcoded WhatsApp Number (Placeholder)
- `WHATSAPP_NUMBER = '5215512345678'` is hardcoded in two files:
  - `app/page.tsx:6`
  - `components/ProductCard.tsx:5`
- This is a placeholder, not a real number
- **Impact:** WhatsApp links won't reach the actual business

### 3. Duplicated Product Data
- Product slides are hardcoded in `app/page.tsx` (lines 8-36) with prices, images, messages
- Same products exist in `data/products.json`
- These can drift out of sync
- **Impact:** Price/availability changes need updates in two places

## High

### 4. No Environment Variable Validation
- `process.env.STRIPE_SECRET_KEY!` and `process.env.MERCADOPAGO_ACCESS_TOKEN!` use non-null assertions
- No runtime validation, no graceful fallback
- **Impact:** App crashes at import time if env vars are missing

### 5. Stripe API Version Mismatch
- `lib/stripe.ts` uses `@ts-expect-error` to suppress API version type error
- The configured API version may not match the installed SDK version
- **Impact:** Potential runtime issues when Stripe APIs are eventually used

### 6. Single-File Homepage (300+ lines)
- `app/page.tsx` contains the entire landing page as one component
- Header, hero, slides, benefits, products, how-it-works, CTA — all inline
- **Impact:** Hard to maintain, hard to iterate on individual sections

## Medium

### 7. No Cart Implementation
- `CartItem` type exists in `types/product.ts` but no cart state, context, or UI
- No "Add to Cart" functionality anywhere
- **Impact:** Cart-based checkout can't work until this is built

### 8. No Database
- All product data is in a static JSON file
- No inventory tracking, no order storage
- **Impact:** Scaling beyond a few products requires a data layer

### 9. ProductCard Component Unused
- `components/ProductCard.tsx` is built but not imported anywhere
- Homepage uses inline product slides instead
- **Impact:** Dead code, potential confusion about which component to use

### 10. No SEO Beyond Basic Metadata
- Only title and description in layout metadata
- No Open Graph, no Twitter cards, no structured data
- No sitemap, no robots.txt
- **Impact:** Poor discoverability for an e-commerce site

### 11. No Error Boundaries or Loading States
- No error.tsx or loading.tsx files
- No skeleton loaders or fallback UI
- **Impact:** Poor UX if anything fails

## Security

### 12. No Input Sanitization
- WhatsApp messages are URL-encoded but no other sanitization exists
- No CSP headers configured
- **Impact:** Low risk currently (no user input forms), but relevant when checkout is added

## Technical Debt Summary
- The codebase is an early-stage landing page that was planned for full e-commerce but pivoted to WhatsApp-based sales
- Payment integrations are stubs — initialized but never used
- The gap between "what's built" (landing page) and "what was planned" (full e-commerce with cart/checkout) is significant
