# Phase 1: Site + Infrastructure - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the Punto Clave MX e-commerce site (WhatsApp number, design improvements, SPEI payment option) and deploy it to the Hostinger VPS (72.60.228.135) with Docker, nginx, and HTTPS.

</domain>

<decisions>
## Implementation Decisions

### Deployment Approach
- Use Docker (docker-compose) — consistent with existing clinic system on the VPS
- Plan for nginx possibly already running (check on VPS) — add site config either way
- Next.js configured with `output: 'standalone'` for containerized deployment
- Dockerfile for Next.js standalone build

### Deploy Workflow
- Push to GitHub, SSH into VPS, git pull, docker-compose up
- Build happens inside Docker container on VPS (or multi-stage Dockerfile)
- No CI/CD for MVP — manual deploy is fine

### Site Changes — WhatsApp Number
- Replace placeholder `5215512345678` with `5572408666` in:
  - `app/page.tsx` (line 6)
  - `components/ProductCard.tsx` (line 5)

### Site Changes — SPEI Bank Transfer Option
- Add a "Pago por Transferencia" section with SPEI logo for trust
- Display a placeholder CLABE account number for the client's bank account
- This gives customers a direct bank transfer option alongside WhatsApp ordering
- SPEI is widely trusted in Mexico — showing the logo builds credibility

### Site Changes — Design Improvements
- Act as a professional web designer — make improvements that increase conversion and trust
- Improve overall selling points, visual hierarchy, and call-to-action effectiveness
- Ensure the site looks premium and trustworthy for a Mexican tech e-commerce brand
- Fix any UX issues found during implementation (product data duplication, unused components, etc.)

### Claude's Discretion
- Exact Docker/docker-compose configuration
- nginx site config details
- SSL/Certbot setup approach
- Specific design improvements (typography, spacing, sections, layout refinements)
- Whether to extract homepage sections into reusable components
- How to handle the SPEI/CLABE display (modal, section, footer, etc.)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `components/ProductCard.tsx`: Built but unused on homepage — could be integrated for a proper product grid
- `lib/products.ts`: Product query helpers (getAllProducts, getProductById, getProductsByCategory)
- `data/products.json`: Static product catalog with 3 products (prices in MXN cents)
- `types/product.ts`: Product and CartItem TypeScript interfaces

### Established Patterns
- Tailwind CSS 4.x for styling (utility-first)
- Next.js App Router with 'use client' for interactive components
- Google Fonts: Syne (display) + Outfit (body)
- Spanish language throughout — all UI copy in Spanish
- WhatsApp links via `wa.me` with encoded pre-filled messages

### Integration Points
- `next.config.ts`: Currently empty — needs `output: 'standalone'` added
- Product data duplicated: hardcoded slides in page.tsx AND products.json — should consolidate
- WhatsApp number hardcoded in 2 files — should ideally be a constant or env var

</code_context>

<specifics>
## Specific Ideas

- SPEI logo displayed prominently near payment/trust section to build credibility
- CLABE account number visible for direct bank transfers (placeholder from client)
- Design should feel premium — "Punto Clave MX" is a Mexican tech e-commerce brand
- User wants professional web designer quality improvements to maximize conversion

</specifics>

<deferred>
## Deferred Ideas

- Stripe/Mercado Pago checkout flows — v2 (payment accounts not set up yet)
- Cart functionality — v2
- Product detail pages — v2

</deferred>

---

*Phase: 01-site-infrastructure*
*Context gathered: 2026-03-14*
