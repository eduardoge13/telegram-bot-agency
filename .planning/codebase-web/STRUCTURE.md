# Structure — spike-ecommerce-web

## Directory Layout

```
spike-ecommerce-web/
├── app/
│   ├── globals.css          # Tailwind imports + custom styles
│   ├── layout.tsx           # Root layout (fonts, metadata)
│   └── page.tsx             # Homepage (single-page landing)
├── components/
│   └── ProductCard.tsx      # Reusable product card component
├── data/
│   └── products.json        # Static product catalog (3 items)
├── docs/
│   ├── CLIENT_CHECKLIST.md  # Client onboarding checklist
│   ├── DEVELOPMENT_LOG.md   # Session-based dev log
│   ├── LANDING_PROGRESS_2026-03-09.md
│   └── SETUP_GUIDE.md       # Setup instructions
├── lib/
│   ├── mercadopago.ts       # Mercado Pago SDK init
│   ├── products.ts          # Product query helpers
│   └── stripe.ts            # Stripe SDK init
├── public/
│   ├── logo.jpeg            # Brand logo
│   └── products/            # Product images (JPEGs)
├── types/
│   └── product.ts           # Product & CartItem interfaces
├── next.config.ts           # Next.js config (empty)
├── package.json
├── tsconfig.json
├── postcss.config.mjs
└── eslint.config.mjs
```

## Key Locations
- **Pages:** `app/` (only homepage exists)
- **Components:** `components/` (only ProductCard)
- **Data/Models:** `types/product.ts`, `data/products.json`
- **Services:** `lib/` (stripe, mercadopago, products)
- **Static Assets:** `public/` (logo, product images)
- **Documentation:** `docs/`

## Naming Conventions
- PascalCase for components: `ProductCard.tsx`
- camelCase for lib modules: `mercadopago.ts`, `products.ts`
- kebab-case for data files: `products.json`
- Flat structure — no nested directories within app/
