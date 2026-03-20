# Parallel Upgrade Execution Plan (2026-03-05)

## Goal
- Organize parallel development into fixed agent ownership.
- Produce a completion summary for each run.
- Persist an append-only execution history.

## Scope
- `web/platform`
- `web/review`
- `web/bohemian-marketing`
- `web/coocook`
- `web/ai-automation`
- `web/webapp-builder`
- `web/instagram-cardnews`
- `web/sns-auto`
- `web/marketplace`
- `web/experience`
- `web/admin`

## Completion Rules
- One task can be marked complete only when implementation, UX review, and docs update are all done.
- Every run must emit:
- `summary.json`
- `README.md`
- `run_results.json` and `run_results.csv` (run mode only)
- `COMPLETION_SUMMARY.md` (run mode only)
- Every run must append:
- `docs/plans/execution/execution_history.jsonl`
- `docs/plans/execution/EXECUTION_HISTORY.md`

## Agent Backlog (10x10)

### A01 Navigation and IA
- [ ] A01-T01 Define canonical sidebar tree schema.
- [ ] A01-T02 Build shared sidebar renderer.
- [ ] A01-T03 Normalize active route highlighting.
- [ ] A01-T04 Add breadcrumb standard.
- [ ] A01-T05 Add mobile drawer behavior.
- [ ] A01-T06 Add section grouping rules.
- [ ] A01-T07 Add menu search.
- [ ] A01-T08 Add role-based menu filtering placeholders.
- [ ] A01-T09 Add nav fallback when config fails.
- [ ] A01-T10 Migrate all target pages to shared nav.

### A02 Korean Content and Text Quality
- [ ] A02-T01 Normalize page titles in Korean.
- [ ] A02-T02 Normalize button labels in Korean.
- [ ] A02-T03 Normalize validation and error messages.
- [ ] A02-T04 Normalize KPI and chart labels.
- [ ] A02-T05 Normalize tooltip and helper copy.
- [ ] A02-T06 Normalize aria-label text in Korean.
- [ ] A02-T07 Normalize date/time locale output to `ko-KR`.
- [ ] A02-T08 Normalize number formatting and units.
- [ ] A02-T09 Build untranslated text checklist.
- [ ] A02-T10 Apply final terminology glossary.

### A03 Encoding and Corruption Recovery
- [ ] A03-T01 Recover corrupted text in `web/experience/index.html`.
- [ ] A03-T02 Recover corrupted text in `web/marketplace/index.html`.
- [ ] A03-T03 Recover corrupted title/meta tags.
- [ ] A03-T04 Remove malformed HTML fragments.
- [ ] A03-T05 Add encoding check helper script.
- [ ] A03-T06 Normalize file encoding to UTF-8.
- [ ] A03-T07 Add regression checklist for corrupted strings.
- [ ] A03-T08 Patch mixed-encoding edge cases.
- [ ] A03-T09 Add pre-deploy encoding gate.
- [ ] A03-T10 Document encoding policy.

### A04 Design System Consistency
- [ ] A04-T01 Define global color token set.
- [ ] A04-T02 Define typography scale.
- [ ] A04-T03 Standardize panel/card visual style.
- [ ] A04-T04 Standardize button variants.
- [ ] A04-T05 Standardize form control styles.
- [ ] A04-T06 Standardize status badge styles.
- [ ] A04-T07 Standardize spacing and layout rhythm.
- [ ] A04-T08 Standardize motion and loading patterns.
- [ ] A04-T09 Remove conflicting page-local overrides.
- [ ] A04-T10 Publish design consistency checklist.

### A05 Responsive and Mobile UX
- [ ] A05-T01 Rebalance breakpoint behavior (320 to 1440).
- [ ] A05-T02 Optimize sidebar for mobile.
- [ ] A05-T03 Optimize KPI card wrapping on mobile.
- [ ] A05-T04 Provide table-to-card fallback pattern.
- [ ] A05-T05 Improve touch target sizes.
- [ ] A05-T06 Fix chart resizing in narrow viewports.
- [ ] A05-T07 Reduce layout shift on initial load.
- [ ] A05-T08 Improve bottom action area on mobile.
- [ ] A05-T09 Improve orientation switch handling.
- [ ] A05-T10 Document responsive QA matrix.

### A06 Accessibility and Semantic Structure
- [ ] A06-T01 Add skip links consistently.
- [ ] A06-T02 Normalize semantic landmarks.
- [ ] A06-T03 Normalize keyboard navigation order.
- [ ] A06-T04 Normalize focus visibility behavior.
- [ ] A06-T05 Improve color contrast compliance.
- [ ] A06-T06 Add missing aria attributes.
- [ ] A06-T07 Improve form label associations.
- [ ] A06-T08 Add live-region messaging for status.
- [ ] A06-T09 Add accessibility smoke checklist.
- [ ] A06-T10 Publish a11y regression protocol.

### A07 Platform and Review Product Features
- [ ] A07-T01 Stabilize platform KPI data bindings.
- [ ] A07-T02 Standardize loading/empty/error states.
- [ ] A07-T03 Improve review campaign filtering.
- [ ] A07-T04 Improve review application workflow states.
- [ ] A07-T05 Add bulk actions for campaign management.
- [ ] A07-T06 Improve dashboard quick actions.
- [ ] A07-T07 Improve notification center consistency.
- [ ] A07-T08 Improve report export behavior.
- [ ] A07-T09 Improve list performance for large data.
- [ ] A07-T10 Align platform-review navigation experience.

### A08 Automation Modules
- [ ] A08-T01 Build staged pipeline UI in webapp-builder.
- [ ] A08-T02 Add requirement-to-deploy stage tracking.
- [ ] A08-T03 Add queue/worker status panel.
- [ ] A08-T04 Improve cardnews template CRUD.
- [ ] A08-T05 Improve cardnews canvas editor controls.
- [ ] A08-T06 Improve multi-account posting queue.
- [ ] A08-T07 Add run safety limits and approvals.
- [ ] A08-T08 Add retry and recovery flow.
- [ ] A08-T09 Unify automation APIs across modules.
- [ ] A08-T10 Add automation runbook for operators.

### A09 Data/API/DB Reliability
- [ ] A09-T01 Validate production DB schema parity.
- [ ] A09-T02 Separate local and production DB configs.
- [ ] A09-T03 Improve seed data for real service scenarios.
- [ ] A09-T04 Standardize API error payloads.
- [ ] A09-T05 Standardize auth token lifecycle handling.
- [ ] A09-T06 Add idempotency protections in job flows.
- [ ] A09-T07 Improve queue state persistence.
- [ ] A09-T08 Improve audit log completeness.
- [ ] A09-T09 Improve analytics aggregation reliability.
- [ ] A09-T10 Document migration and rollback process.

### A10 Deployment and Operations
- [ ] A10-T01 Keep deployment secret checks fail-fast.
- [ ] A10-T02 Keep Vercel access policy and 401 guide current.
- [ ] A10-T03 Add Render UTF-8 build gate for frontend files.
- [ ] A10-T04 Standardize static asset paths for deployment.
- [ ] A10-T05 Maintain `.env.example` with required variables.
- [ ] A10-T06 Add pre-deploy nav/link verification.
- [ ] A10-T07 Add post-deploy health summary output.
- [ ] A10-T08 Improve alert routing and incident logs.
- [ ] A10-T09 Maintain rollback runbook.
- [ ] A10-T10 Maintain deployment history and release notes.

## Execution Command Template
```bash
python scripts/enterprise_parallel_runner.py \
  --mode run \
  --backlog docs/plans/department_backlog_100x10_2026-03-03.csv \
  --output-dir docs/plans/execution/2026-03-05-wave1 \
  --session-label "2026-03-05-wave1" \
  --include-all \
  --priorities P0,P1,P2,P3 \
  --limit-per-dept 10 \
  --max-workers 10 \
  --command-template "python scripts/department_queue_worker.py --department-id \"{department_id}\" --task-file \"{task_file}\" --output-dir \"{output_dir}\""
```

## Reporting Rule
- At the end of each wave, publish:
- Completion ratio by agent (`done/10`)
- Blockers and owner
- Next-wave carry-over tasks
- Deployment impact and rollback note
