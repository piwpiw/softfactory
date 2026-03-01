"""
Agent 04 — Solution Architect
ADR generation, C4 model text diagrams, OpenAPI stub, DDD domain model design.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core import (
    ThoughtChain, ThinkingStep, HandOffMessage, TaskStatus,
    get_logger, log_to_ledger, get_bus, ConsultationType,
    ConsultationPriority, generate_adr, get_manager, MissionPhase, notify,
)
from skills import DomainDrivenDesign, CleanArchitecture, APIFirstDesign

AGENT_ID   = "04"
AGENT_NAME = "Solution-Architect"

logger = get_logger(AGENT_ID, AGENT_NAME)

ARCHITECTURE = {
    "backend":  {"framework": "FastAPI (Python)", "runtime": "Python 3.12"},
    "frontend": {"framework": "Next.js 15 (TypeScript)", "styling": "Tailwind CSS"},
    "database": {"primary": "PostgreSQL 16", "cache": "Redis 7", "search": "Elasticsearch"},
    "ai_layer": {"model": "claude-sonnet-4-6 via Anthropic API",
                 "use_cases": ["recommendations", "itinerary generation", "review summarization"]},
    "infra":    {"cloud": "AWS", "containers": "Docker + ECS Fargate", "ci_cd": "GitHub Actions"},
    "auth":     "Auth0 (OAuth2 / JWT)",
    "storage":  "AWS S3 (media)",
    "monitoring": "Datadog + Prometheus/Grafana",
}


# ---------------------------------------------------------------------------
# C4 Model (text diagrams)
# ---------------------------------------------------------------------------

def c4_context_diagram(system: str, users: list, external_systems: list) -> str:
    user_lines = "\n".join(f"  [{u}] --> [{system}]" for u in users)
    ext_lines  = "\n".join(f"  [{system}] --> [{e}]" for e in external_systems)
    return (
        f"## C4 Level 1: System Context — {system}\n\n"
        f"```\n{user_lines}\n{ext_lines}\n```\n\n"
        f"Actors: {', '.join(users)}\n"
        f"External Systems: {', '.join(external_systems)}\n"
    )


def c4_container_diagram(system: str, containers: list) -> str:
    lines = "\n".join(f"  [{c['name']} | {c['tech']}]: {c['desc']}" for c in containers)
    return f"## C4 Level 2: Container Diagram — {system}\n\n```\n{lines}\n```\n"


# ---------------------------------------------------------------------------
# Main design function
# ---------------------------------------------------------------------------

def design(mission_id: str, prd_summary: str = "") -> HandOffMessage:
    logger.info(f"Starting architecture design for mission {mission_id}")

    chain = (
        ThoughtChain(AGENT_ID, AGENT_NAME, "System Architecture Design")
        .think(ThinkingStep.UNDERSTAND, "Design scalable architecture for CooCook travel-food platform.")
        .think(ThinkingStep.DECOMPOSE, "1) Domain model (DDD) 2) C4 diagrams 3) ADR 4) OpenAPI spec 5) Clean Architecture")
        .think(ThinkingStep.EVALUATE, "Consult Backend + Frontend on feasibility. Must support: marketplace, AI, geo-search, bookings.")
        .think(ThinkingStep.DECIDE, "Modular monolith with Clean Architecture for MVP; extract services at scale.")
        .think(ThinkingStep.EXECUTE, "Generating ADR, C4, OpenAPI stub, domain model.")
        .think(ThinkingStep.HANDOFF, "Pass to Backend + Frontend (parallel execution).")
    )

    logger.info(chain.summary())

    # Consult Backend + Frontend on design feasibility
    bus = get_bus()
    responses = bus.broadcast(
        from_agent=f"{AGENT_ID}/{AGENT_NAME}",
        question="Reviewing proposed Clean Architecture + REST API design for CooCook. Any technical constraints?",
        target_agents=["05/Backend-Developer", "06/Frontend-Developer"],
        context=f"Mission {mission_id} — architecture design phase",
    )
    logger.info(f"Received {len(responses)} feasibility consultations")

    # Apply skills
    ddd = DomainDrivenDesign()
    ddd_output = ddd.apply({
        "domain": "Food-Travel Tech",
        "subdomains": ["User", "Recipe", "Chef", "Booking", "Payment"],
    })
    logger.info(f"DDD: {len(ddd_output['bounded_contexts'])} bounded contexts defined")

    api = APIFirstDesign()
    openapi_stub = api.openapi_stub(
        title="CooCook API",
        version="v1",
        resources=["users", "recipes", "chefs", "bookings"],
    )

    # Generate ADR
    adr_path = generate_adr(
        title="Adopt Clean Architecture with Modular Monolith for CooCook MVP",
        status="ACCEPTED",
        context=(
            "CooCook needs to deliver MVP quickly while maintaining architectural integrity. "
            "Team is small (3-5 devs). We need a structure that prevents spaghetti code but "
            "doesn't over-engineer with premature microservices."
        ),
        decision=(
            "Use Clean Architecture (Domain → Use Cases → Interface Adapters → Frameworks) "
            "within a single deployable unit (modular monolith). "
            "Bounded Contexts map to Python packages. "
            "Extract to microservices when a context exceeds 2 devs or 10k req/min."
        ),
        consequences=(
            "Positive: Fast iteration, single deployment, easy debugging.\n"
            "Negative: Eventual service extraction requires careful refactoring.\n"
            "Neutral: Team must be disciplined about layer dependency rules."
        ),
        alternatives=(
            "Option A: Microservices from day 1 — rejected (premature complexity for 3-dev team).\n"
            "Option B: Django monolith — rejected (no boundary enforcement without Clean Architecture)."
        ),
        adr_number=1,
    )
    logger.info(f"ADR generated: {adr_path}")

    # C4 diagrams
    c4_ctx = c4_context_diagram(
        system="CooCook Platform",
        users=["Leisure Traveler", "Digital Nomad", "Local Chef"],
        external_systems=["Stripe", "Google Maps API", "SendGrid", "Telegram Bot API"],
    )

    containers = [
        {"name": "Web App",      "tech": "Next.js/React",  "desc": "SPA served via CDN"},
        {"name": "Mobile App",   "tech": "React Native",   "desc": "iOS + Android"},
        {"name": "API Server",   "tech": "FastAPI/Python", "desc": "REST API (Clean Architecture)"},
        {"name": "Database",     "tech": "PostgreSQL",     "desc": "Primary data store"},
        {"name": "Cache",        "tech": "Redis",          "desc": "Session + rate limiting"},
        {"name": "File Storage", "tech": "S3-compatible",  "desc": "Recipe photos, chef portfolios"},
    ]
    c4_cont = c4_container_diagram("CooCook Platform", containers)
    logger.info("C4 Context + Container diagrams generated")

    # Advance mission phase
    mgr = get_manager()
    if mgr.get(mission_id):
        mgr.advance_phase(mission_id, MissionPhase.DESIGN, f"{AGENT_ID}/{AGENT_NAME}")

    msg = HandOffMessage(
        from_agent_id=AGENT_ID,
        from_agent_name=AGENT_NAME,
        to_agent_id="05",
        to_agent_name="Backend-Developer",
        mission_id=mission_id,
        status=TaskStatus.IN_PROGRESS,
        summary="ADR-0001 generated. C4 diagrams produced. OpenAPI stub ready. DDD bounded contexts defined.",
        output=[str(adr_path), "docs/generated/openapi.yaml", "Architecture: Clean Architecture + Modular Monolith"],
        next_action="Backend + Frontend (parallel): implement per Clean Architecture. Backend implements OpenAPI spec.",
        blockers="none",
    )

    log_to_ledger(AGENT_NAME, f"Architecture designed for mission {mission_id} — ADR-0001, C4, OpenAPI spec")
    notify(AGENT_ID, AGENT_NAME, "Architecture Design Complete", "ADR",
           f"ADR-0001 확정 (Clean Architecture + Modular Monolith). C4 다이어그램 + OpenAPI stub 생성.",
           outputs=[str(adr_path)], mission_id=mission_id)
    return msg


if __name__ == "__main__":
    result = design("M-002", "CooCook travel-tech — food discovery + chef booking")
    print(result.to_json())
    print("\nTech Stack:", ARCHITECTURE)
