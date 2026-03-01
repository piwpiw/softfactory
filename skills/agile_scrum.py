"""
skills/agile_scrum.py
Agile / Scrum — Scrum ceremonies, Kanban flow, Velocity, Burndown.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class AgileScrum:
    name: str = "Agile Scrum"
    principles: List[str] = field(default_factory=lambda: [
        "Individuals and interactions over processes and tools",
        "Working software over comprehensive documentation",
        "Customer collaboration over contract negotiation",
        "Responding to change over following a plan",
        "Deliver working software frequently (2-4 week sprints)",
        "Sustainable pace — teams should maintain indefinitely",
    ])
    methodology: List[str] = field(default_factory=lambda: [
        "1. PRODUCT BACKLOG — Prioritized list of all desired work (PO owned)",
        "2. SPRINT PLANNING — Select items from backlog, create Sprint Backlog",
        "3. DAILY SCRUM (15min) — What did I do? What will I do? Any blockers?",
        "4. SPRINT REVIEW — Demo working software to stakeholders",
        "5. RETROSPECTIVE — Inspect and adapt process (Start/Stop/Continue)",
        "6. BACKLOG REFINEMENT — Ongoing estimation and prioritization",
    ])
    tools: List[str] = field(default_factory=lambda: [
        "Product Backlog", "Sprint Backlog", "Burndown Chart",
        "Velocity Chart", "Definition of Done", "Story Points",
        "Kanban Board (To Do / In Progress / Review / Done)",
        "Sprint Goal Statement", "Release Burnup Chart",
        "Team Health Check Radar",
    ])
    output_templates: List[str] = field(default_factory=lambda: [
        "Sprint Planning Board",
        "User Story: 'As a {persona}, I want {feature} so that {benefit}'",
        "Definition of Done Checklist",
        "Sprint Retrospective Report (Start/Stop/Continue)",
        "Velocity Trend Chart",
        "Release Plan (story points per sprint)",
    ])

    def apply(self, context: dict) -> dict:
        team_size = context.get("team_size", 5)
        sprint_length = context.get("sprint_length_days", 14)
        velocity = context.get("avg_velocity_pts", 30)
        backlog_pts = context.get("backlog_points", 120)

        sprints_needed = -(-backlog_pts // velocity)  # ceiling division

        return {
            "skill": self.name,
            "team": {
                "size": team_size,
                "recommended_roles": ["Product Owner", "Scrum Master", f"{team_size-2} Developers"],
            },
            "sprint_cadence": {
                "length_days": sprint_length,
                "ceremonies": {
                    "planning": f"Day 1, {min(4, sprint_length//3)}h max",
                    "daily": "Every day, 15 min, same time",
                    "review": f"Day {sprint_length}, 1h per week of sprint",
                    "retrospective": f"Day {sprint_length}, {sprint_length//7 + 1}h max",
                },
            },
            "metrics": {
                "current_velocity": velocity,
                "backlog_points": backlog_pts,
                "estimated_sprints": sprints_needed,
                "estimated_weeks": sprints_needed * (sprint_length // 7),
            },
            "kanban_flow": {
                "columns": ["Backlog", "Ready", "In Progress", "In Review", "Done"],
                "wip_limits": {"In Progress": team_size, "In Review": team_size // 2 + 1},
            },
            "definition_of_done": [
                "Code reviewed (min 1 peer reviewer)",
                "Unit tests written and passing",
                "Integration tests passing",
                "No new CRITICAL/HIGH security findings",
                "Documentation updated",
                "Deployed to staging",
                "Product Owner acceptance confirmed",
            ],
        }

    def checklist(self) -> List[str]:
        return [
            "[ ] Product Backlog groomed and estimated",
            "[ ] Sprint Goal clearly stated and agreed",
            "[ ] Daily Scrums held consistently",
            "[ ] Burndown chart updated daily",
            "[ ] Sprint Review demo prepared",
            "[ ] Retrospective actions have owners + due dates",
            "[ ] Velocity tracked over minimum 3 sprints",
            "[ ] Definition of Done enforced consistently",
        ]
