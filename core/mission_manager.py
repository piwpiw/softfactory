"""
core/mission_manager.py
Mission lifecycle management: CREATE → IN_PROGRESS → BLOCKED → COMPLETE → ARCHIVED.
All state changes are persisted to logs/missions.jsonl and reflected in CLAUDE.md.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict

LOGS_DIR = Path(__file__).parent.parent / "logs"
MISSIONS_LOG = LOGS_DIR / "missions.jsonl"


class MissionStatus(str, Enum):
    PENDING     = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED     = "BLOCKED"
    COMPLETE    = "COMPLETE"
    ARCHIVED    = "ARCHIVED"


class MissionPhase(str, Enum):
    PLANNING    = "PLANNING"
    RESEARCH    = "RESEARCH"
    DESIGN      = "DESIGN"
    DEVELOPMENT = "DEVELOPMENT"
    VALIDATION  = "VALIDATION"
    DEPLOYMENT  = "DEPLOYMENT"
    REPORTING   = "REPORTING"


@dataclass
class MissionEvent:
    event: str
    agent: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: str = ""


@dataclass
class Retrospective:
    mission_id: str
    what_went_well: List[str] = field(default_factory=list)
    what_to_improve: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    recorded_by: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Mission:
    mission_id: str
    name: str
    owner: str
    status: MissionStatus = MissionStatus.PENDING
    phase: MissionPhase = MissionPhase.PLANNING
    started: Optional[str] = None
    completed: Optional[str] = None
    notes: str = ""
    blockers: List[str] = field(default_factory=list)
    events: List[MissionEvent] = field(default_factory=list)
    retrospective: Optional[Retrospective] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        d["phase"] = self.phase.value
        return d


# ---------------------------------------------------------------------------
# Mission Manager
# ---------------------------------------------------------------------------

class MissionManager:
    """Thread-safe mission lifecycle manager."""

    _instance: Optional[MissionManager] = None
    _lock = threading.Lock()
    _missions: Dict[str, Mission] = {}

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._missions = {}
        return cls._instance

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(
        self,
        mission_id: str,
        name: str,
        owner: str,
        notes: str = "",
    ) -> Mission:
        mission = Mission(
            mission_id=mission_id,
            name=name,
            owner=owner,
            notes=notes,
        )
        self._missions[mission_id] = mission
        self._persist(mission, "CREATED")
        return mission

    def get(self, mission_id: str) -> Optional[Mission]:
        return self._missions.get(mission_id)

    def start(self, mission_id: str, agent: str) -> Mission:
        return self._transition(
            mission_id, MissionStatus.IN_PROGRESS, MissionPhase.PLANNING, agent, "Mission started"
        )

    def advance_phase(self, mission_id: str, phase: MissionPhase, agent: str) -> Mission:
        m = self._get_or_raise(mission_id)
        m.phase = phase
        self._record_event(m, f"Phase advanced to {phase.value}", agent)
        self._persist(m, f"PHASE:{phase.value}")
        return m

    def block(self, mission_id: str, reason: str, agent: str) -> Mission:
        m = self._get_or_raise(mission_id)
        m.status = MissionStatus.BLOCKED
        m.blockers.append(reason)
        self._record_event(m, f"BLOCKED: {reason}", agent)
        self._persist(m, "BLOCKED")
        return m

    def unblock(self, mission_id: str, agent: str) -> Mission:
        m = self._get_or_raise(mission_id)
        m.status = MissionStatus.IN_PROGRESS
        m.blockers.clear()
        self._record_event(m, "Unblocked — resuming", agent)
        self._persist(m, "UNBLOCKED")
        return m

    def complete(self, mission_id: str, agent: str) -> Mission:
        m = self._get_or_raise(mission_id)
        m.status = MissionStatus.COMPLETE
        m.completed = datetime.utcnow().isoformat()
        self._record_event(m, "Mission completed", agent)
        self._persist(m, "COMPLETED")
        # Update CLAUDE.md
        try:
            from core.ledger import update_mission_status
            update_mission_status(mission_id, "COMPLETE")
        except Exception:
            pass
        return m

    def record_retrospective(
        self,
        mission_id: str,
        what_went_well: List[str],
        what_to_improve: List[str],
        action_items: List[str],
        recorded_by: str,
    ) -> Mission:
        """Rule 12: retrospective mandatory after each mission completion."""
        m = self._get_or_raise(mission_id)
        m.retrospective = Retrospective(
            mission_id=mission_id,
            what_went_well=what_went_well,
            what_to_improve=what_to_improve,
            action_items=action_items,
            recorded_by=recorded_by,
        )
        self._persist(m, "RETROSPECTIVE")
        return m

    def list_active(self) -> List[Mission]:
        return [
            m for m in self._missions.values()
            if m.status in (MissionStatus.PENDING, MissionStatus.IN_PROGRESS, MissionStatus.BLOCKED)
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_raise(self, mission_id: str) -> Mission:
        m = self._missions.get(mission_id)
        if m is None:
            raise MissionNotFoundError(f"Mission '{mission_id}' not found.")
        return m

    def _transition(
        self,
        mission_id: str,
        status: MissionStatus,
        phase: MissionPhase,
        agent: str,
        note: str,
    ) -> Mission:
        m = self._get_or_raise(mission_id)
        m.status = status
        m.phase = phase
        if status == MissionStatus.IN_PROGRESS and not m.started:
            m.started = datetime.utcnow().isoformat()
        self._record_event(m, note, agent)
        self._persist(m, status.value)
        return m

    def _record_event(self, mission: Mission, event: str, agent: str, details: str = "") -> None:
        mission.events.append(MissionEvent(event=event, agent=agent, details=details))

    def _persist(self, mission: Mission, event_type: str) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        entry = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **mission.to_dict(),
        }
        with self._lock:
            with open(MISSIONS_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class MissionNotFoundError(Exception):
    pass


# Singleton accessor
def get_manager() -> MissionManager:
    return MissionManager()
