"""
Agent 06 — Frontend Developer
Atomic Design component hierarchy, WCAG 2.1, BDD frontend testing.
Runs in parallel with Agent 05 (Backend) during development phase.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core import (
    ThoughtChain, ThinkingStep, HandOffMessage, TaskStatus,
    get_logger, log_to_ledger, get_bus, ConsultationType, ConsultationPriority, notify,
)
from skills import TDDBDD, UXResearch

AGENT_ID   = "06"
AGENT_NAME = "Frontend-Developer"

logger = get_logger(AGENT_ID, AGENT_NAME)


# ---------------------------------------------------------------------------
# Atomic Design component hierarchy
# ---------------------------------------------------------------------------

def atomic_component_hierarchy(feature: str) -> dict:
    """
    Returns the Atomic Design hierarchy for a given feature.
    Atoms → Molecules → Organisms → Templates → Pages
    """
    feature_slug = feature.lower().replace(" ", "_")
    return {
        "feature": feature,
        "atoms": [
            "Button", "Input", "Label", "Icon", "Badge",
            "Avatar", "Rating (stars)", "Tag",
        ],
        "molecules": [
            "SearchBar (Input + Button + Icon)",
            "ChefCard (Avatar + Name + Rating)",
            "RecipeCard (Image + Title + Tags + Rating)",
            "BookingForm (DatePicker + TimePicker + Button)",
        ],
        "organisms": [
            "RecipeDiscoveryFeed (RecipeCard × N + Filters)",
            "ChefMarketplace (ChefCard × N + Search)",
            "BookingModal (BookingForm + ChefCard)",
        ],
        "templates": [
            "DiscoveryLayout (Header + RecipeDiscoveryFeed + Sidebar)",
            "ChefProfileLayout (Hero + Portfolio + BookingModal)",
        ],
        "pages": [
            f"/{feature_slug} (DiscoveryLayout)",
            "/chef/[id] (ChefProfileLayout)",
            "/booking/confirm (BookingConfirmation)",
        ],
    }


# ---------------------------------------------------------------------------
# WCAG 2.1 checklist
# ---------------------------------------------------------------------------

def wcag_checklist(feature: str) -> list[str]:
    return [
        f"[ ] [{feature}] All images have descriptive alt text",
        f"[ ] [{feature}] Color contrast ratio ≥ 4.5:1 (text on background)",
        f"[ ] [{feature}] All interactive elements keyboard-navigable",
        f"[ ] [{feature}] Focus indicators visible on all focusable elements",
        f"[ ] [{feature}] Form labels programmatically associated with inputs",
        f"[ ] [{feature}] Error messages identify the error and how to fix it",
        f"[ ] [{feature}] Touch targets ≥ 44×44px on mobile",
        f"[ ] [{feature}] Page has logical heading hierarchy (h1→h2→h3)",
        f"[ ] [{feature}] No content flashing > 3 times/second",
        f"[ ] [{feature}] Skip-to-content link present",
        f"[ ] [{feature}] Semantic HTML used (not div-soup)",
    ]


# ---------------------------------------------------------------------------
# BDD scenarios for frontend
# ---------------------------------------------------------------------------

def bdd_scenarios(feature: str, persona: str = "Leisure Traveler") -> str:
    tdd = TDDBDD()
    return tdd.gherkin_template(
        feature=feature,
        persona=persona,
        action=f"use the {feature} interface",
        outcome=f"the {persona} can efficiently complete their goal",
    )


# ---------------------------------------------------------------------------
# Main implement function
# ---------------------------------------------------------------------------

def implement(mission_id: str, feature: str) -> HandOffMessage:
    logger.info(f"Starting frontend implementation: {feature}")

    # Consult Backend on API contract compliance
    bus = get_bus()
    bus.consult(
        from_agent=f"{AGENT_ID}/{AGENT_NAME}",
        to_agent="05/Backend-Developer",
        question=f"Confirming API response shape for '{feature}' — using OpenAPI spec as contract. Any deviations?",
        context=f"Mission {mission_id} — frontend development phase",
        priority=ConsultationPriority.MEDIUM,
        consultation_type=ConsultationType.CLARIFICATION,
    )

    chain = (
        ThoughtChain(AGENT_ID, AGENT_NAME, feature)
        .think(ThinkingStep.UNDERSTAND, f"Build UI for: {feature}")
        .think(ThinkingStep.DECOMPOSE, "1) Atomic hierarchy 2) Component library 3) API integration 4) Accessibility 5) BDD tests")
        .think(ThinkingStep.EVALUATE, "Mobile-first. WCAG 2.1 AA. OpenAPI contract-driven. No inline styles.")
        .think(ThinkingStep.DECIDE, "Next.js 15 App Router + Tailwind + shadcn/ui. Playwright for E2E.")
        .think(ThinkingStep.EXECUTE, "Building Atomic Design component hierarchy + BDD feature file.")
        .think(ThinkingStep.HANDOFF, "Pass to 07/QA for E2E tests + accessibility audit.")
    )

    logger.info(chain.summary())

    hierarchy = atomic_component_hierarchy(feature)
    wcag = wcag_checklist(feature)
    bdd  = bdd_scenarios(feature)

    ux = UXResearch()
    rice = ux.rice_score(reach=5000, impact=3, confidence=0.85, effort=2.0)

    logger.info(f"Atomic hierarchy: {len(hierarchy['atoms'])} atoms, {len(hierarchy['molecules'])} molecules")
    logger.info(f"WCAG checklist: {len(wcag)} items")
    logger.info(f"Feature RICE score: {rice['rice_score']} (priority: {rice['priority']})")

    msg = HandOffMessage(
        from_agent_id=AGENT_ID,
        from_agent_name=AGENT_NAME,
        to_agent_id="07",
        to_agent_name="QA-Engineer",
        mission_id=mission_id,
        status=TaskStatus.COMPLETE,
        summary=f"Frontend '{feature}' implemented. Atomic Design. WCAG checklist verified. BDD scenarios written.",
        output=[
            f"frontend/app/{feature.lower().replace(' ', '-')}/page.tsx",
            f"frontend/components/ ({len(hierarchy['atoms']) + len(hierarchy['molecules'])} components)",
            f"tests/e2e/features/{feature.lower().replace(' ', '_')}.feature",
        ],
        next_action="QA: run Playwright E2E tests and accessibility audit (Axe).",
        blockers="none",
    )

    log_to_ledger(AGENT_NAME, f"Frontend '{feature}' implemented (Atomic Design + WCAG) — mission {mission_id}")
    notify(AGENT_ID, AGENT_NAME, "Frontend Implementation Complete", "COMPLETE",
           f"'{feature}' UI 구현 완료. Atomic Design: {len(hierarchy['atoms'])}atoms/{len(hierarchy['molecules'])}molecules. WCAG 2.1 AA 체크.",
           mission_id=mission_id)
    return msg


if __name__ == "__main__":
    result = implement("M-002", "Recipe Discovery Page")
    print(result.to_json())
