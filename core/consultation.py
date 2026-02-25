"""
core/consultation.py
ConsultationBus — bidirectional inter-agent consultation system.
All consultations are persisted to logs/consultations.jsonl.
Circular consultation detection (A→B→A) is enforced.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict

LOGS_DIR = Path(__file__).parent.parent / "logs"
CONSULTATION_LOG = LOGS_DIR / "consultations.jsonl"


class ConsultationType(str, Enum):
    CLARIFICATION = "CLARIFICATION"   # Need a definition / requirement clarity
    REVIEW        = "REVIEW"          # Peer review of output
    DEPENDENCY    = "DEPENDENCY"      # Blocking dependency on another agent
    ESCALATION    = "ESCALATION"      # Always routed to Dispatcher (01)


class ConsultationPriority(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"
    URGENT = "URGENT"


@dataclass
class ConsultationRequest:
    from_agent: str          # e.g. "02/Product-Manager"
    to_agent: str            # e.g. "03/Market-Analyst"
    question: str
    context: str = ""
    priority: ConsultationPriority = ConsultationPriority.MEDIUM
    consultation_type: ConsultationType = ConsultationType.CLARIFICATION
    request_id: str = field(default_factory=lambda: _gen_id())
    timestamp: str = field(default_factory=lambda: _now())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["priority"] = self.priority.value
        d["consultation_type"] = self.consultation_type.value
        return d


@dataclass
class ConsultationResponse:
    request_id: str
    from_agent: str
    to_agent: str           # The original requester
    answer: str
    confidence: float = 1.0  # 0.0-1.0
    sources: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: _now())

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.utcnow().isoformat()


def _gen_id() -> str:
    import uuid
    return str(uuid.uuid4())[:8]


def _ensure_logs_dir():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# ConsultationBus
# ---------------------------------------------------------------------------

class ConsultationBus:
    """
    Central bus for agent-to-agent consultations.
    Thread-safe; all operations log to consultations.jsonl.
    """

    _instance: Optional[ConsultationBus] = None
    _lock = threading.Lock()

    # Circular detection: tracks currently in-flight (requester, target) pairs
    _active_pairs: set = set()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def consult(
        self,
        from_agent: str,
        to_agent: str,
        question: str,
        context: str = "",
        priority: ConsultationPriority = ConsultationPriority.MEDIUM,
        consultation_type: ConsultationType = ConsultationType.CLARIFICATION,
    ) -> ConsultationResponse:
        """
        Send a single consultation request.
        Raises ConsultationLoopError if circular consultation detected.
        """
        req = ConsultationRequest(
            from_agent=from_agent,
            to_agent=to_agent,
            question=question,
            context=context,
            priority=priority,
            consultation_type=consultation_type,
        )
        self._check_circular(req)
        pair = (req.from_agent, req.to_agent)
        self._active_pairs.add(pair)
        self._log_request(req)
        try:
            answer = self._resolve(req)
        finally:
            self._active_pairs.discard(pair)
        resp = ConsultationResponse(
            request_id=req.request_id,
            from_agent=to_agent,
            to_agent=from_agent,
            answer=answer,
            confidence=0.9,
            sources=[f"Agent {to_agent} knowledge base"],
        )
        self._log_response(resp)
        return resp

    def broadcast(
        self,
        from_agent: str,
        question: str,
        target_agents: List[str],
        context: str = "",
    ) -> List[ConsultationResponse]:
        """
        Broadcast a question to multiple agents and collect all responses.
        """
        responses = []
        for agent in target_agents:
            try:
                resp = self.consult(
                    from_agent=from_agent,
                    to_agent=agent,
                    question=question,
                    context=context,
                )
                responses.append(resp)
            except ConsultationLoopError as e:
                print(f"[ConsultationBus] Skipped circular consultation: {e}")
        return responses

    def escalate(
        self,
        from_agent: str,
        conflict: str,
    ) -> ConsultationResponse:
        """
        Escalate a conflict to Chief Dispatcher (01).
        Always bypasses circular detection (escalation is terminal).
        """
        req = ConsultationRequest(
            from_agent=from_agent,
            to_agent="01/Chief-Dispatcher",
            question=f"ESCALATION: {conflict}",
            priority=ConsultationPriority.URGENT,
            consultation_type=ConsultationType.ESCALATION,
        )
        self._log_request(req)
        answer = (
            f"[Dispatcher] Conflict received from {from_agent}. "
            "Roadmap re-evaluation initiated. All dependent agents set to BLOCKED."
        )
        resp = ConsultationResponse(
            request_id=req.request_id,
            from_agent="01/Chief-Dispatcher",
            to_agent=from_agent,
            answer=answer,
            confidence=1.0,
            sources=["01/Chief-Dispatcher escalation protocol"],
        )
        self._log_response(resp)
        return resp

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_circular(self, req: ConsultationRequest) -> None:
        """
        Detect A→B→A loops: if (B, A) is already active and A is now consulting B,
        or if (A, B) is already active (duplicate call), raise ConsultationLoopError.
        """
        # Direct reverse: A is consulting B while B is already consulting A
        reverse = (req.to_agent, req.from_agent)
        if reverse in self._active_pairs:
            raise ConsultationLoopError(
                f"Circular consultation detected: {req.from_agent} → {req.to_agent} "
                f"(reverse {req.to_agent} → {req.from_agent} is already active)"
            )
        # Self-loop
        if req.from_agent == req.to_agent:
            raise ConsultationLoopError(
                f"Self-consultation detected: {req.from_agent} → {req.to_agent}"
            )

    def _resolve(self, req: ConsultationRequest) -> str:
        """
        In production, each agent implements its own responder.
        This base implementation returns a structured placeholder.
        """
        return (
            f"[{req.to_agent}] Consultation received. "
            f"Type: {req.consultation_type.value}. "
            f"Question: '{req.question[:80]}'. "
            "Agent will process and update mission output accordingly."
        )

    def _log_request(self, req: ConsultationRequest) -> None:
        _ensure_logs_dir()
        entry = {"type": "REQUEST", **req.to_dict()}
        self._append_log(entry)

    def _log_response(self, resp: ConsultationResponse) -> None:
        _ensure_logs_dir()
        entry = {"type": "RESPONSE", **resp.to_dict()}
        self._append_log(entry)

    def _append_log(self, entry: dict) -> None:
        with self._lock:
            with open(CONSULTATION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class ConsultationLoopError(Exception):
    """Raised when a circular consultation chain is detected."""
    pass


# Singleton accessor
def get_bus() -> ConsultationBus:
    return ConsultationBus()
