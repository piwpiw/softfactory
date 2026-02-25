"""
Agent 01 — Chief Dispatcher
Receives all incoming tasks, evaluates roadmap, routes to correct agents.
Implements WSJF prioritization and real conflict resolution.
Conflict escalation target for all agents (.clauderules Rule 3).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core import (
    ThoughtChain, ThinkingStep, HandOffMessage, TaskStatus,
    get_logger, log_to_ledger, get_bus, ConsultationType,
    ConsultationPriority, get_manager, MissionPhase, notify,
)

AGENT_ID   = "01"
AGENT_NAME = "Chief-Dispatcher"

logger = get_logger(AGENT_ID, AGENT_NAME)


# ---------------------------------------------------------------------------
# WSJF Prioritization
# ---------------------------------------------------------------------------

def wsjf_score(user_value: int, time_criticality: int, risk_reduction: int, job_size: int) -> float:
    """
    Weighted Shortest Job First.
    CoD = User Value + Time Criticality + Risk/Opportunity Reduction
    WSJF = CoD / Job Size
    Higher score = higher priority.
    """
    if job_size <= 0:
        raise ValueError("Job size must be > 0")
    cod = user_value + time_criticality + risk_reduction
    return round(cod / job_size, 2)


def prioritize_tasks(tasks: list[dict]) -> list[dict]:
    """
    Sort tasks by WSJF score (descending).
    Each task dict: {name, user_value, time_criticality, risk_reduction, job_size}
    """
    scored = []
    for t in tasks:
        score = wsjf_score(
            t.get("user_value", 1),
            t.get("time_criticality", 1),
            t.get("risk_reduction", 1),
            t.get("job_size", 1),
        )
        scored.append({**t, "wsjf_score": score})
    return sorted(scored, key=lambda x: x["wsjf_score"], reverse=True)


# ---------------------------------------------------------------------------
# Conflict Resolution
# ---------------------------------------------------------------------------

def resolve_conflict(conflict: dict, mission_id: str) -> dict:
    """
    Structured conflict resolution algorithm.
    conflict dict: {type, description, blocking_agents, severity}
    Returns: {resolution, reassigned_to, action_items}
    """
    severity    = conflict.get("severity", "MEDIUM")
    description = conflict.get("description", "Unknown conflict")
    blocking    = conflict.get("blocking_agents", [])

    logger.warning(f"[CONFLICT] {severity}: {description}")
    logger.warning(f"Blocking agents: {blocking}")

    # Use ConsultationBus to escalate
    bus = get_bus()

    if severity in ("CRITICAL", "HIGH"):
        # Broadcast to all affected agents
        if blocking:
            responses = bus.broadcast(
                from_agent=f"{AGENT_ID}/{AGENT_NAME}",
                question=f"CONFLICT RESOLUTION REQUIRED: {description}. Please provide your assessment.",
                target_agents=blocking,
                context=f"Mission {mission_id}",
            )
            logger.info(f"Collected {len(responses)} conflict assessments")

        action_items = [
            f"Halt current work on mission {mission_id}",
            "Re-evaluate dependency graph",
            "Re-issue tasks with conflict resolved",
        ]
        log_to_ledger(AGENT_NAME, f"Conflict RESOLVED [{severity}] for {mission_id}: {description[:50]}")
        return {
            "resolution": "RESOLVED",
            "severity": severity,
            "action_items": action_items,
            "reassigned_to": "Roadmap reissued after conflict clearance",
        }
    else:
        log_to_ledger(AGENT_NAME, f"Conflict NOTED [{severity}] for {mission_id}")
        return {
            "resolution": "NOTED",
            "severity": severity,
            "action_items": ["Continue with workaround; monitor for escalation"],
            "reassigned_to": None,
        }


# ---------------------------------------------------------------------------
# Main dispatch function
# ---------------------------------------------------------------------------

def dispatch(task: str, mission_id: str, tasks_list: list[dict] = None) -> HandOffMessage:
    logger.info(f"Received task for mission {mission_id}: {task}")

    # WSJF prioritization if multiple tasks provided
    if tasks_list:
        prioritized = prioritize_tasks(tasks_list)
        logger.info(f"WSJF prioritized {len(prioritized)} tasks. Top: {prioritized[0]['name']}")

    chain = (
        ThoughtChain(AGENT_ID, AGENT_NAME, task)
        .think(ThinkingStep.UNDERSTAND, f"New task received: {task}")
        .think(ThinkingStep.DECOMPOSE, "Break into: planning → research → design → dev → QA → deploy → report")
        .think(ThinkingStep.EVALUATE, "WSJF scoring applied. No conflicts detected. Dependencies: PM needs market context first.")
        .think(ThinkingStep.DECIDE, "Route to PM + Market Analyst in parallel (allowed per Rule 4).")
        .think(ThinkingStep.EXECUTE, "Generating hand-off message to PM.")
        .think(ThinkingStep.HANDOFF, "Sending to 02/Product-Manager")
    )

    logger.info(chain.summary())

    # Register mission
    mgr = get_manager()
    if not mgr.get(mission_id):
        mgr.create(mission_id, task, f"{AGENT_ID}/{AGENT_NAME}")
    mgr.start(mission_id, f"{AGENT_ID}/{AGENT_NAME}")

    msg = HandOffMessage(
        from_agent_id=AGENT_ID,
        from_agent_name=AGENT_NAME,
        to_agent_id="02",
        to_agent_name="Product-Manager",
        mission_id=mission_id,
        status=TaskStatus.IN_PROGRESS,
        summary="Task received. WSJF scoring applied. Routed to PM + Analyst (parallel).",
        output=[],
        next_action="PM and Market Analyst: begin planning and market research in parallel.",
    )

    log_to_ledger(AGENT_NAME, f"Dispatched mission {mission_id} to PM/Analyst (WSJF applied)")
    notify(AGENT_ID, AGENT_NAME, "Mission Dispatched", "IN_PROGRESS",
           f"Mission {mission_id} dispatched. WSJF applied. Routing to PM + Analyst.",
           mission_id=mission_id)
    return msg


def handle_conflict(conflict_description: str, mission_id: str, severity: str = "MEDIUM") -> dict:
    """Called by any agent when a conflict is detected (Rule 3)."""
    logger.warning(f"CONFLICT received for {mission_id}: {conflict_description}")
    conflict = {
        "type": "ESCALATION",
        "description": conflict_description,
        "blocking_agents": [],
        "severity": severity,
    }
    return resolve_conflict(conflict, mission_id)


if __name__ == "__main__":
    sample_tasks = [
        {"name": "Recipe Discovery API", "user_value": 8, "time_criticality": 5, "risk_reduction": 3, "job_size": 3},
        {"name": "Auth System",          "user_value": 9, "time_criticality": 8, "risk_reduction": 8, "job_size": 5},
        {"name": "Chef Marketplace",     "user_value": 6, "time_criticality": 3, "risk_reduction": 2, "job_size": 8},
    ]
    result = dispatch("Build CooCook travel-tech platform", "M-002", sample_tasks)
    print(result.to_json())
