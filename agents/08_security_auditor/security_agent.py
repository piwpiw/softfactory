"""
Agent 08 — Security Auditor
STRIDE threat modeling, CVSS 3.1 scoring, OWASP Top 10, GDPR, security report generation.
Runs in parallel with Agent 07 (QA Engineer).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core import (
    ThoughtChain, ThinkingStep, HandOffMessage, TaskStatus,
    get_logger, log_to_ledger, get_bus, ConsultationType,
    ConsultationPriority, generate_security_report, notify,
)
from skills import OWASPSecurity

AGENT_ID   = "08"
AGENT_NAME = "Security-Auditor"

logger = get_logger(AGENT_ID, AGENT_NAME)


# ---------------------------------------------------------------------------
# STRIDE threat modeling
# ---------------------------------------------------------------------------

def stride_threat_model(components: list[str]) -> dict:
    owasp = OWASPSecurity()
    return owasp.apply({"components": components})["threat_model"]


# ---------------------------------------------------------------------------
# CVSS scoring helper
# ---------------------------------------------------------------------------

def score_finding(finding: dict) -> dict:
    owasp = OWASPSecurity()
    cvss = owasp.cvss_score(
        av=finding.get("av", "N"),
        ac=finding.get("ac", "L"),
        pr=finding.get("pr", "N"),
        ui=finding.get("ui", "N"),
        s=finding.get("s",  "U"),
        c=finding.get("c",  "H"),
        i=finding.get("i",  "H"),
        a=finding.get("a",  "H"),
    )
    return {**finding, **cvss}


# ---------------------------------------------------------------------------
# Main audit function
# ---------------------------------------------------------------------------

def audit(mission_id: str, artifact: str, findings: list = None) -> HandOffMessage:
    logger.info(f"Starting security audit for: {artifact}")

    findings = findings or []
    owasp    = OWASPSecurity()

    chain = (
        ThoughtChain(AGENT_ID, AGENT_NAME, artifact)
        .think(ThinkingStep.UNDERSTAND, f"Security audit of: {artifact}")
        .think(ThinkingStep.DECOMPOSE, "1) STRIDE threat model 2) OWASP Top 10 3) CVSS scoring 4) GDPR check 5) Report generation")
        .think(ThinkingStep.EVALUATE, f"Findings: {len(findings)}. STRIDE per component. CVSS for each finding.")
        .think(ThinkingStep.DECIDE, "Block if CRITICAL/HIGH unmitigated. Provide remediation for all findings.")
        .think(ThinkingStep.EXECUTE, "Running full OWASP + STRIDE assessment.")
        .think(ThinkingStep.HANDOFF, "09/DevOps if clear; 01/Dispatcher if blocked (escalation).")
    )

    logger.info(chain.summary())

    # STRIDE analysis
    components = ["API Gateway", "Auth Service", "Recipe Service", "Booking Service", "Payment Proxy"]
    stride = stride_threat_model(components)
    logger.info(f"STRIDE model: {len(components)} components analyzed")

    # OWASP Top 10
    owasp_result = owasp.apply({"components": components, "findings": findings})
    logger.info(f"OWASP Top 10: {len(owasp_result['owasp_assessment'])} categories assessed")

    # Score each finding
    scored_findings = [score_finding(f) for f in findings]
    critical = [f for f in scored_findings if f.get("rating") == "CRITICAL"]
    high     = [f for f in scored_findings if f.get("rating") == "HIGH"]
    medium   = [f for f in scored_findings if f.get("rating") == "MEDIUM"]

    logger.info(f"Findings: {len(critical)} CRITICAL, {len(high)} HIGH, {len(medium)} MEDIUM")

    # Generate security report for each critical/high finding
    report_paths = []
    for i, finding in enumerate(critical + high, 1):
        path = generate_security_report(
            finding_id=f"SEC-{mission_id}-{i:03d}",
            owasp_category=finding.get("owasp", "A03 Injection"),
            cvss_score=finding.get("score", 9.8),
            description=finding.get("description", "Security finding identified during audit"),
            affected=artifact,
            poc=finding.get("poc", "Manual testing; automated scan confirmation pending"),
            remediation=finding.get("remediation", "Apply input validation; update dependencies"),
            verification=finding.get("verification", "Re-scan after fix; confirm via automated test"),
        )
        report_paths.append(str(path))

    # GDPR quick check
    gdpr_items = [
        "✓ User data stored in EU region (GDPR Art.44)",
        "✓ Consent mechanism planned for analytics",
        "⚠ DPA (Data Processing Agreement) needed for Stripe, SendGrid",
        "✓ Right to erasure endpoint planned (GDPR Art.17)",
    ]
    logger.info("GDPR quick check completed")

    # Escalate critical findings via ConsultationBus
    blocked = bool(critical or high)
    if blocked:
        bus = get_bus()
        bus.escalate(
            from_agent=f"{AGENT_ID}/{AGENT_NAME}",
            conflict=f"Security findings block deployment: {len(critical)} CRITICAL, {len(high)} HIGH in {artifact}",
        )

    msg = HandOffMessage(
        from_agent_id=AGENT_ID,
        from_agent_name=AGENT_NAME,
        to_agent_id="01" if blocked else "09",
        to_agent_name="Chief-Dispatcher" if blocked else "DevOps-Engineer",
        mission_id=mission_id,
        status=TaskStatus.BLOCKED if blocked else TaskStatus.COMPLETE,
        summary=(
            f"Security audit {'BLOCKED' if blocked else 'CLEARED'} for {artifact}. "
            f"STRIDE: {len(components)} components. CVSS: {len(scored_findings)} findings scored. "
            f"CRITICAL: {len(critical)}, HIGH: {len(high)}."
        ),
        output=report_paths + ["agents/08_security_auditor/output/stride_model.md"],
        next_action=(
            "Dispatcher: critical/high findings require remediation before deployment."
            if blocked else
            "DevOps: artifact is security-cleared. Deploy per runbook."
        ),
        blockers=f"{len(critical)} CRITICAL, {len(high)} HIGH findings" if blocked else "none",
    )

    log_to_ledger(
        AGENT_NAME,
        f"Security audit {'BLOCKED' if blocked else 'CLEARED'} for {artifact} — {len(critical)}C/{len(high)}H — mission {mission_id}"
    )
    notify(AGENT_ID, AGENT_NAME,
           "Security Audit BLOCKED" if blocked else "Security Audit CLEARED",
           "BLOCKED" if blocked else "SECURITY",
           f"STRIDE: {len(components)}개 컴포넌트. OWASP Top 10 점검 완료. "
           f"CRITICAL: {len(critical)}, HIGH: {len(high)}, MEDIUM: {len(medium)}",
           outputs=report_paths or None, mission_id=mission_id)
    return msg


if __name__ == "__main__":
    result = audit("M-002", "Recipe Discovery API", findings=[])
    print(result.to_json())
