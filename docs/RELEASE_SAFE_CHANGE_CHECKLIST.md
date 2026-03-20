# Release Safe Change Checklist

Purpose: reduce side effects and keep core flows working during feature upgrades.

## 1) Requirement Lock

- Define exact domain meaning and unit (example: `remaining_credits` vs `remaining_days`).
- Record acceptance criteria in one sentence per behavior.
- Record non-goals to prevent accidental scope expansion.

## 2) Scope and Impact

- List files to change before coding.
- Mark shared modules separately (`api client`, auth, common UI runtime).
- Confirm backward-compatibility strategy for existing payload shapes.

## 3) Safe Implementation Rules

- Keep old behavior available as fallback defaults.
- Guard optional dependencies with `typeof fn === 'function'`.
- Accept schema variants (`data`, `items`, direct array) in UI readers.
- Clamp numeric rendering to safe ranges and fail closed on invalid input.

## 4) Pre-Deploy Gate

- Smoke check: `login -> target page load -> key action -> render result`.
- Error-path check: API unavailable case still renders fallback UI.
- Regression check: shared pages touched by common modules still open.

## 5) Deploy and Rollback

- Deploy preview first.
- Keep rollback target (previous deployment URL or commit SHA) ready.
- Rollback trigger rule: any broken core flow or error spike above baseline.

## 6) Post-Deploy Watch (first 30 minutes)

- Watch client console errors and API error-rate trend.
- Verify 3 user paths with real timestamps and screenshots.
- Close release only after monitoring window passes.

## Quick Sign-off Template

- Feature:
- Domain definition:
- Acceptance criteria:
- Changed files:
- Fallback strategy:
- Rollback target:
- Monitoring owner:
