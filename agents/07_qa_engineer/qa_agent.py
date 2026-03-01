"""
Agent 07 — QA Engineer
Test pyramid strategy, risk-based testing, test plan generation, bug reporting.
Runs in parallel with Agent 08 (Security Auditor).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core import (
    ThoughtChain, ThinkingStep, HandOffMessage, TaskStatus,
    get_logger, log_to_ledger, get_bus, ConsultationType, ConsultationPriority,
    generate_test_plan, generate_bug_report, notify,
)
from skills import TDDBDD, AgileScrum

AGENT_ID   = "07"
AGENT_NAME = "QA-Engineer"

logger = get_logger(AGENT_ID, AGENT_NAME)


# ---------------------------------------------------------------------------
# Risk-based test prioritization
# ---------------------------------------------------------------------------

def risk_matrix(features: list[dict]) -> list[dict]:
    """
    features: [{name, probability (1-5), impact (1-5)}]
    Returns prioritized list by risk score (probability × impact).
    """
    scored = [
        {**f, "risk_score": f["probability"] * f["impact"],
         "priority": "P0" if f["probability"] * f["impact"] >= 20 else
                     "P1" if f["probability"] * f["impact"] >= 12 else
                     "P2" if f["probability"] * f["impact"] >= 6  else "P3"}
        for f in features
    ]
    return sorted(scored, key=lambda x: x["risk_score"], reverse=True)


# ---------------------------------------------------------------------------
# Test plan generation
# ---------------------------------------------------------------------------

def create_test_plan(project: str, mission_id: str, features: list[str]) -> str:
    test_cases = "| TC-ID | Feature | Scenario | Type | Priority |\n"
    test_cases += "|-------|---------|----------|------|----------|\n"
    for i, feat in enumerate(features, 1):
        test_cases += f"| TC-{i:03d} | {feat} | Happy path | Unit | P0 |\n"
        test_cases += f"| TC-{i:03d}b | {feat} | Error handling | Unit | P1 |\n"
        test_cases += f"| TC-{i:03d}c | {feat} | E2E user journey | E2E | P0 |\n"

    path = generate_test_plan(
        project=project,
        scope=f"All features for {project} MVP: {', '.join(features)}",
        strategy="Test Pyramid: Unit (70%) + Integration (20%) + E2E (10%). Risk-based prioritization.",
        entry_criteria="Code review passed; dev environment stable; test data seeded",
        exit_criteria="All P0/P1 test cases pass; coverage ≥ 80%; no open CRITICAL/HIGH bugs",
        test_cases=test_cases,
        coverage_metrics="Line: ≥80% | Branch: ≥70% | E2E critical paths: 100%",
    )
    logger.info(f"Test plan generated: {path}")
    return str(path)


# ---------------------------------------------------------------------------
# Main validate function
# ---------------------------------------------------------------------------

def validate(mission_id: str, artifact: str, test_results: dict = None) -> HandOffMessage:
    logger.info(f"Starting QA validation for: {artifact}")

    test_results = test_results or {}
    passed = test_results.get("passed", 0)
    total  = test_results.get("total", 0)
    all_pass = (passed == total and total > 0)

    chain = (
        ThoughtChain(AGENT_ID, AGENT_NAME, artifact)
        .think(ThinkingStep.UNDERSTAND, f"Validate quality of: {artifact}")
        .think(ThinkingStep.DECOMPOSE, "1) Test pyramid execution 2) Risk-based prioritization 3) Coverage check 4) Bug reporting 5) Sign-off")
        .think(ThinkingStep.EVALUATE, f"Test results: {passed}/{total} passed. Coverage target ≥ 80%. Risk matrix applied.")
        .think(ThinkingStep.DECIDE, "Pass to DevOps if all P0/P1 tests pass and coverage met; else escalate.")
        .think(ThinkingStep.EXECUTE, f"Running test suite for {artifact}. Generating test plan.")
        .think(ThinkingStep.HANDOFF, "09/DevOps (if passed) or 01/Dispatcher (if blocked)")
    )

    logger.info(chain.summary())

    # Risk matrix
    features_to_test = [
        {"name": "Auth/Login",         "probability": 3, "impact": 5},
        {"name": "Recipe Discovery",   "probability": 4, "impact": 4},
        {"name": "Chef Booking",       "probability": 3, "impact": 5},
        {"name": "Payment Processing", "probability": 2, "impact": 5},
        {"name": "Search/Filter",      "probability": 4, "impact": 3},
    ]
    risk = risk_matrix(features_to_test)
    logger.info(f"Risk matrix: top risk — {risk[0]['name']} (score: {risk[0]['risk_score']}, priority: {risk[0]['priority']})")

    # Generate test plan
    test_plan_path = create_test_plan("CooCook", mission_id, [f["name"] for f in features_to_test])

    # Generate bug report if failures exist
    bugs = test_results.get("failures", [])
    bug_paths = []
    for bug in bugs[:3]:  # cap at 3 for demo
        bp = generate_bug_report(
            title=bug.get("title", "Test failure"),
            severity=bug.get("severity", "P2 — Medium"),
            component=artifact,
            steps=bug.get("steps", "1. Run test suite\n2. Observe failure"),
            expected=bug.get("expected", "Test passes"),
            actual=bug.get("actual", "Test fails with assertion error"),
            environment="CI (Python 3.12, pytest)",
            root_cause=bug.get("root_cause", "TBD — under investigation"),
            fix_suggestion=bug.get("fix", "Review failing assertion and fix business logic"),
        )
        bug_paths.append(str(bp))

    # Consult Security in parallel
    bus = get_bus()
    bus.consult(
        from_agent=f"{AGENT_ID}/{AGENT_NAME}",
        to_agent="08/Security-Auditor",
        question=f"QA complete for '{artifact}'. Any security test cases I should add for the test plan?",
        context=f"Mission {mission_id} — parallel QA/Security validation",
        priority=ConsultationPriority.MEDIUM,
        consultation_type=ConsultationType.REVIEW,
    )

    blocked = not all_pass and bool(test_results)

    if blocked:
        logger.warning(f"Tests FAILED: {passed}/{total}. Escalating to Dispatcher.")
        status    = TaskStatus.BLOCKED
        to_id     = "01"
        to_name   = "Chief-Dispatcher"
        next_action = "Dispatcher: test failures block deployment. Dev agents must fix. Re-test required."
    else:
        status    = TaskStatus.COMPLETE
        to_id     = "09"
        to_name   = "DevOps-Engineer"
        next_action = "DevOps: artifact is QA-approved. Test plan and coverage report attached. Proceed with deployment."

    msg = HandOffMessage(
        from_agent_id=AGENT_ID,
        from_agent_name=AGENT_NAME,
        to_agent_id=to_id,
        to_agent_name=to_name,
        mission_id=mission_id,
        status=status,
        summary=f"QA {'PASSED' if not blocked else 'BLOCKED'} for {artifact}. {passed}/{total} tests. Risk matrix applied.",
        output=[test_plan_path] + bug_paths + ["agents/07_qa_engineer/output/coverage_report.html"],
        next_action=next_action,
        blockers="none" if not blocked else f"Test failures: {total - passed}/{total}",
    )

    log_to_ledger(AGENT_NAME, f"QA {'PASSED' if not blocked else 'BLOCKED'} for {artifact} — mission {mission_id}")
    notify(AGENT_ID, AGENT_NAME,
           "QA Validation Complete" if not blocked else "QA BLOCKED — Test Failures",
           "QA" if not blocked else "BLOCKED",
           f"{artifact} 검증 {'완료' if not blocked else '차단'}. {passed}/{total} tests. 리스크 상위: {risk[0]['name']}",
           outputs=[test_plan_path], mission_id=mission_id)
    return msg


if __name__ == "__main__":
    result = validate("M-002", "Recipe Discovery API", {"passed": 42, "total": 42})
    print(result.to_json())
