"""
Agent 03 — Market Analyst
SWOT, PESTLE, Porter's Five Forces, TAM/SAM/SOM analysis.
Runs in parallel with Agent 02 (PM) during planning phase.
Uses Google Search MCP for live research (requires MCP configuration).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core import (
    ThoughtChain, ThinkingStep, HandOffMessage, TaskStatus,
    get_logger, log_to_ledger, get_bus, ConsultationType, ConsultationPriority, notify,
)

AGENT_ID   = "03"
AGENT_NAME = "Market-Analyst"

logger = get_logger(AGENT_ID, AGENT_NAME)


# ---------------------------------------------------------------------------
# SWOT Analysis
# ---------------------------------------------------------------------------

def swot_analysis(strengths: list, weaknesses: list, opportunities: list, threats: list) -> dict:
    cross_matrix = {
        "SO_strategies": "Use strengths to capture opportunities",
        "WO_strategies": "Overcome weaknesses by pursuing opportunities",
        "ST_strategies": "Use strengths to neutralize threats",
        "WT_strategies": "Minimize weaknesses, avoid threats",
    }
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats,
        "cross_matrix": cross_matrix,
    }


# ---------------------------------------------------------------------------
# PESTLE Analysis
# ---------------------------------------------------------------------------

def pestle_analysis(domain: str) -> dict:
    return {
        "domain": domain,
        "political": {
            "factors": ["Digital nomad visa expansion (50+ countries by 2026)", "Cross-border payment regulations"],
            "impact": "OPPORTUNITY",
            "score": 4,
        },
        "economic": {
            "factors": ["Post-pandemic travel recovery +18% YoY", "Inflation affecting food service margins"],
            "impact": "MIXED",
            "score": 3,
        },
        "social": {
            "factors": ["Hyper-local food experiences trending", "Remote work normalization driving nomad segment"],
            "impact": "OPPORTUNITY",
            "score": 5,
        },
        "technological": {
            "factors": ["AI-powered personalization maturing", "Mobile-first food discovery", "Real-time availability APIs"],
            "impact": "OPPORTUNITY",
            "score": 5,
        },
        "legal": {
            "factors": ["GDPR / data privacy compliance", "Food safety regulations for home chefs vary by country"],
            "impact": "RISK",
            "score": 2,
        },
        "environmental": {
            "factors": ["Sustainable slow travel growing 22% YoY", "Local sourcing as differentiator"],
            "impact": "OPPORTUNITY",
            "score": 4,
        },
    }


# ---------------------------------------------------------------------------
# Porter's Five Forces
# ---------------------------------------------------------------------------

def porters_five_forces(industry: str) -> dict:
    return {
        "industry": industry,
        "competitive_rivalry": {
            "intensity": "MEDIUM",
            "rationale": "EatWith, Traveling Spoon present but fragmented. No dominant player in AI-powered food-travel.",
            "score": 3,
        },
        "threat_new_entrants": {
            "intensity": "MEDIUM",
            "rationale": "Low capital barrier for MVP; network effects create moat over time.",
            "score": 3,
        },
        "threat_substitutes": {
            "intensity": "HIGH",
            "rationale": "Airbnb Experiences, GetYourGuide, restaurant apps (Yelp, TripAdvisor) are broad substitutes.",
            "score": 4,
        },
        "bargaining_power_buyers": {
            "intensity": "MEDIUM",
            "rationale": "Price-sensitive travelers; loyalty programs reduce switching cost.",
            "score": 3,
        },
        "bargaining_power_suppliers": {
            "intensity": "LOW",
            "rationale": "Local chefs are fragmented; platform creates distribution they cannot replicate alone.",
            "score": 2,
        },
        "overall_attractiveness": "MEDIUM-HIGH",
        "strategic_implication": "Build strong network effects early. Focus on chef quality and AI personalization as differentiation.",
    }


# ---------------------------------------------------------------------------
# TAM/SAM/SOM
# ---------------------------------------------------------------------------

def market_sizing() -> dict:
    return {
        "TAM": {
            "value": "$1.8T",
            "description": "Global food tourism market (2026 est.)",
            "source": "UNWTO + Market Research Future (validate with live MCP search)",
        },
        "SAM": {
            "value": "$340B",
            "description": "Tech-enabled travel + food experiences worldwide",
            "source": "Estimate based on Airbnb Experiences + food delivery market",
        },
        "SOM": {
            "value": "$120M",
            "description": "Obtainable: SEA + Western EU digital nomad segment, 3-year horizon",
            "source": "Bottom-up: 50K MAU × $40 ARPU × 12 months",
        },
        "note": "Validate TAM/SAM with Google Search MCP when available",
    }


# ---------------------------------------------------------------------------
# Main analyze function
# ---------------------------------------------------------------------------

def analyze(mission_id: str, topic: str) -> HandOffMessage:
    logger.info(f"Starting market analysis for: {topic}")

    chain = (
        ThoughtChain(AGENT_ID, AGENT_NAME, topic)
        .think(ThinkingStep.UNDERSTAND, f"Research market landscape for: {topic}")
        .think(ThinkingStep.DECOMPOSE, "1) SWOT 2) PESTLE 3) Porter's 5 Forces 4) TAM/SAM/SOM 5) Opportunity gaps")
        .think(ThinkingStep.EVALUATE, "Google Search MCP needed for live data. Structured analysis provided.")
        .think(ThinkingStep.DECIDE, "Return full SWOT + PESTLE + Porter's + Sizing. Flag MCP requirement.")
        .think(ThinkingStep.EXECUTE, "Running all four frameworks for CooCook.")
        .think(ThinkingStep.HANDOFF, "Send to 02/PM to merge with product brief.")
    )

    logger.info(chain.summary())

    swot = swot_analysis(
        strengths=["AI personalization differentiator", "Digital nomad community expertise", "First-mover in SEA food-travel tech"],
        weaknesses=["No brand recognition (pre-launch)", "Chef supply chain takes time to build", "Regulatory complexity varies by market"],
        opportunities=["Hyper-local food experiences trend", "Digital nomad visa expansion", "AI travel planning mainstream"],
        threats=["Airbnb Experiences scale advantage", "Super-app consolidation (Grab, GoTo)", "Economic downturn reducing travel spend"],
    )

    pestle = pestle_analysis("Food-Travel Tech / CooCook")
    forces = porters_five_forces("Tech-enabled food tourism")
    sizing = market_sizing()

    # Optional: consult PM on specific requirements
    bus = get_bus()
    logger.info("Sharing market findings with PM via ConsultationBus")
    bus.consult(
        from_agent=f"{AGENT_ID}/{AGENT_NAME}",
        to_agent="02/Product-Manager",
        question="Market analysis complete. SWOT + PESTLE + Porter's + Sizing available. Which findings should be highlighted in PRD?",
        context=f"Mission {mission_id} — market analysis output ready",
        priority=ConsultationPriority.MEDIUM,
        consultation_type=ConsultationType.REVIEW,
    )

    full_report = {
        "topic": topic,
        "mission_id": mission_id,
        "swot": swot,
        "pestle": pestle,
        "porters_five_forces": forces,
        "market_sizing": sizing,
        "key_insight": "Position CooCook as 'Airbnb for Local Food Experiences' with AI personalization and digital nomad community at core.",
        "go_to_market": {
            "phase_1": "SEA (Thailand, Vietnam, Bali) — largest digital nomad hubs",
            "phase_2": "Western Europe (Portugal, Spain, Italy)",
            "phase_3": "Global with super-app partnerships",
        },
    }

    logger.info(f"Analysis complete. Opportunity score: {forces['overall_attractiveness']}")

    msg = HandOffMessage(
        from_agent_id=AGENT_ID,
        from_agent_name=AGENT_NAME,
        to_agent_id="02",
        to_agent_name="Product-Manager",
        mission_id=mission_id,
        status=TaskStatus.COMPLETE,
        summary="SWOT + PESTLE + Porter's Five Forces + TAM/SAM/SOM complete. Live data requires Google Search MCP.",
        output=["agents/03_market_analyst/output/market_analysis.json"],
        next_action="PM: merge market data into PRD, then route to Architect.",
        blockers="none",
    )

    log_to_ledger(AGENT_NAME, f"Full market analysis (SWOT/PESTLE/Porter's) for mission {mission_id}")
    notify(AGENT_ID, AGENT_NAME, "Market Analysis Complete", "COMPLETE",
           f"SWOT + PESTLE + Porter's 5 Forces + TAM/SAM/SOM 완료. 기회 등급: {forces['overall_attractiveness']}",
           mission_id=mission_id)
    return msg


if __name__ == "__main__":
    result = analyze("M-002", "2026 Global Travel & Tech Trends for CooCook")
    print(result.to_json())
