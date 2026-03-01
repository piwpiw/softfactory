"""
core/document_engine.py
Document generation engine — creates standard-compliant markdown files
from templates defined in docs/standards/.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

STANDARDS_DIR = Path(__file__).parent.parent / "docs" / "standards"
OUTPUT_DIR    = Path(__file__).parent.parent / "docs" / "generated"


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w\-]", "_", name).strip("_")


def _render(template_path: Path, replacements: dict) -> str:
    content = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        content = content.replace(f"{{{{{key}}}}}", str(value))
    return content


def _write(content: str, filename: str, subdir: str = "") -> Path:
    output_dir = OUTPUT_DIR / subdir if subdir else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(content, encoding="utf-8")
    print(f"[DocumentEngine] Generated: {path}")
    return path


# ---------------------------------------------------------------------------
# PRD
# ---------------------------------------------------------------------------

def generate_prd(
    project: str,
    problem: str,
    goals: str,
    personas: str,
    stories: str,
    requirements: str,
    moscow: str,
    out_name: Optional[str] = None,
) -> Path:
    template = STANDARDS_DIR / "PRD_TEMPLATE.md"
    content = _render(template, {
        "PROJECT": project,
        "DATE": _now(),
        "PROBLEM": problem,
        "GOALS": goals,
        "PERSONAS": personas,
        "STORIES": stories,
        "REQUIREMENTS": requirements,
        "MOSCOW": moscow,
    })
    fname = out_name or f"PRD_{_safe_filename(project)}_{_now()}.md"
    return _write(content, fname, "prd")


# ---------------------------------------------------------------------------
# ADR
# ---------------------------------------------------------------------------

def generate_adr(
    title: str,
    status: str,
    context: str,
    decision: str,
    consequences: str,
    alternatives: str,
    adr_number: int = 1,
    out_name: Optional[str] = None,
) -> Path:
    template = STANDARDS_DIR / "ADR_TEMPLATE.md"
    content = _render(template, {
        "ADR_NUMBER": str(adr_number).zfill(4),
        "TITLE": title,
        "DATE": _now(),
        "STATUS": status,
        "CONTEXT": context,
        "DECISION": decision,
        "CONSEQUENCES": consequences,
        "ALTERNATIVES": alternatives,
    })
    fname = out_name or f"ADR-{str(adr_number).zfill(4)}_{_safe_filename(title)}.md"
    return _write(content, fname, "adr")


# ---------------------------------------------------------------------------
# RFC
# ---------------------------------------------------------------------------

def generate_rfc(
    title: str,
    summary: str,
    motivation: str,
    design: str,
    drawbacks: str,
    alternatives: str,
    unresolved: str,
    rfc_number: int = 1,
    out_name: Optional[str] = None,
) -> Path:
    template = STANDARDS_DIR / "RFC_TEMPLATE.md"
    content = _render(template, {
        "RFC_NUMBER": str(rfc_number).zfill(4),
        "TITLE": title,
        "DATE": _now(),
        "SUMMARY": summary,
        "MOTIVATION": motivation,
        "DESIGN": design,
        "DRAWBACKS": drawbacks,
        "ALTERNATIVES": alternatives,
        "UNRESOLVED": unresolved,
    })
    fname = out_name or f"RFC-{str(rfc_number).zfill(4)}_{_safe_filename(title)}.md"
    return _write(content, fname, "rfc")


# ---------------------------------------------------------------------------
# Bug Report
# ---------------------------------------------------------------------------

def generate_bug_report(
    title: str,
    severity: str,
    component: str,
    steps: str,
    expected: str,
    actual: str,
    environment: str,
    root_cause: str,
    fix_suggestion: str,
    out_name: Optional[str] = None,
) -> Path:
    template = STANDARDS_DIR / "BUG_REPORT_TEMPLATE.md"
    content = _render(template, {
        "TITLE": title,
        "DATE": _now(),
        "SEVERITY": severity,
        "COMPONENT": component,
        "STEPS": steps,
        "EXPECTED": expected,
        "ACTUAL": actual,
        "ENVIRONMENT": environment,
        "ROOT_CAUSE": root_cause,
        "FIX_SUGGESTION": fix_suggestion,
    })
    fname = out_name or f"BUG_{_safe_filename(title)}_{_now()}.md"
    return _write(content, fname, "bugs")


# ---------------------------------------------------------------------------
# Security Report
# ---------------------------------------------------------------------------

def generate_security_report(
    finding_id: str,
    owasp_category: str,
    cvss_score: float,
    description: str,
    affected: str,
    poc: str,
    remediation: str,
    verification: str,
    out_name: Optional[str] = None,
) -> Path:
    template = STANDARDS_DIR / "SECURITY_REPORT_TEMPLATE.md"
    content = _render(template, {
        "FINDING_ID": finding_id,
        "DATE": _now(),
        "OWASP_CATEGORY": owasp_category,
        "CVSS_SCORE": str(cvss_score),
        "DESCRIPTION": description,
        "AFFECTED": affected,
        "POC": poc,
        "REMEDIATION": remediation,
        "VERIFICATION": verification,
    })
    fname = out_name or f"SEC_{finding_id}_{_now()}.md"
    return _write(content, fname, "security")


# ---------------------------------------------------------------------------
# Test Plan
# ---------------------------------------------------------------------------

def generate_test_plan(
    project: str,
    scope: str,
    strategy: str,
    entry_criteria: str,
    exit_criteria: str,
    test_cases: str,
    coverage_metrics: str,
    out_name: Optional[str] = None,
) -> Path:
    template = STANDARDS_DIR / "TEST_PLAN_TEMPLATE.md"
    content = _render(template, {
        "PROJECT": project,
        "DATE": _now(),
        "SCOPE": scope,
        "STRATEGY": strategy,
        "ENTRY_CRITERIA": entry_criteria,
        "EXIT_CRITERIA": exit_criteria,
        "TEST_CASES": test_cases,
        "COVERAGE_METRICS": coverage_metrics,
    })
    fname = out_name or f"TEST_PLAN_{_safe_filename(project)}_{_now()}.md"
    return _write(content, fname, "test_plans")


# ---------------------------------------------------------------------------
# Deployment Runbook
# ---------------------------------------------------------------------------

def generate_deployment_runbook(
    service: str,
    version: str,
    pre_deploy: str,
    deploy_steps: str,
    health_checks: str,
    rollback: str,
    post_deploy: str,
    incident_response: str,
    out_name: Optional[str] = None,
) -> Path:
    template = STANDARDS_DIR / "DEPLOYMENT_RUNBOOK_TEMPLATE.md"
    content = _render(template, {
        "SERVICE": service,
        "VERSION": version,
        "DATE": _now(),
        "PRE_DEPLOY": pre_deploy,
        "DEPLOY_STEPS": deploy_steps,
        "HEALTH_CHECKS": health_checks,
        "ROLLBACK": rollback,
        "POST_DEPLOY": post_deploy,
        "INCIDENT_RESPONSE": incident_response,
    })
    fname = out_name or f"RUNBOOK_{_safe_filename(service)}_v{version}_{_now()}.md"
    return _write(content, fname, "runbooks")
