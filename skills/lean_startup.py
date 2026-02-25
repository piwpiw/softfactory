"""
skills/lean_startup.py
Lean Startup — Build-Measure-Learn cycle with MVP and Pivot/Persevere decisions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class LeanStartup:
    name: str = "Lean Startup"
    principles: List[str] = field(default_factory=lambda: [
        "Eliminate waste — build only what validates learning",
        "Validated learning — every build must produce measurable insight",
        "Innovation accounting — track actionable, accessible, auditable metrics",
        "Build-Measure-Learn — tighten the loop as fast as possible",
        "Pivot or Persevere — honest data-driven decisions, not ego-driven",
    ])
    methodology: List[str] = field(default_factory=lambda: [
        "1. IDENTIFY — Define riskiest assumption (Leap of Faith)",
        "2. BUILD    — Minimum Viable Product to test the assumption",
        "3. MEASURE  — Define and collect One Metric That Matters (OMTM)",
        "4. LEARN    — Validated Learning: did we invalidate or confirm?",
        "5. DECIDE   — Pivot (change strategy) or Persevere (scale)",
    ])
    tools: List[str] = field(default_factory=lambda: [
        "Lean Canvas", "MVP Experiment Board",
        "A/B Testing", "Cohort Analysis", "Funnel Metrics",
        "Jobs-To-Be-Done", "Customer Development Interviews",
        "Innovation Accounting Dashboard", "Pivot Log",
    ])
    output_templates: List[str] = field(default_factory=lambda: [
        "Lean Canvas (9-block)",
        "MVP Hypothesis: 'We believe {customer} will {action} for {reason}'",
        "Experiment Card (assumption/test/metric/criteria)",
        "Pivot Decision Report (data + reasoning)",
        "OMTM Dashboard",
    ])

    def apply(self, context: dict) -> dict:
        hypothesis = context.get("hypothesis", "Our product solves a real problem")
        mvp_type = context.get("mvp_type", "Concierge MVP")
        metric = context.get("primary_metric", "activation_rate")
        target = context.get("metric_target", 0.1)

        return {
            "skill": self.name,
            "current_hypothesis": hypothesis,
            "build": {
                "mvp_type": mvp_type,
                "mvp_types_available": [
                    "Concierge (manual service)", "Wizard of Oz (fake automation)",
                    "Landing Page", "Feature Fake", "Smoke Test",
                ],
                "scope_constraint": "Ship in ≤2 weeks",
            },
            "measure": {
                "omtm": metric,
                "target": target,
                "data_collection": ["Analytics events", "User interviews", "NPS survey"],
                "avoid_vanity_metrics": ["Total signups", "Page views"],
            },
            "learn": {
                "validated_if": f"{metric} >= {target}",
                "invalidated_if": f"{metric} < {target * 0.5}",
                "pivot_triggers": [
                    "Retention < 20% at Day 7",
                    "CAC > 3x LTV",
                    "NPS consistently < 0",
                ],
            },
            "decide": {
                "persevere_criteria": f"{metric} >= {target} consistently over 2 cohorts",
                "pivot_options": ["Zoom-in", "Zoom-out", "Customer segment", "Platform"],
            },
        }

    def checklist(self) -> List[str]:
        return [
            "[ ] Identified riskiest Leap of Faith assumption",
            "[ ] Defined MVP scope (build in ≤2 weeks)",
            "[ ] Selected One Metric That Matters (OMTM)",
            "[ ] Set clear pass/fail criteria BEFORE building",
            "[ ] Completed one full BML loop",
            "[ ] Made explicit Pivot or Persevere decision with data",
            "[ ] Updated Lean Canvas after each loop",
            "[ ] Logged pivot decisions with rationale",
        ]
