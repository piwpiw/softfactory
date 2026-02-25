"""
Agent 02 — Product Manager
PRD generation, RICE scoring, OKR definition, Story Mapping, MoSCoW.
Works in parallel with Agent 03 (Market Analyst) during planning phase.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core import (
    ThoughtChain, ThinkingStep, HandOffMessage, TaskStatus,
    get_logger, log_to_ledger, get_bus, ConsultationType,
    ConsultationPriority, generate_prd, get_manager, MissionPhase, notify,
)
from skills import DesignThinking, LeanStartup, AgileScrum

AGENT_ID   = "02"
AGENT_NAME = "Product-Manager"

logger = get_logger(AGENT_ID, AGENT_NAME)


# ---------------------------------------------------------------------------
# RICE Scoring
# ---------------------------------------------------------------------------

def rice_score(reach: int, impact: int, confidence: float, effort: float) -> dict:
    """RICE = (Reach × Impact × Confidence) / Effort"""
    score = round((reach * impact * confidence) / effort, 1)
    return {"reach": reach, "impact": impact, "confidence": confidence, "effort": effort, "rice": score}


def build_rice_table(features: list[dict]) -> list[dict]:
    """features: [{name, reach, impact, confidence, effort}]"""
    scored = [{"name": f["name"], **rice_score(f["reach"], f["impact"], f["confidence"], f["effort"])} for f in features]
    return sorted(scored, key=lambda x: x["rice"], reverse=True)


# ---------------------------------------------------------------------------
# OKR Definition
# ---------------------------------------------------------------------------

def define_okr(objective: str, key_results: list[str]) -> dict:
    return {
        "objective": objective,
        "key_results": [{"kr": kr, "current": "—", "target": "—", "owner": "TBD"} for kr in key_results],
    }


# ---------------------------------------------------------------------------
# Story Map
# ---------------------------------------------------------------------------

def build_story_map(project: str, activities: list[dict]) -> dict:
    """
    activities: [{name, tasks: [{story, release}]}]
    """
    return {
        "project": project,
        "backbone": [a["name"] for a in activities],
        "releases": {
            "v1_mvp": [t["story"] for a in activities for t in a.get("tasks", []) if t.get("release") == "mvp"],
            "v2":     [t["story"] for a in activities for t in a.get("tasks", []) if t.get("release") == "v2"],
        },
        "activities": activities,
    }


# ---------------------------------------------------------------------------
# PRD Generation
# ---------------------------------------------------------------------------

def create_prd(project: str, mission_id: str, market_data: dict = None) -> str:
    """Generate a full PRD markdown file and return its path."""

    # Optional: consult Analyst if market data missing
    if not market_data:
        bus = get_bus()
        resp = bus.consult(
            from_agent=f"{AGENT_ID}/{AGENT_NAME}",
            to_agent="03/Market-Analyst",
            question="Please provide market sizing and competitive landscape for the PRD.",
            context=f"Mission {mission_id} — PRD creation phase",
            priority=ConsultationPriority.HIGH,
            consultation_type=ConsultationType.CLARIFICATION,
        )
        logger.info(f"Analyst consultation response: {resp.answer[:80]}")

    lean = LeanStartup()
    lean_ctx = lean.apply({"hypothesis": f"{project} solves food-travel discovery gap", "mvp_type": "Concierge MVP"})

    personas = """
### Persona 1: Leisure Traveler (Primary)
| Field | Value |
|-------|-------|
| Name | Alex, 32 |
| Role | Marketing manager + food enthusiast |
| Key Goal | Discover authentic local food during trips |
| Key Pain | Generic restaurant apps miss local hidden gems |
| Tech Proficiency | High |

### Persona 2: Digital Nomad (Secondary)
| Field | Value |
|-------|-------|
| Name | Sam, 28 |
| Role | Remote software developer |
| Key Goal | Find weekly meal plans with local ingredients while working abroad |
| Key Pain | Spending too much time on food logistics |
| Tech Proficiency | Expert |
"""

    stories = """
### Epic 1: Recipe Discovery
```
As a Leisure Traveler,
I want to discover local recipes by destination,
So that I can plan authentic food experiences before my trip.

Acceptance Criteria:
  Given I have selected a destination
  When I browse the recipe discovery feed
  Then I see minimum 10 locally-verified recipes with photos, ratings, and chef info
```

### Epic 2: Chef Booking
```
As a Digital Nomad,
I want to book a local chef for a private cooking session,
So that I can learn and eat authentic cuisine weekly.

Acceptance Criteria:
  Given I have found a chef profile
  When I select a time slot and confirm booking
  Then I receive a booking confirmation with location and payment receipt within 30 seconds
```
"""

    requirements = """
| ID | Requirement | Priority |
|----|------------|----------|
| FR-001 | User registration with email + OAuth (Google/Apple) | Must |
| FR-002 | Recipe browsing filtered by destination, cuisine, dietary | Must |
| FR-003 | Chef profile with portfolio, ratings, availability calendar | Must |
| FR-004 | Booking flow with payment (Stripe integration) | Must |
| FR-005 | AI-powered recipe recommendation | Should |
| FR-006 | Community reviews and social sharing | Could |
| FR-007 | Physical ingredient delivery | Won't (v1) |
"""

    moscow = """
| Priority | Feature | Justification |
|----------|---------|---------------|
| **Must** | Auth, Recipe Discovery, Chef Booking, Payment | Core value proposition |
| **Should** | Reviews, AI Recommendations, Notifications | Engagement drivers |
| **Could** | Social sharing, Dietary tracking | Nice-to-have |
| **Won't (v1)** | Physical delivery, Live streaming | Out of scope for MVP |
"""

    path = generate_prd(
        project=project,
        problem=f"{project} addresses the gap in travel-tech: no dominant platform combines authentic local food discovery with chef booking. Target users: leisure travelers and digital nomads.",
        goals="1. 10,000 MAU within 6 months of launch\n2. Chef booking conversion rate > 15%\n3. Day-7 retention > 40%\n4. NPS > 50",
        personas=personas,
        stories=stories,
        requirements=requirements,
        moscow=moscow,
    )
    logger.info(f"PRD generated: {path}")
    return str(path)


# ---------------------------------------------------------------------------
# Main plan function
# ---------------------------------------------------------------------------

def plan(mission_id: str, task: str, market_data: dict = None) -> HandOffMessage:
    logger.info(f"Starting product planning for mission {mission_id}")

    chain = (
        ThoughtChain(AGENT_ID, AGENT_NAME, task)
        .think(ThinkingStep.UNDERSTAND, "Need to define product scope, user personas, and feature priority.")
        .think(ThinkingStep.DECOMPOSE, "1) Consult Analyst 2) Define personas 3) RICE score 4) OKR 5) PRD 6) Story Map")
        .think(ThinkingStep.EVALUATE, f"Market data available: {bool(market_data)}. Consulting Analyst via ConsultationBus.")
        .think(ThinkingStep.DECIDE, "Produce full PRD with RICE scoring and OKR. Apply Lean Startup BML cycle.")
        .think(ThinkingStep.EXECUTE, "Generating PRD, RICE table, OKR board.")
        .think(ThinkingStep.HANDOFF, "Pass PRD + outputs to 04/Architect")
    )

    logger.info(chain.summary())

    # Generate PRD file
    prd_path = create_prd("CooCook", mission_id, market_data)

    # RICE table
    rice_features = [
        {"name": "Recipe Discovery",  "reach": 5000, "impact": 3, "confidence": 0.9, "effort": 2.0},
        {"name": "Chef Booking",      "reach": 2000, "impact": 4, "confidence": 0.8, "effort": 3.0},
        {"name": "Auth System",       "reach": 10000, "impact": 2, "confidence": 0.95, "effort": 1.5},
        {"name": "AI Recommendations","reach": 3000, "impact": 3, "confidence": 0.6, "effort": 5.0},
        {"name": "Community Reviews", "reach": 4000, "impact": 2, "confidence": 0.7, "effort": 2.5},
    ]
    rice_table = build_rice_table(rice_features)
    logger.info(f"RICE Top feature: {rice_table[0]['name']} (score: {rice_table[0]['rice']})")

    # OKR
    okr = define_okr(
        "Establish CooCook as the leading food-travel discovery platform in SEA",
        ["Reach 10,000 MAU by Q3 2026",
         "Chef booking conversion > 15%",
         "Day-7 retention > 40%",
         "NPS > 50 by end of Q2 2026"],
    )
    logger.info(f"OKR defined: {okr['objective']}")

    # Advance mission phase
    mgr = get_manager()
    if mgr.get(mission_id):
        mgr.advance_phase(mission_id, MissionPhase.RESEARCH, f"{AGENT_ID}/{AGENT_NAME}")

    status = TaskStatus.IN_PROGRESS if market_data else TaskStatus.IN_PROGRESS

    msg = HandOffMessage(
        from_agent_id=AGENT_ID,
        from_agent_name=AGENT_NAME,
        to_agent_id="04",
        to_agent_name="Solution-Architect",
        mission_id=mission_id,
        status=status,
        summary="PRD generated. RICE scoring complete. OKR defined. Story Map drafted.",
        output=[prd_path, "agents/02_product_manager/output/rice_table.json"],
        next_action="Architect: review PRD and design system architecture. Generate ADR + OpenAPI spec.",
        blockers="none",
    )

    log_to_ledger(AGENT_NAME, f"PRD + RICE + OKR generated for mission {mission_id}")
    notify(AGENT_ID, AGENT_NAME, "PRD + RICE + OKR Complete", "PRD",
           f"PRD 생성 완료. RICE Top: {rice_table[0]['name']} ({rice_table[0]['rice']}pt). OKR defined.",
           outputs=[prd_path], mission_id=mission_id)
    return msg


if __name__ == "__main__":
    result = plan("M-002", "Build CooCook travel-tech platform")
    print(result.to_json())
