# Stack — spike-ecommerce-web

## Runtime & Language
- **Runtime:** Node.js
- **Language:** TypeScript 5.x
- **Framework:** Next.js 16.1.6 (App Router)
- **React:** 19.2.3

## Frontend
- **Styling:** Tailwind CSS 4.x (via PostCSS)
- **Fonts:** Google Fonts (Syne for display, Outfit for body)
- **Images:** Next.js `Image` component for optimization
- **Locale:** Spanish (es) — Mexico market

## Payment SDKs
- **Stripe:** `stripe` ^20.4.0 (server), `@stripe/stripe-js` ^8.9.0 (client)
- **Mercado Pago:** `mercadopago` ^2.12.0

## Dev Dependencies
- ESLint 9 + eslint-config-next
- TypeScript ^5
- @tailwindcss/postcss ^4
- @types/node, @types/react, @types/react-dom

## Configuration Files
- `next.config.ts` — Empty/default config
- `tsconfig.json` — Standard Next.js TypeScript config
- `postcss.config.mjs` — Tailwind PostCSS plugin
- `eslint.config.mjs` — ESLint flat config

## Environment Variables (from .env.example)
- `STRIPE_SECRET_KEY` — Stripe server-side key
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` — Stripe client-side key
- `MERCADOPAGO_ACCESS_TOKEN` — Mercado Pago server token

## Deployment Target
- Vercel (recommended in docs)
- No deployment config present yet
