# Conventions — spike-ecommerce-web

## Code Style
- TypeScript with strict mode
- Functional components only (no class components)
- 'use client' directive for interactive components
- Tailwind CSS utility classes inline (no CSS modules or styled-components)
- Single quotes for imports, template literals for dynamic strings

## Component Patterns
- Default exports for page and component files
- Props defined via TypeScript interfaces
- Next.js `Image` component for all images
- Inline Tailwind classes (long class strings, no extraction)

## Data Patterns
- Prices stored as integers in MXN cents (e.g., 2599900 = $25,999.00)
- `Intl.NumberFormat('es-MX')` for price display
- Static JSON for product data (no database)
- Path aliases: `@/` maps to project root

## Error Handling
- Minimal — no try/catch blocks in current code
- `@ts-expect-error` used to suppress Stripe API version mismatch
- Non-null assertions (`!`) on environment variables (will throw at runtime if missing)

## Spanish Language
- All UI copy in Spanish
- WhatsApp messages in Spanish
- Metadata in Spanish
- Code/variables in English

## Patterns Used
- URL-encoded WhatsApp links with pre-filled messages
- Auto-rotating slideshow with `setInterval`
- Responsive grid layouts (mobile-first)
- Gradient overlays for visual depth
