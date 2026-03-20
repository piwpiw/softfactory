# Enterprise Upgrade Day Plan (2026-03-03)

## 1) Objective
Upgrade SoftFactory toward enterprise-grade operations using a document-driven and automation-first execution model.

This plan is based on existing project governance, team routing, and feature documentation, and is scoped for one working day.

## 2) Source of Truth
- `.agent/AGENT_SYSTEM.md` (team-to-role mapping, escalation, lifecycle)
- `orchestrator/phase-structure-v4.md` (document-driven execution phases)
- `VALIDATION_QUICK_REFERENCE.md` (validated baseline, endpoint and UI coverage)
- `docs/runbooks/DEMO_GUIDE.md` (service features and test walkthrough)
- `../reference/legacy-root/USER_MANUAL.md` (user-level functional requirements)
- `DEPLOYMENT_STATUS_FINAL.md` (deployment and runtime readiness context)

## 3) Current Snapshot
- Team model: 10 departments (`T1` to `T10`)
- HTML pages currently present in `web/`: `126`
- Major page distribution:
- `platform`: 41
- `sns-auto`: 13
- `coocook`: 11
- `review`: 10
- `ai-automation`: 8
- `webapp-builder`: 7
- Validation baseline (from docs): 40/40 checks passed, 0 critical blockers

## 4) Page Feature Research Summary

### 4.1 Platform (`web/platform/*`)
- Login with passkey and credential options
- Unified dashboard and multi-service navigation
- Settings/profile/security/billing/admin-monitoring pages
- Enterprise gap:
- RBAC granularity and least-privilege enforcement per page/action
- Full audit trail and actor/session correlation for all sensitive actions
- Tenant-level controls and policy inheritance model

### 4.2 CooCook (`web/coocook/*`)
- Chef discovery, filtering, booking flow, booking history
- Dynamic pricing and booking status handling
- Enterprise gap:
- Contracted pricing policy versioning and approval trace
- Fraud/risk controls on booking and payment flow
- SLA and incident playbook for booking failures

### 4.3 SNS Auto (`web/sns-auto/*`)
- Multi-account social connection
- Post creation/scheduling/history/templates
- Analytics/monetization/trending pages exist in module
- Enterprise gap:
- Publishing reliability controls (retry policy, idempotency, dead-letter)
- Platform-specific compliance checks before publish
- Cross-account governance and delegated access policy

### 4.4 Review (`web/review/*`)
- Campaign browse/create/apply and application status flows
- Review lifecycle management and campaign analytics
- Enterprise gap:
- Data provenance and anti-abuse controls for review ingestion
- Moderation workflow with policy, evidence, and appeal state
- PII masking and retention control in exports

### 4.5 AI Automation (`web/ai-automation/*`)
- Plan/scenario catalog and worker deployment flow
- Dashboard for savings and worker state visibility
- Enterprise gap:
- Model-risk governance (prompt/version/owner/change history)
- Human approval checkpoints for high-risk automation
- Drift and cost guardrails with policy thresholds

### 4.6 WebApp Builder (`web/webapp-builder/*`)
- Enrollment, curriculum, project creation/management pages
- Lifecycle visibility from draft to deployed status
- Enterprise gap:
- Release governance with stage gates (dev/staging/prod)
- Artifact integrity and deployment traceability
- Policy-based rollback criteria and ownership

## 5) Enterprise Upgrade Work Model

### 5.1 Backlog Scale
- Generated backlog: `100 tasks per department` x `10 departments` = `1,000 tasks`
- File: `docs/plans/department_backlog_100x10_2026-03-03.csv`
- Structure: 10 services x 10 workstreams per department = 100 tasks each

### 5.2 Workstream Set (applied to every department)
- Requirements traceability
- Page function audit
- API contract audit
- Data integrity
- Test automation
- Performance and SLO
- Security hardening
- CI/CD automation
- Runbook and incident handling
- Metrics and reporting

## 6) One-Day Execution Plan (Today)

### 6.1 Parallel Ownership
- T1 Chief Dispatcher: priority, decision gates, blockers
- T2 Product Manager: requirement quality and KPI acceptance
- T3 Market Analyst: competitive and value validation
- T4 Architect: ADR/OpenAPI/system consistency
- T5 Backend: API/data integrity implementation
- T6 Frontend: page behavior/accessibility/integration
- T7 QA: regression and integration test design/execution
- T8 Security: OWASP and compliance controls
- T9 DevOps: CI/CD, observability, rollback readiness
- T10 Reporter: status cadence and alert routing

### 6.2 Timeboxed Plan (KST, 2026-03-03)
- `09:00-09:30` Phase -1 Research sync
- Confirm scope from source docs and lock "today candidate" tasks
- `09:30-10:30` Phase 0 Planning
- Assign top tasks per department, define acceptance and SLA
- `10:30-12:00` Phase 1 Requirement + Phase 2 Documentation
- Update requirement diffs and produce doc-linked checklists
- `13:00-15:30` Phase 3 Design + Phase 4 Development
- Execute highest-risk enterprise gaps in parallel by department
- `15:30-17:00` Phase 5 Testing and Validation
- Validate page flows, API contracts, security checks, and SLO probes
- `17:00-18:00` Phase 6 Finalization + Phase 7 Delivery
- Publish daily report, backlog burn snapshot, and next-day queue

### 6.3 Daily Throughput Target
- Minimum completion target today:
- `12 tasks per department` (`today_candidate=Yes` in CSV)
- Total target: `120 tasks`
- Stretch target:
- `30 tasks per department` (`today_candidate in Yes/Maybe`)

## 7) Automation-First Maintenance Loop
- Document gate:
- No task can be marked complete without doc reference and evidence link
- Validation gate:
- Page/API/security checks run against task acceptance criteria
- Handoff gate:
- Emit structured handoff payload with owner, blockers, and changed assets
- Reporting gate:
- Post status digest and risk alerts at fixed intervals

## 8) End-of-Day Success Criteria
- 0 unresolved P0 security or production-risk blockers
- All completed tasks linked to source documents and evidence
- Updated prioritized queue for next day from remaining backlog
- Published daily summary with KPI deltas and incident notes

## 9) Execution Notes
- Use the generated CSV as the operational queue.
- Filter quickly:
- `today_candidate=Yes` for strict day plan
- `priority=P0 or P1` for risk-first execution
- Keep all outputs doc-linked to preserve automated maintenance readiness.

## 10) Parallel Execution Commands
- Prepare per-department daily queues:
```bash
python scripts/enterprise_parallel_runner.py \
  --mode prepare \
  --backlog docs/plans/department_backlog_100x10_2026-03-03.csv \
  --today-only \
  --priorities P0,P1 \
  --limit-per-dept 12
```

- Run all departments in parallel (example command template):
```bash
python scripts/enterprise_parallel_runner.py \
  --mode run \
  --backlog docs/plans/department_backlog_100x10_2026-03-03.csv \
  --today-only \
  --priorities P0,P1 \
  --limit-per-dept 12 \
  --max-workers 10 \
  --command-template "python scripts/project_reporter.py summary"
```
