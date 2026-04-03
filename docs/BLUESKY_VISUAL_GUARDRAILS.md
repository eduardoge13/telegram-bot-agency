# Blue Sky Travel Visual Guardrails

Date: 2026-04-02

This document defines how Blue Sky Travel should avoid generic "vibe-coded" web visuals and move toward a credible premium travel brand. It is meant to guide homepage revisions, asset selection, copy, layout, motion, and proof strategy.

## Goal

Build a site that feels:

- premium, not templated
- human, not AI-generated
- specific to Blue Sky Travel, not interchangeable with any agency
- clear enough to convert on mobile through WhatsApp
- credible enough to support Meta go-live and live sales

## Research Summary

### 1. Trust is visual before it is verbal

Baymard's usability guidance is consistent on this point: credibility is a first-order usability requirement. A site can be attractive and still fail if it does not feel trustworthy or relevant to the user's goal.

Practical implication for Blue Sky Travel:

- visible contact information matters
- a strong primary task matters
- mobile usability matters
- visual polish must support trust, not distract from it

Relevant sources:

- [Baymard: Website Usability Best Practices](https://baymard.com/learn/website-usability)
- [Baymard: UX Principles](https://baymard.com/learn/ux-design-principles)
- [Nielsen Norman Group: Presenting Company Information on Corporate Websites](https://media.nngroup.com/media/reports/free/Presenting_Company_Information_on_Corporate_Websites_3rd_Edition.pdf)

### 2. Travel buyers distrust self-curated praise

Baymard's travel-site research found that curated testimonials on a site's own homepage are often treated as biased. Users place more weight on proof they can verify externally.

Practical implication for Blue Sky Travel:

- do not fill the homepage with invented or unverified testimonials
- prefer real review sources, partner marks, response-time claims you can support, or concrete operating proof
- if testimonials are used, they should be attributable, sparse, and ideally paired with third-party verification

Relevant source:

- [Baymard: Travel Site UX Best Practices](https://baymard.com/blog/travel-site-ux-best-practices)

### 3. Authenticity beats polished genericity

Adobe's 2025 and 2026 creative guidance points in the same direction: authenticity, local culture, warmth, documentary imagery, human-centered imperfection, and freeform storytelling are increasingly preferred over sterile high-tech polish.

Practical implication for Blue Sky Travel:

- use real travel imagery tied to actual destinations, clients, or brand context
- avoid the "floating gradient blob + generic luxury copy + stock people smiling at laptops" pattern
- favor editorial layouts, local cues, and lived-in details over over-produced abstractions

Relevant sources:

- [Adobe: Harnessing the power of brand culture and heritage](https://blog.adobe.com/en/publish/2025/03/13/harnessing-power-of-brand-culture-heritage)
- [Adobe Express: Design trends for 2026](https://www.adobe.com/express/learn/blog/design-trends-2026)

### 4. Strong brands show who they are, not just what they sell

Both Adobe's brand-culture guidance and NNGroup's company-information guidance align on a core point: people trust brands more when the site clearly signals identity, community ties, contact routes, and operational legitimacy.

Practical implication for Blue Sky Travel:

- the brand should present a real business identity
- the site should show who handles inquiries, how to get in touch, and what type of travel work is actually done
- the homepage should feel tied to a point of view, not assembled from generic travel-agent modules

Relevant sources:

- [Adobe: Harnessing the power of brand culture and heritage](https://blog.adobe.com/en/publish/2025/03/13/harnessing-power-of-brand-culture-heritage)
- [Nielsen Norman Group: Presenting Company Information on Corporate Websites](https://media.nngroup.com/media/reports/free/Presenting_Company_Information_on_Corporate_Websites_3rd_Edition.pdf)

### 5. Travel privacy pages that feel credible are specific

Peer travel brands in Mexico and the U.S. do not keep privacy pages vague. They typically specify:

- responsible party or legal entity
- contact channels
- categories of data collected
- business purposes
- sharing or third-party processor categories
- cookies or technical tracking
- rights or request channels
- change notices and last-updated dates

Observed peer patterns:

- [PriceTravel aviso de privacidad](https://www.pricetravel.com.mx/info/aviso-privacidad/) is explicit about the responsible entity, address, categories of data, purposes, transfers, cookies, and updates.
- [Expedia Group Legal Center](https://legal.expediagroup.com/privacy) separates privacy principles, rights, cookies, transfers, and subprocessors into clearly navigable sections.

Practical implication for Blue Sky Travel:

- the privacy page must be legally specific before production
- placeholders are acceptable only in staging
- Meta should receive the stable production privacy URL only after the final legal details are inserted

## Anti-Vibecode Rules

These rules apply to all future homepage and landing-page work.

### 1. No generic hero in production

Do not ship a production hero that relies only on:

- gradients
- abstract blobs
- empty luxury adjectives
- AI-looking travel collages
- faceless stock scenes with no brand connection

Production hero requirements:

- one real destination-led image or a strong branded editorial composition
- one concrete promise
- one primary CTA
- one proof cluster that signals legitimacy

### 2. Use real photography or clearly intentional illustration

Preferred asset order:

1. Blue Sky Travel's own travel photography
2. licensed editorial-style travel imagery with a documentary feel
3. bespoke illustration or graphic treatment that is obviously intentional

Avoid:

- over-smoothed AI-looking skies
- generic stock "call center" people
- mixed-image sets with inconsistent color temperature, geography, or tone
- images that could belong to any resort affiliate page

### 3. Show proof that can survive scrutiny

Allowed proof types:

- real partner affiliations
- verified review-platform links
- real WhatsApp response expectations
- specific service areas
- specific destination expertise
- real company location or operating footprint

Avoid:

- anonymous five-star quotes
- inflated counters without a source
- generic badge walls
- fake urgency copy

### 4. Make the layout feel authored

To avoid AI-template energy, the page needs clear compositional decisions:

- vary rhythm between wide sections, split layouts, and editorial blocks
- use at least one section that breaks the default card-grid pattern
- let type do real work instead of wrapping every message in a box
- use spacing and hierarchy intentionally instead of stacking modules mechanically

Avoid:

- eight sections in a row that all look structurally identical
- every block being a rounded card
- repetitive three-column grids without narrative progression

### 5. Typography must carry brand tone

Typography rules:

- use a pair with character, not a default startup stack
- let the display type establish travel/editorial tone
- keep body copy readable and restrained
- preserve hierarchy consistency across both languages

Avoid:

- oversized marketing copy with no supporting detail
- random font shifts
- all-caps overload
- decorative scripts without a strong brand reason

### 6. Motion should be restrained and deliberate

Allowed motion:

- one page-load reveal pattern
- subtle section parallax or image drift only if performance remains strong
- CTA and hover states that feel tactile

Avoid:

- autoplay video unless it adds clear brand value
- layered animations on every block
- motion that competes with reading
- scroll gimmicks that feel like an agency demo reel

### 7. Mobile is not a compressed desktop poster

Mobile rules:

- CTA visible early
- no hero copy wall
- cards must stack cleanly
- legal/contact links stay accessible
- no cramped nav or over-designed desktop-only composition

If the site looks premium on desktop but generic or broken on mobile, it is not ready.

### 8. Local and bilingual means more than translation

Spanish and English versions should preserve tone, not just meaning.

Rules:

- use proper accents in Spanish
- adapt phrasing to how travel services are actually sold in each language
- avoid machine-translated stiffness
- keep destination, culture, and service language grounded in real usage

### 9. Legal trust must be visible, not buried

For a travel brand selling via WhatsApp, trust cues should be visible in the layout:

- privacy policy
- terms
- data deletion route
- business contact information
- real email addresses and WhatsApp channel

This is both a legal requirement and a design requirement.

## Phase 1 Implementation Rules

These rules apply directly to the current Astro site.

### Homepage

- Keep one dominant CTA: WhatsApp.
- Add one stronger visual anchor before production: real destination photography or branded editorial artwork.
- Replace any generic testimonial block with verifiable proof if/when proof is added.
- Preserve visible legal/footer links.
- Keep the homepage concise enough that the CTA remains visible within the first scroll on mobile.

### Privacy page

- Must include final legal entity, address, and privacy contact before production.
- Must remain accessible at `/privacy-policy`.
- Must not be replaced by a PDF-only flow.

### Terms and data deletion pages

- Keep them public and linked in the footer.
- Keep contact instructions explicit.
- Treat them as trust pages, not boilerplate dumping grounds.

### Assets required before production cutover

- final logo or wordmark
- final legal entity name
- final business address
- final privacy contact email if different
- one strong hero image set
- optional but recommended: one real proof source such as Google reviews, TripAdvisor, or supplier affiliations

## Current Design Gaps

As of this document, the current Phase 1 site structure is sound, but it still needs production-grade brand specificity in these areas:

- real imagery
- final legal identity
- Spanish copy polish with full accents and final editorial cleanup
- stronger proof elements based on real business assets

That means the site is acceptable for staging, but not yet for final production polish.

## Development Checklist

Use this before approving any Blue Sky Travel visual revision.

- Is the hero unmistakably tied to travel and to this brand?
- Is the primary CTA obvious within seconds?
- Does the page show real contact and legal identity?
- Does any proof on the page survive a skeptical user?
- Does the mobile view still feel premium?
- Does the Spanish copy read like native Spanish, not placeholder Spanish?
- Does the page still feel distinct if the gradients are removed?
- Would this design still make sense if someone saw it without animations?

If any answer is no, it is not ready.
