# Dashboard Implementation Note

Updated: 2026-03-07
Status: active
Scope: dashboard-style patterns shared across platform and Growth Automation surfaces

## 1. Purpose

This document explains how dashboard-style UI should be implemented in this codebase.
It is not a product spec.
It is an implementation note for layout, component hierarchy, and evidence presentation.

Linked docs:
- [docs/IA.md](/d:/Project/docs/IA.md)
- [web/RESPONSIVE_DESIGN_GUIDE_CLEAN.md](/d:/Project/web/RESPONSIVE_DESIGN_GUIDE_CLEAN.md)
- [docs/GROWTH_AUTOMATION_PARALLEL_UPDATE_2026-03-07.md](/d:/Project/docs/GROWTH_AUTOMATION_PARALLEL_UPDATE_2026-03-07.md)

## 2. Shared Dashboard Pattern

Every dashboard-like screen should be composed from these layers:

1. Context block
2. KPI summary block
3. Filter and action block
4. Compare or trend block
5. Evidence table block
6. Detail panel block

If a screen removes one of these layers, the reason should be explicit in the IA.

## 3. Component Guidelines

### 3.1 Hero / Context block

- state what the screen is for
- explain the operator task in one or two sentences
- contain navigation if the page belongs to a multi-page console

### 3.2 KPI summary cards

- prioritize fast scanning over decoration
- use tone or accent to communicate operational meaning
- should not require charts to understand the current state

### 3.3 Filter chips

- represent a small number of meaningful presets
- should immediately change the data shown on screen
- must expose active state clearly

### 3.4 Compare cards

- compare current state against a baseline or target
- include label, current value, trend hint, and a compact visual bar
- should answer "is this healthy?" without opening another page

### 3.5 Evidence tables

- are the source of truth for operational inspection
- should use sticky headers when long
- should support row selection when detail context matters

### 3.6 Detail panels

- should explain the selected row without leaving the page
- should show the fields needed for a decision, not every field in the payload

## 4. Growth Automation Mapping

These dashboard patterns now map directly onto Growth Automation:

- Hub
  - context + simulator + KPI + recommendation + evidence
- Contacts
  - KPI + compare + saved filters + list + contact detail panel
- Journeys
  - state cards + compare + saved filters + evidence + journey detail panel
- Ops
  - severity cues + compare + saved filters + evidence + recovery detail panels

## 5. Visual Hierarchy Rules

- recommendation and compare surfaces should sit above raw evidence
- evidence tables should not visually overpower the summary layer
- danger and warning tones should be reserved for actual operational risk
- selection states must be visible but should not dominate the entire table

## 6. Frontend / Backend Balance

Dashboard screens in this codebase should keep a balanced contract:

- Frontend side
  - layout hierarchy
  - component meaning
  - interaction flow
  - responsive interpretation
- Backend side
  - payload shape
  - evidence fields
  - state and transition source of truth
  - recovery and error semantics

If either side dominates the document, the screen becomes harder to implement correctly.

## 7. Current Implementation Note

As of 2026-03-07, the Growth Automation pages already implement:

- summary cards with operational tone
- recommendation and action zones
- selectable tables with detail panels
- severity badges for operations
- saved filters for fast operator slicing
- compare cards with simple baseline references

## 8. Next Upgrade Direction

The next dashboard-level improvements should focus on:

- historical trend indicators
- deeper cohort comparison against real baselines
- browser-session smoke checks for interaction flows
