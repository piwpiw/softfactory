"""
skills/ux_research.py
UX Research — JTBD, Nielsen 10 Heuristics, WCAG 2.1, RICE scoring.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class UXResearch:
    name: str = "UX Research"
    principles: List[str] = field(default_factory=lambda: [
        "User-Centered — design decisions grounded in observed user behavior",
        "Continuous Discovery — research is never 'done'; validate every sprint",
        "Inclusive Design — design for accessibility first (WCAG 2.1 AA)",
        "Evidence-Based — data over opinions; avoid HiPPO bias",
        "Jobs-To-Be-Done — users hire products to get a job done, not features",
        "Minimum Observable Research — ship learning, not just shipping features",
    ])
    methodology: List[str] = field(default_factory=lambda: [
        "1. RECRUIT      — Define screener; recruit 5-8 target users per study",
        "2. CHOOSE METHOD — Generative (interviews, diary) vs Evaluative (usability, A/B)",
        "3. CONDUCT       — Moderate neutrally; capture observations, not interpretations",
        "4. SYNTHESIZE    — Affinity mapping; identify patterns",
        "5. INSIGHTS      — Convert observations → insights → design implications",
        "6. VALIDATE      — Test designs; iterate; measure HEART metrics",
        "7. SHARE         — Research repository; weekly insight summaries",
    ])
    tools: List[str] = field(default_factory=lambda: [
        "User Interview Guide", "Affinity Map (Miro/FigJam)",
        "Usability Test Protocol (Maze/UserTesting)",
        "HEART Framework (Happiness, Engagement, Adoption, Retention, Task Success)",
        "SUS (System Usability Scale)", "NPS Survey",
        "Tree Testing", "Card Sorting", "First Click Test",
        "Session Recording (FullStory/Hotjar)",
    ])
    output_templates: List[str] = field(default_factory=lambda: [
        "JTBD Statement: 'When {situation}, I want to {motivation}, so I can {expected outcome}'",
        "Research Plan (goal/questions/method/participants/timeline)",
        "Usability Test Report (tasks/findings/severity/recommendations)",
        "WCAG 2.1 Audit Checklist",
        "HEART Metrics Dashboard",
    ])

    NIELSEN_HEURISTICS = {
        "H1":  "Visibility of system status",
        "H2":  "Match between system and real world",
        "H3":  "User control and freedom",
        "H4":  "Consistency and standards",
        "H5":  "Error prevention",
        "H6":  "Recognition rather than recall",
        "H7":  "Flexibility and efficiency of use",
        "H8":  "Aesthetic and minimalist design",
        "H9":  "Help users recognize, diagnose, and recover from errors",
        "H10": "Help and documentation",
    }

    WCAG_PRINCIPLES = {
        "Perceivable":   ["Text alternatives for non-text", "Captions for video", "Min 4.5:1 color contrast"],
        "Operable":      ["Keyboard accessible", "No seizure triggers", "Min 44px touch targets"],
        "Understandable": ["Consistent navigation", "Error identification", "Labels for inputs"],
        "Robust":        ["Valid HTML", "Name/role/value for UI components", "Status messages programmatic"],
    }

    def apply(self, context: dict) -> dict:
        product = context.get("product", "CooCook")
        users = context.get("user_segments", ["Leisure Traveler", "Digital Nomad"])
        features = context.get("features_to_evaluate", ["Recipe Discovery", "Chef Booking"])

        jtbd = [
            {
                "segment": u,
                "statement": f"When planning a trip, I want to discover authentic local food experiences so I can connect with the culture of {product}.",
            }
            for u in users
        ]

        return {
            "skill": self.name,
            "jtbd_statements": jtbd,
            "research_plan": {
                "goals": [f"Understand {u} pain points with {f}" for u in users for f in features[:1]],
                "methods": ["Semi-structured interviews (generative)", "Usability test (evaluative)"],
                "participant_count": 5,
                "timeline": "2 weeks: 1 recruit + 1 conduct + 1 synthesize",
            },
            "heuristic_evaluation": {
                description: heuristic
                for description, heuristic in self.NIELSEN_HEURISTICS.items()
            },
            "wcag_assessment": self.WCAG_PRINCIPLES,
            "heart_metrics": {
                "Happiness": "SUS score target: > 68",
                "Engagement": "Sessions per user per week",
                "Adoption": "% new users completing first booking",
                "Retention": "Day-7 retention rate",
                "Task Success": "Recipe discovery task completion rate",
            },
        }

    def rice_score(self, reach: int, impact: int, confidence: float, effort: float) -> dict:
        """
        RICE Scoring: (Reach × Impact × Confidence) / Effort
        reach: users affected per period
        impact: 0=minimal, 1=low, 2=medium, 3=high, 4=massive
        confidence: 0.0-1.0
        effort: person-months
        """
        if effort <= 0:
            raise ValueError("Effort must be > 0")
        score = round((reach * impact * confidence) / effort, 1)
        priority = "P0" if score >= 1000 else "P1" if score >= 500 else "P2" if score >= 100 else "P3"
        return {
            "reach": reach, "impact": impact,
            "confidence": confidence, "effort": effort,
            "rice_score": score, "priority": priority,
        }

    def checklist(self) -> List[str]:
        return [
            "[ ] JTBD statements defined for primary user segments",
            "[ ] Research questions scoped (3-5 questions per study)",
            "[ ] Minimum 5 participants recruited per study",
            "[ ] Heuristic evaluation completed (Nielsen 10)",
            "[ ] WCAG 2.1 AA audit completed",
            "[ ] Usability issues classified by severity (Critical/Serious/Minor)",
            "[ ] HEART metrics defined and tracked",
            "[ ] Research insights documented in shared repository",
            "[ ] Design decisions linked to research insights",
        ]
