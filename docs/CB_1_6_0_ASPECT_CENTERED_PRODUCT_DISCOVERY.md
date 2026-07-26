# CB-1.6.0 — Aspect-Centered Product Discovery

## Goal

Product discovery is centered on the requested aspect, not on a single product category.
A broad request such as “что-нибудь с Калачакрой” may return statues, thangkas,
stickers, and other catalog products connected with that aspect.

When the visitor explicitly names both an aspect and a product type, both facets are
applied. For example, “тханки Калачакры” returns only thangkas connected with
Калачакра.

## Design

- Product type and aspect remain independent search facets.
- A broad aspect request does not manufacture a product-type restriction.
- Collection cards expose their source category for presentation and grouping.
- Generic request words are excluded from lexical constraints.
- No special branch is added for a particular user phrase.
