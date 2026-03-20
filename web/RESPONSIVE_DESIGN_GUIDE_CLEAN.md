# Responsive Design Guide

Updated: 2026-03-07
Status: active
Scope: all web surfaces, with special alignment to Growth Automation

## 1. Purpose

This guide defines how SoftFactory web pages should adapt across device sizes.
It is the implementation-side companion to the Growth Automation IA document.

Primary linked docs:
- [docs/IA.md](/d:/Project/docs/IA.md)
- [web/platform/DASHBOARD_IMPLEMENTATION_CLEAN.md](/d:/Project/web/platform/DASHBOARD_IMPLEMENTATION_CLEAN.md)
- [docs/GROWTH_AUTOMATION_PARALLEL_UPDATE_2026-03-07.md](/d:/Project/docs/GROWTH_AUTOMATION_PARALLEL_UPDATE_2026-03-07.md)

## 2. Breakpoints

- Mobile: under `640px`
- Tablet: `640px` to `1023px`
- Desktop: `1024px` to `1439px`
- Wide: `1440px` and above

Rule:
- start from a one-column mobile layout
- expand density only when the content still remains readable

## 3. Layout Rules

### 3.1 Core structure

Every operational page should keep this order:

1. Hero or context block
2. Summary or KPI layer
3. Action or filter layer
4. Evidence tables or detail panels

### 3.2 Grid behavior

- Mobile: stack everything into one column
- Tablet: allow two-column content where the left and right panels are equally important
- Desktop: allow asymmetric grids when one panel is clearly primary
- Wide: increase breathing room before increasing information density

### 3.3 Table behavior

- horizontal scrolling is acceptable for operational evidence tables
- sticky table headers should be used when tables can extend vertically
- detail panels should appear below tables on smaller screens

## 4. Touch and Input Rules

- minimum tappable area: `44x44px`
- minimum gap between interactive controls: `8px`
- primary actions should remain visible without requiring precise pointer targeting
- search and filter controls should remain full width on mobile

## 5. Typography and Readability

- do not shrink body text below readable mobile sizes
- use short labels for chips, badges, and controls
- heading scale should create hierarchy without forcing extra scrolling
- explanatory copy should be one or two sentences, not paragraphs of prose

## 6. Component Contracts

### KPI cards

- should wrap cleanly from 4-5 columns to 2 columns to 1 column
- should preserve emphasis color or tone at every breakpoint

### Filter chips

- should wrap across rows without horizontal overflow
- should preserve active state clearly

### Compare cards

- should collapse from 3-up to 1-up on narrow screens
- should preserve label, value, and trend line in that order

### Detail panels

- should move below the primary evidence table on tablet and mobile
- should not rely on hover-only affordances

## 7. Growth Automation Interpretation

Growth Automation pages use this guide in a specific way:

- Hub
  - hero and simulator can split into two columns on desktop
  - recommendation and evidence blocks should stack on mobile
- Contacts
  - composer and table split on desktop, stack on tablet/mobile
  - saved filters and segment chips should wrap naturally
- Journeys
  - simulator and action guidance can sit side-by-side on desktop
  - stage cards and compare cards should collapse aggressively on mobile
- Ops
  - two-panel evidence layout is acceptable on desktop
  - detail panels must remain readable below each table on narrow screens

## 8. Accessibility Baseline

- maintain WCAG 2.1 AA contrast targets
- preserve keyboard focus visibility
- do not hide critical labels inside placeholders only
- keep semantic heading order intact

## 9. Synchronization Rule

When Growth Automation layout changes materially, update both:

1. [docs/IA.md](/d:/Project/docs/IA.md)
2. this document or [web/platform/DASHBOARD_IMPLEMENTATION_CLEAN.md](/d:/Project/web/platform/DASHBOARD_IMPLEMENTATION_CLEAN.md)

## 10. Current Alignment Note

As of 2026-03-07, this guide is aligned with the following implemented patterns:

- summary cards with operational tone
- selectable evidence tables with detail panels
- saved filter chips
- compare cards with baseline and trend hints
- sticky table headers for operational evidence
