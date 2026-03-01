"""
skills/devops_sre.py
DevOps / SRE — SLO/SLI/Error Budget, GitOps, Chaos Engineering, Blue-Green.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class DevOpsSRE:
    name: str = "DevOps / SRE"
    principles: List[str] = field(default_factory=lambda: [
        "Everything as Code — infra, config, pipelines all in version control",
        "Automate toil — manual work that is repetitive/automatable must be eliminated",
        "Error Budgets — balance reliability and feature velocity explicitly",
        "Blameless Culture — post-mortems focus on systems, not individuals",
        "Observability — Logs + Metrics + Traces = full system understanding",
        "Continuous Delivery — every commit is a release candidate",
    ])
    methodology: List[str] = field(default_factory=lambda: [
        "1. SLI SELECTION  — Define measurable indicators (latency, availability, error rate)",
        "2. SLO SETTING    — Set target thresholds (e.g., 99.9% availability/28-day rolling)",
        "3. ERROR BUDGET   — 100% - SLO target = budget available for risk",
        "4. GITOPS SETUP   — All infra changes via Git PRs (ArgoCD/Flux reconciles)",
        "5. CI/CD PIPELINE — Build → Test → Scan → Deploy → Verify",
        "6. BLUE-GREEN     — Run parallel environments; switch traffic; verify; decommission old",
        "7. CHAOS TESTING  — Hypothesis → Steady State → Inject Failure → Observe",
    ])
    tools: List[str] = field(default_factory=lambda: [
        "Terraform / Pulumi (IaC)",
        "GitHub Actions / GitLab CI / Jenkins (CI/CD)",
        "ArgoCD / Flux (GitOps)",
        "Prometheus + Grafana (Metrics)",
        "OpenTelemetry (Tracing)", "ELK / Loki (Logging)",
        "Chaos Monkey / Gremlin / Litmus (Chaos)",
        "Datadog / New Relic (APM)",
        "Dependabot / Renovate (Dependency updates)",
    ])
    output_templates: List[str] = field(default_factory=lambda: [
        "SLO Document (SLI, target, window, error budget)",
        "Deployment Runbook per docs/standards/DEPLOYMENT_RUNBOOK_TEMPLATE.md",
        "Post-Mortem Report (5 Whys, timeline, action items)",
        "Chaos Experiment Report",
        "CI/CD Pipeline specification",
    ])

    def apply(self, context: dict) -> dict:
        service = context.get("service", "CooCook API")
        slo_target = context.get("slo_target_pct", 99.9)
        deployment_strategy = context.get("deployment_strategy", "blue-green")
        window_days = context.get("window_days", 28)

        error_budget_minutes = (100 - slo_target) / 100 * window_days * 24 * 60

        return {
            "skill": self.name,
            "slo": {
                "service": service,
                "slis": [
                    "Availability (HTTP 2xx/5xx ratio)",
                    "Latency (p99 < 500ms)",
                    "Error Rate (< 0.1%)",
                    "Throughput (req/sec)",
                ],
                "target": f"{slo_target}%",
                "window": f"{window_days}-day rolling",
                "error_budget_minutes": round(error_budget_minutes, 1),
                "burn_rate_alerts": [
                    {"window": "1h", "burn_rate": 14.4, "severity": "CRITICAL"},
                    {"window": "6h", "burn_rate": 6, "severity": "HIGH"},
                    {"window": "3d", "burn_rate": 1, "severity": "WARNING"},
                ],
            },
            "gitops": {
                "principle": "Git is single source of truth",
                "flow": "Code PR → CI Tests → Merge → GitOps operator reconciles cluster",
                "tools": ["ArgoCD", "Flux v2"],
                "rollback": "Git revert → auto-reconcile",
            },
            "deployment": {
                "strategy": deployment_strategy,
                "blue_green_steps": [
                    "1. Deploy new version to Green environment",
                    "2. Run smoke tests on Green",
                    "3. Switch load balancer: 100% traffic → Green",
                    "4. Monitor error budget for 15 min",
                    "5. Decommission Blue (or keep for 24h rollback)",
                ],
                "rollback_time": "< 2 minutes",
            },
            "chaos_engineering": {
                "hypothesis_template": "Steady state: {slo_target}% availability. Inject: {failure}. Expect: {recovery_behavior}.",
                "common_experiments": [
                    "Kill random pod in production",
                    "Inject 500ms network latency",
                    "Exhaust DB connection pool",
                    "Corrupt 1% of cache entries",
                ],
            },
        }

    def checklist(self) -> List[str]:
        return [
            "[ ] SLIs defined and measurable via telemetry",
            "[ ] SLO targets set with stakeholder agreement",
            "[ ] Error budget policy documented (freeze features when budget exhausted)",
            "[ ] All infra in version control (no manual config)",
            "[ ] CI pipeline: build → test → security scan → deploy",
            "[ ] Deployment verified via health checks before traffic switch",
            "[ ] Rollback procedure tested and documented",
            "[ ] Runbook exists for all P0/P1 incident scenarios",
            "[ ] Alerting covers all SLI burn rate thresholds",
            "[ ] Post-mortem completed for every P0/P1 incident",
        ]
