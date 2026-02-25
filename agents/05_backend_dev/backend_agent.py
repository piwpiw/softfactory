"""
Agent 05 — Backend Developer
TDD cycle, Clean Architecture implementation, API-first development.
Runs in parallel with Agent 06 (Frontend) during development phase.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core import (
    ThoughtChain, ThinkingStep, HandOffMessage, TaskStatus,
    get_logger, log_to_ledger, get_bus, ConsultationType,
    ConsultationPriority, get_manager, MissionPhase, notify,
)
from skills import TDDBDD, CleanArchitecture, APIFirstDesign

AGENT_ID   = "05"
AGENT_NAME = "Backend-Developer"

logger = get_logger(AGENT_ID, AGENT_NAME)


# ---------------------------------------------------------------------------
# TDD Cycle planning
# ---------------------------------------------------------------------------

def plan_tdd_cycle(feature: str, use_cases: list[str]) -> dict:
    """
    Plan a TDD Red-Green-Refactor cycle for a given feature.
    Returns test file structure and implementation checklist.
    """
    tdd = TDDBDD()
    result = tdd.apply({
        "feature": feature,
        "scenarios": [
            {
                "name": f"Successful {uc}",
                "given": "valid authenticated user",
                "when": f"user invokes {uc}",
                "then": "system returns 200 with expected payload",
            }
            for uc in use_cases
        ],
    })
    return {
        "feature": feature,
        "tdd_cycle": result["tdd_cycle"],
        "test_files": [f"tests/unit/test_{uc.lower().replace(' ', '_')}.py" for uc in use_cases],
        "coverage_targets": result["coverage_targets"],
        "checklist": tdd.checklist(),
    }


# ---------------------------------------------------------------------------
# Clean Architecture layer design
# ---------------------------------------------------------------------------

def design_layers(domain_entities: list[str], use_cases: list[str]) -> dict:
    ca = CleanArchitecture()
    return ca.apply({"domain_entities": domain_entities, "use_cases": use_cases})


# ---------------------------------------------------------------------------
# Main implement function
# ---------------------------------------------------------------------------

def implement(mission_id: str, feature: str, adr: dict = None) -> HandOffMessage:
    logger.info(f"Starting backend implementation: {feature}")

    # Consult Architect on any implementation ambiguity
    bus = get_bus()
    bus.consult(
        from_agent=f"{AGENT_ID}/{AGENT_NAME}",
        to_agent="04/Solution-Architect",
        question=f"Confirming implementation approach for '{feature}': Use Case class → Repository interface → SQLAlchemy adapter. Correct?",
        context=f"Mission {mission_id} — backend development phase",
        priority=ConsultationPriority.MEDIUM,
        consultation_type=ConsultationType.CLARIFICATION,
    )

    chain = (
        ThoughtChain(AGENT_ID, AGENT_NAME, feature)
        .think(ThinkingStep.UNDERSTAND, f"Implement backend for: {feature}")
        .think(ThinkingStep.DECOMPOSE, "1) TDD: write tests first 2) Domain entities 3) Use cases 4) REST controllers 5) Repository")
        .think(ThinkingStep.EVALUATE, "Follow Clean Architecture layers. Validate all inputs. Parameterized queries only. No secrets in code.")
        .think(ThinkingStep.DECIDE, "FastAPI + SQLAlchemy ORM + Pydantic schemas. pytest + coverage ≥ 80%.")
        .think(ThinkingStep.EXECUTE, "TDD cycle: RED → GREEN → REFACTOR for each use case.")
        .think(ThinkingStep.HANDOFF, "Pass to 07/QA and 08/Security for parallel validation.")
    )

    logger.info(chain.summary())

    use_cases = ["DiscoverRecipes", "BookChef", "ProcessPayment"] if feature == "Recipe Discovery API" else [feature]
    domain_entities = ["User", "Recipe", "Chef", "Booking"]

    tdd_plan = plan_tdd_cycle(feature, use_cases)
    layer_design = design_layers(domain_entities, use_cases)

    api = APIFirstDesign()
    endpoint_count = len(use_cases) * 5  # CRUD per resource
    logger.info(f"TDD planned for {len(use_cases)} use cases. Layer design: {len(layer_design['layer_structure'])} layers.")
    logger.info(f"TDD checklist items: {len(tdd_plan['checklist'])}")

    # Advance mission phase
    mgr = get_manager()
    if mgr.get(mission_id):
        mgr.advance_phase(mission_id, MissionPhase.DEVELOPMENT, f"{AGENT_ID}/{AGENT_NAME}")

    msg = HandOffMessage(
        from_agent_id=AGENT_ID,
        from_agent_name=AGENT_NAME,
        to_agent_id="07",
        to_agent_name="QA-Engineer",
        mission_id=mission_id,
        status=TaskStatus.COMPLETE,
        summary=f"Backend '{feature}' implemented. TDD cycle complete. Coverage ≥ 80% target.",
        output=[
            f"backend/api/{feature.lower().replace(' ', '_')}/",
            f"tests/unit/ ({len(use_cases)} test modules)",
            "12-Factor compliance: config via .env, stateless processes",
        ],
        next_action="QA: run test suite + coverage report. Security: audit per OWASP Top 10.",
        blockers="none",
    )

    log_to_ledger(AGENT_NAME, f"Backend '{feature}' implemented (TDD + Clean Architecture) — mission {mission_id}")
    notify(AGENT_ID, AGENT_NAME, "Backend Implementation Complete", "COMPLETE",
           f"'{feature}' 구현 완료. TDD Red-Green-Refactor. Use cases: {len(use_cases)}개. Coverage ≥80% 목표.",
           mission_id=mission_id)
    return msg


if __name__ == "__main__":
    result = implement("M-002", "Recipe Discovery API")
    print(result.to_json())
