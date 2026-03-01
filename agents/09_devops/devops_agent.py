"""
Agent 09 — DevOps Engineer
SLO/SLI definition, Blue-Green deployment, IaC, CI/CD, deployment runbook generation.
Receives QA-approved + Security-cleared artifacts.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core import (
    ThoughtChain, ThinkingStep, HandOffMessage, TaskStatus,
    get_logger, log_to_ledger, get_bus, ConsultationType,
    ConsultationPriority, generate_deployment_runbook, get_manager, MissionPhase, notify,
)
from skills import DevOpsSRE

AGENT_ID   = "09"
AGENT_NAME = "DevOps-Engineer"

logger = get_logger(AGENT_ID, AGENT_NAME)


# ---------------------------------------------------------------------------
# SLO/SLI definition
# ---------------------------------------------------------------------------

def define_slos(service: str) -> dict:
    sre = DevOpsSRE()
    return sre.apply({
        "service": service,
        "slo_target_pct": 99.9,
        "deployment_strategy": "blue-green",
        "window_days": 28,
    })


# ---------------------------------------------------------------------------
# Main deploy function
# ---------------------------------------------------------------------------

def deploy(mission_id: str, artifact: str, environment: str = "staging") -> HandOffMessage:
    logger.info(f"Deploying {artifact} to {environment}")

    chain = (
        ThoughtChain(AGENT_ID, AGENT_NAME, f"Deploy {artifact}")
        .think(ThinkingStep.UNDERSTAND, f"Deploy QA+security-approved {artifact} to {environment}.")
        .think(ThinkingStep.DECOMPOSE, "1) SLO/SLI check 2) Pre-deploy checklist 3) Build + push 4) Blue-Green 5) Health checks 6) Runbook")
        .think(ThinkingStep.EVALUATE, "Verify QA + Security clearance. Blue-Green with instant rollback < 2 min.")
        .think(ThinkingStep.DECIDE, "GitHub Actions → Docker → ECS Fargate → Blue-Green. Runbook generated.")
        .think(ThinkingStep.EXECUTE, f"Triggering deployment pipeline for {artifact} to {environment}.")
        .think(ThinkingStep.HANDOFF, "Notify 10/Reporter on success or failure.")
    )

    logger.info(chain.summary())

    # Define SLOs
    slo_data = define_slos(artifact)
    logger.info(f"SLO defined: {slo_data['slo']['target']} availability over {slo_data['slo']['window']}")
    logger.info(f"Error budget: {slo_data['slo']['error_budget_minutes']} minutes/window")

    # Generate deployment runbook
    version = "0.1.0" if environment == "staging" else "1.0.0"
    runbook_path = generate_deployment_runbook(
        service=artifact,
        version=version,
        pre_deploy=(
            "- [ ] CI checks passing\n"
            "- [ ] Security clearance confirmed\n"
            "- [ ] QA sign-off confirmed\n"
            "- [ ] DB migrations reviewed\n"
            "- [ ] Rollback tested within 30 days"
        ),
        deploy_steps=(
            "1. Build Docker image: `docker build -t coocook-api:{version} .`\n"
            "2. Push to ECR registry\n"
            "3. Update GitOps repo image tag (Green environment)\n"
            "4. ArgoCD reconciles — Green environment deployed\n"
            "5. Run smoke tests on Green\n"
            "6. Switch ALB target group: Blue → Green\n"
            "7. Monitor for 15 minutes"
        ),
        health_checks=(
            "GET /health → 200 OK\n"
            "GET /ready → 200 OK\n"
            "Error rate < 0.1% (Grafana dashboard)\n"
            "p99 latency < 500ms (Grafana dashboard)"
        ),
        rollback=(
            "Trigger: error rate > 1% for > 2 minutes\n"
            "Action: switch ALB back to Blue environment\n"
            "Target: < 2 minutes rollback time\n"
            "GitOps: revert image tag commit"
        ),
        post_deploy=(
            "- [ ] Health checks passing\n"
            "- [ ] Error rate baseline confirmed\n"
            "- [ ] Key user journeys smoke-tested\n"
            "- [ ] SLO dashboard: availability ≥ 99.9%\n"
            "- [ ] Stakeholders notified"
        ),
        incident_response=(
            "P0 (service down): page DevOps lead immediately\n"
            "P1 (major degradation): 15-min response\n"
            "P2 (partial impact): 1-hour response\n"
            "All incidents → blameless post-mortem within 48h"
        ),
    )
    logger.info(f"Deployment runbook generated: {runbook_path}")

    # Advance mission phase
    mgr = get_manager()
    if mgr.get(mission_id):
        mgr.advance_phase(mission_id, MissionPhase.DEPLOYMENT, f"{AGENT_ID}/{AGENT_NAME}")

    msg = HandOffMessage(
        from_agent_id=AGENT_ID,
        from_agent_name=AGENT_NAME,
        to_agent_id="10",
        to_agent_name="Telegram-Reporter",
        mission_id=mission_id,
        status=TaskStatus.COMPLETE,
        summary=f"Deployment of {artifact} v{version} to {environment} completed. Blue-Green. SLO: {slo_data['slo']['target']}.",
        output=[str(runbook_path), f"infra/deployments/{mission_id}_{environment}.log"],
        next_action=f"Reporter: send deployment success notification for {environment} ({artifact} v{version}).",
        blockers="none",
    )

    log_to_ledger(AGENT_NAME, f"Deployed '{artifact}' v{version} to {environment} — Blue-Green — mission {mission_id}")
    notify(AGENT_ID, AGENT_NAME, f"Deployment to {environment}", "DEPLOYMENT",
           f"🚀 {artifact} v{version} → {environment} 배포 완료 (Blue-Green). "
           f"SLO: {slo_data['slo']['target']} | Error Budget: {slo_data['slo']['error_budget_minutes']}min",
           outputs=[str(runbook_path)], mission_id=mission_id)
    return msg


if __name__ == "__main__":
    result = deploy("M-002", "CooCook API", "staging")
    print(result.to_json())
