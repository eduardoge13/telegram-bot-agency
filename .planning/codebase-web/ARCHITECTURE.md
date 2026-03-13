# Architecture — spike-ecommerce-web

## Pattern
Single-page landing site using Next.js App Router. Currently a marketing/catalog page with WhatsApp as the primary sales channel. Payment integrations (Stripe, Mercado Pago) are initialized but not wired into any checkout flow.

## Layers

### Presentation Layer
- `app/page.tsx` — Single page, client component ('use client'), contains entire landing page
- `app/layout.tsx` — Root layout with fonts (Syne, Outfit) and metadata
- `components/ProductCard.tsx` — Reusable product card (currently unused on homepage, available for catalog page)

### Data Layer
- `data/products.json` — Static product catalog (3 products: iPhone 17 Pro Max, iPhone 16, Sonos ERA 100)
- `lib/products.ts` — Product query helpers (getAllProducts, getProductById, getProductsByCategory)
- `types/product.ts` — Product and CartItem TypeScript interfaces

### Integration Layer (Stub)
- `lib/stripe.ts` — Stripe SDK initialization only
- `lib/mercadopago.ts` — Mercado Pago SDK + Preference client initialization only

## Data Flow
1. Products defined in `data/products.json` (prices in MXN cents)
2. Homepage has hardcoded product slides (not reading from products.json)
3. User clicks "Comprar por WhatsApp" → opens WhatsApp with pre-filled message
4. No cart, no checkout, no order processing exists yet

## Entry Points
- `app/page.tsx` — Only page in the app
- No API routes exist yet

## Key Observations
- The homepage (`app/page.tsx`) is a single 300-line client component with everything inline
- Product data is duplicated: slides array in page.tsx AND products.json
- ProductCard component exists but isn't used by the homepage (it was built for a future catalog page)
- CartItem type exists but no cart functionality is implemented
- Brand: "Punto Clave MX" — Mexican tech e-commerce
