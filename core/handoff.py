"""
core/handoff.py
Structured inter-agent hand-off message format (per .clauderules Rule 2).
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import datetime
import json


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETE = "COMPLETE"


@dataclass
class HandOffMessage:
    from_agent_id: str
    from_agent_name: str
    to_agent_id: str
    to_agent_name: str
    mission_id: str
    status: TaskStatus
    summary: str
    output: List[str] = field(default_factory=list)
    next_action: str = ""
    blockers: str = "none"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "FROM": f"{self.from_agent_id}/{self.from_agent_name}",
            "TO": f"{self.to_agent_id}/{self.to_agent_name}",
            "MISSION": self.mission_id,
            "STATUS": self.status.value,
            "SUMMARY": self.summary,
            "OUTPUT": self.output,
            "NEXT_ACTION": self.next_action,
            "BLOCKERS": self.blockers,
            "TIMESTAMP": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def is_blocked(self) -> bool:
        return self.status == TaskStatus.BLOCKED
