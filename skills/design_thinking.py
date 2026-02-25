"""
skills/design_thinking.py
Stanford d.school Design Thinking — 5-stage human-centered design process.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class DesignThinking:
    name: str = "Design Thinking"
    principles: List[str] = field(default_factory=lambda: [
        "Human-centered — start with empathy, not assumptions",
        "Iterative — prototype early, learn fast, refine often",
        "Collaborative — cross-functional diverse teams",
        "Optimistic — assume all problems are solvable",
        "Experimental — bias toward action over discussion",
    ])
    methodology: List[str] = field(default_factory=lambda: [
        "1. EMPATHIZE — Observe, interview, immerse to understand user needs",
        "2. DEFINE    — Synthesize findings into a clear Problem Statement (HMW)",
        "3. IDEATE    — Brainstorm broadly; defer judgment; quantity over quality",
        "4. PROTOTYPE — Build low-fidelity artifacts to test ideas cheaply",
        "5. TEST      — Get user feedback, iterate, pivot or persevere",
    ])
    tools: List[str] = field(default_factory=lambda: [
        "Empathy Map", "User Interview Guide", "Journey Map",
        "HMW (How Might We) statements", "Affinity Diagram",
        "Crazy 8s", "Storyboard", "Paper Prototype",
        "Usability Test Script", "5 Whys",
    ])
    output_templates: List[str] = field(default_factory=lambda: [
        "Empathy Map (4-quadrant: Say/Think/Do/Feel)",
        "Problem Statement: '{Persona} needs {need} because {insight}'",
        "Ideation Board (minimum 20 ideas)",
        "Prototype Hypothesis: 'We believe {prototype} will achieve {outcome}'",
        "Test Findings Report (observations + insights + next iterations)",
    ])

    def apply(self, context: dict) -> dict:
        """
        Apply Design Thinking to a given product/feature context.

        Args:
            context: dict with keys like 'user_segment', 'pain_points', 'goal'

        Returns:
            Structured DT output per stage.
        """
        user = context.get("user_segment", "Target User")
        pain = context.get("pain_points", ["undefined pain points"])
        goal = context.get("goal", "improve user experience")

        return {
            "skill": self.name,
            "empathize": {
                "observation_focus": user,
                "key_pain_points": pain,
                "recommended_methods": ["User interviews", "Shadowing", "Diary studies"],
            },
            "define": {
                "hmw_statement": f"How Might We help {user} to {goal} without {', '.join(pain[:1])}?",
                "problem_statement": f"{user} needs a way to {goal} because {', '.join(pain[:1])}.",
            },
            "ideate": {
                "techniques": ["Crazy 8s", "SCAMPER", "Worst Possible Idea (invert)"],
                "target_ideas": 20,
                "convergence_method": "Dot voting → top 3 ideas",
            },
            "prototype": {
                "fidelity": "Lo-fi (paper/wireframe)",
                "hypothesis": f"We believe that if {user} can {goal}, we will see increased engagement.",
                "build_time_target": "1 day maximum",
            },
            "test": {
                "participant_count": 5,
                "method": "Usability test (think-aloud protocol)",
                "success_metrics": ["Task completion rate", "SUS score > 68"],
            },
        }

    def checklist(self) -> List[str]:
        return [
            "[ ] Conducted minimum 5 user interviews",
            "[ ] Created Empathy Map for primary persona",
            "[ ] Defined HMW statement (tested with team)",
            "[ ] Generated 20+ ideas before convergence",
            "[ ] Built and tested at least 1 lo-fi prototype",
            "[ ] Documented test findings and next iteration",
            "[ ] Shared insights with PM and Dev teams",
        ]
