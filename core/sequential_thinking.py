"""
core/sequential_thinking.py
Shared Sequential Thinking engine used by all Deca-Agents.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class ThinkingStep(str, Enum):
    UNDERSTAND = "UNDERSTAND"
    DECOMPOSE = "DECOMPOSE"
    EVALUATE = "EVALUATE"
    DECIDE = "DECIDE"
    EXECUTE = "EXECUTE"
    HANDOFF = "HAND-OFF"


@dataclass
class ThoughtChain:
    agent_id: str
    agent_name: str
    task: str
    steps: dict = field(default_factory=dict)

    def think(self, step: ThinkingStep, content: str) -> "ThoughtChain":
        self.steps[step.value] = content
        return self

    def validate(self) -> bool:
        """Ensure all 6 steps are completed before hand-off."""
        required = {s.value for s in ThinkingStep}
        return required.issubset(self.steps.keys())

    def summary(self) -> str:
        lines = [f"[{self.agent_id}][{self.agent_name}] Sequential Thinking Summary"]
        lines.append(f"Task: {self.task}")
        for step, content in self.steps.items():
            lines.append(f"  [{step}] {content}")
        if not self.validate():
            missing = {s.value for s in ThinkingStep} - self.steps.keys()
            lines.append(f"  WARNING: Missing steps: {missing}")
        return "\n".join(lines)
