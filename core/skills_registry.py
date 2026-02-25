"""
core/skills_registry.py
Skill catalog and agent skill-set registry.
Each agent declares its skills; tasks can be matched to capable agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


class SkillLevel(str, Enum):
    AWARENESS  = "AWARENESS"   # Knows the concept
    WORKING    = "WORKING"     # Can apply with guidance
    PRACTITIONER = "PRACTITIONER"  # Applies independently
    EXPERT     = "EXPERT"      # Teaches and innovates


class SkillCategory(str, Enum):
    PRODUCT    = "PRODUCT"
    RESEARCH   = "RESEARCH"
    DESIGN     = "DESIGN"
    BACKEND    = "BACKEND"
    FRONTEND   = "FRONTEND"
    QUALITY    = "QUALITY"
    SECURITY   = "SECURITY"
    DEVOPS     = "DEVOPS"
    UX         = "UX"
    PROCESS    = "PROCESS"


@dataclass
class Skill:
    name: str
    category: SkillCategory
    level: SkillLevel
    description: str
    methodology: List[str] = field(default_factory=list)
    output_templates: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category.value,
            "level": self.level.value,
            "description": self.description,
            "methodology": self.methodology,
            "output_templates": self.output_templates,
        }


@dataclass
class AgentSkillSet:
    agent_id: str
    agent_name: str
    skills: List[Skill] = field(default_factory=list)

    def get_skill(self, name: str) -> Optional[Skill]:
        for s in self.skills:
            if s.name.lower() == name.lower():
                return s
        return None

    def can_handle(self, task_type: str) -> bool:
        task_lower = task_type.lower()
        return any(
            task_lower in s.name.lower() or task_lower in s.description.lower()
            for s in self.skills
        )

    def expert_skills(self) -> List[Skill]:
        return [s for s in self.skills if s.level == SkillLevel.EXPERT]

    def skills_by_category(self, category: SkillCategory) -> List[Skill]:
        return [s for s in self.skills if s.category == category]

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "skills": [s.to_dict() for s in self.skills],
        }


# ---------------------------------------------------------------------------
# Global skill registry
# ---------------------------------------------------------------------------

_REGISTRY: Dict[str, AgentSkillSet] = {}


def register(skill_set: AgentSkillSet) -> None:
    _REGISTRY[skill_set.agent_id] = skill_set


def get_agent_skills(agent_id: str) -> Optional[AgentSkillSet]:
    return _REGISTRY.get(agent_id)


def find_agents_for_task(task_type: str) -> List[AgentSkillSet]:
    return [ss for ss in _REGISTRY.values() if ss.can_handle(task_type)]


def all_skill_sets() -> List[AgentSkillSet]:
    return list(_REGISTRY.values())


# ---------------------------------------------------------------------------
# Pre-populated registry (loaded on import)
# ---------------------------------------------------------------------------

def _build_registry():
    from core.skills_registry import (
        Skill, AgentSkillSet, SkillCategory, SkillLevel, register
    )

    register(AgentSkillSet("01", "Chief-Dispatcher", [
        Skill("WSJF Prioritization", SkillCategory.PROCESS, SkillLevel.EXPERT,
              "Weighted Shortest Job First scoring for task sequencing",
              ["Cost of Delay", "Job Size estimation", "WSJF = CoD / Job Size"],
              ["WSJF Score Table"]),
        Skill("Conflict Resolution", SkillCategory.PROCESS, SkillLevel.EXPERT,
              "Structured conflict detection and roadmap re-evaluation",
              ["STOP → BLOCK → ESCALATE → RE-EVALUATE → RE-ISSUE"],
              ["Conflict Resolution Report"]),
        Skill("Pipeline Orchestration", SkillCategory.PROCESS, SkillLevel.EXPERT,
              "Multi-agent pipeline sequencing and dependency management",
              ["DAG construction", "Parallel gate management"],
              ["Execution Plan", "Dependency Graph"]),
    ]))

    register(AgentSkillSet("02", "Product-Manager", [
        Skill("RICE Scoring", SkillCategory.PRODUCT, SkillLevel.EXPERT,
              "Feature prioritization: Reach × Impact × Confidence / Effort",
              ["Define Reach", "Estimate Impact", "Set Confidence", "Estimate Effort"],
              ["RICE Score Table", "Prioritized Feature Backlog"]),
        Skill("Story Mapping", SkillCategory.PRODUCT, SkillLevel.EXPERT,
              "User Story Map to align product vision with delivery",
              ["Backbone activities", "User tasks", "Release slices"],
              ["Story Map Diagram", "Release Plan"]),
        Skill("OKR Definition", SkillCategory.PRODUCT, SkillLevel.PRACTITIONER,
              "Objectives & Key Results for mission goal alignment",
              ["Objective formulation", "KR measurability check", "Alignment cascade"],
              ["OKR Board", "Quarterly Review Template"]),
        Skill("PRD Writing", SkillCategory.PRODUCT, SkillLevel.EXPERT,
              "Product Requirements Document per docs/standards/PRD_TEMPLATE.md",
              ["Problem statement", "User personas", "Acceptance criteria", "MoSCoW"],
              ["PRD Document"]),
        Skill("MoSCoW Prioritization", SkillCategory.PRODUCT, SkillLevel.EXPERT,
              "Must/Should/Could/Won't framework for scope management",
              ["Stakeholder input", "Constraint analysis"],
              ["MoSCoW Table"]),
    ]))

    register(AgentSkillSet("03", "Market-Analyst", [
        Skill("SWOT Analysis", SkillCategory.RESEARCH, SkillLevel.EXPERT,
              "Strengths / Weaknesses / Opportunities / Threats framework",
              ["Internal audit", "External scan", "Cross-impact matrix"],
              ["SWOT Matrix", "Strategic Implications"]),
        Skill("PESTLE Analysis", SkillCategory.RESEARCH, SkillLevel.EXPERT,
              "Political/Economic/Social/Tech/Legal/Environmental scan",
              ["Factor identification", "Impact scoring", "Trend extrapolation"],
              ["PESTLE Report"]),
        Skill("Porter's Five Forces", SkillCategory.RESEARCH, SkillLevel.EXPERT,
              "Industry competitive intensity analysis",
              ["Supplier power", "Buyer power", "Competitive rivalry", "Substitutes", "New entrants"],
              ["Five Forces Diagram", "Competitive Positioning"]),
        Skill("TAM/SAM/SOM Sizing", SkillCategory.RESEARCH, SkillLevel.PRACTITIONER,
              "Total/Serviceable/Obtainable market sizing",
              ["Top-down estimation", "Bottom-up validation"],
              ["Market Size Report"]),
    ]))

    register(AgentSkillSet("04", "Solution-Architect", [
        Skill("ADR Writing", SkillCategory.DESIGN, SkillLevel.EXPERT,
              "Architecture Decision Records per docs/standards/ADR_TEMPLATE.md",
              ["Context → Decision → Consequences → Alternatives"],
              ["ADR Document"]),
        Skill("C4 Model", SkillCategory.DESIGN, SkillLevel.EXPERT,
              "Context/Container/Component/Code diagrams",
              ["System Context", "Container View", "Component View"],
              ["C4 Text Diagrams"]),
        Skill("Domain-Driven Design", SkillCategory.DESIGN, SkillLevel.EXPERT,
              "Bounded Contexts, Aggregates, Domain Events",
              ["Event Storming", "Context Mapping", "Aggregate design"],
              ["Domain Model", "Context Map"]),
        Skill("OpenAPI Design", SkillCategory.DESIGN, SkillLevel.EXPERT,
              "API-first design with OpenAPI 3.1 spec",
              ["Resource modeling", "Schema definition", "Contract-first"],
              ["openapi.yaml stub"]),
        Skill("Clean Architecture", SkillCategory.DESIGN, SkillLevel.EXPERT,
              "SOLID + Clean Architecture layer separation",
              ["Dependency rule", "Use cases", "Interface adapters"],
              ["Architecture Diagram", "Layer Specification"]),
    ]))

    register(AgentSkillSet("05", "Backend-Developer", [
        Skill("TDD Cycle", SkillCategory.BACKEND, SkillLevel.EXPERT,
              "Red-Green-Refactor development cycle",
              ["Write failing test", "Write minimal code", "Refactor"],
              ["Test suite", "Coverage report"]),
        Skill("Clean Architecture Implementation", SkillCategory.BACKEND, SkillLevel.EXPERT,
              "Entities / Use Cases / Interface Adapters / Frameworks",
              ["Layer separation", "Dependency inversion", "Port & Adapter"],
              ["Codebase structure", "Module map"]),
        Skill("12-Factor App", SkillCategory.BACKEND, SkillLevel.PRACTITIONER,
              "Cloud-native app methodology",
              ["Codebase", "Config", "Backing services", "Build/release/run"],
              ["12-Factor Compliance Checklist"]),
        Skill("API Implementation", SkillCategory.BACKEND, SkillLevel.EXPERT,
              "REST/GraphQL endpoint implementation from OpenAPI spec",
              ["Contract-first coding", "Validation", "Error handling"],
              ["API endpoints", "Integration tests"]),
    ]))

    register(AgentSkillSet("06", "Frontend-Developer", [
        Skill("Atomic Design", SkillCategory.FRONTEND, SkillLevel.EXPERT,
              "Atoms → Molecules → Organisms → Templates → Pages",
              ["Component hierarchy", "Design system integration"],
              ["Component library", "Storybook"]),
        Skill("WCAG 2.1 Compliance", SkillCategory.FRONTEND, SkillLevel.PRACTITIONER,
              "Web Content Accessibility Guidelines Level AA",
              ["Perceivable", "Operable", "Understandable", "Robust"],
              ["Accessibility Audit Report"]),
        Skill("BDD Frontend", SkillCategory.FRONTEND, SkillLevel.PRACTITIONER,
              "Behavior-Driven Development for UI with Gherkin",
              ["Feature files", "Step definitions", "E2E scenarios"],
              ["Gherkin feature files", "Cypress/Playwright tests"]),
        Skill("Performance Optimization", SkillCategory.FRONTEND, SkillLevel.WORKING,
              "Core Web Vitals optimization (LCP, FID, CLS)",
              ["Bundle analysis", "Code splitting", "Lazy loading"],
              ["Performance Report"]),
    ]))

    register(AgentSkillSet("07", "QA-Engineer", [
        Skill("Test Pyramid", SkillCategory.QUALITY, SkillLevel.EXPERT,
              "Unit → Integration → E2E test strategy",
              ["Unit (70%)", "Integration (20%)", "E2E (10%)"],
              ["Test Plan", "Coverage Metrics"]),
        Skill("Risk-Based Testing", SkillCategory.QUALITY, SkillLevel.EXPERT,
              "Prioritize tests by risk probability × impact",
              ["Risk identification", "Risk scoring", "Test prioritization"],
              ["Risk Matrix", "Prioritized Test Cases"]),
        Skill("Test Plan Writing", SkillCategory.QUALITY, SkillLevel.EXPERT,
              "Test planning per docs/standards/TEST_PLAN_TEMPLATE.md",
              ["Scope", "Strategy", "Entry/Exit criteria", "Test cases"],
              ["Test Plan Document"]),
        Skill("Bug Reporting", SkillCategory.QUALITY, SkillLevel.EXPERT,
              "Structured bug reports per BUG_REPORT_TEMPLATE.md",
              ["Severity classification (P0-P4)", "Reproduction steps"],
              ["Bug Report"]),
    ]))

    register(AgentSkillSet("08", "Security-Auditor", [
        Skill("OWASP Top 10", SkillCategory.SECURITY, SkillLevel.EXPERT,
              "Web application security risk assessment",
              ["A01-A10 checklist", "Manual + automated scanning"],
              ["Security Report"]),
        Skill("STRIDE Threat Modeling", SkillCategory.SECURITY, SkillLevel.EXPERT,
              "Spoofing/Tampering/Repudiation/Info Disclosure/DoS/EoP",
              ["Data Flow Diagrams", "Threat enumeration", "Mitigations"],
              ["STRIDE Threat Model"]),
        Skill("CVSS 3.1 Scoring", SkillCategory.SECURITY, SkillLevel.EXPERT,
              "Common Vulnerability Scoring System quantification",
              ["Base score", "Temporal score", "Environmental score"],
              ["CVSS Score Sheet"]),
        Skill("GDPR Compliance", SkillCategory.SECURITY, SkillLevel.PRACTITIONER,
              "Data protection and privacy regulation compliance",
              ["Data mapping", "Consent review", "DPA assessment"],
              ["GDPR Compliance Checklist"]),
    ]))

    register(AgentSkillSet("09", "DevOps-Engineer", [
        Skill("SLO/SLI Definition", SkillCategory.DEVOPS, SkillLevel.EXPERT,
              "Service Level Objectives and Indicators with error budgets",
              ["SLI selection", "SLO target setting", "Error budget burn"],
              ["SLO Dashboard", "Error Budget Report"]),
        Skill("GitOps", SkillCategory.DEVOPS, SkillLevel.EXPERT,
              "Git as single source of truth for infrastructure state",
              ["ArgoCD/Flux setup", "Declarative infra", "PR-based deploy"],
              ["GitOps Workflow", "CD Pipeline"]),
        Skill("Blue-Green Deployment", SkillCategory.DEVOPS, SkillLevel.EXPERT,
              "Zero-downtime deployment with instant rollback capability",
              ["Environment parity", "Traffic switching", "Smoke tests"],
              ["Deployment Runbook"]),
        Skill("IaC (Terraform/Ansible)", SkillCategory.DEVOPS, SkillLevel.PRACTITIONER,
              "Infrastructure as Code for reproducible environments",
              ["Resource declaration", "State management", "Module reuse"],
              ["Terraform modules", "Ansible playbooks"]),
        Skill("Chaos Engineering", SkillCategory.DEVOPS, SkillLevel.AWARENESS,
              "Proactive resilience testing via controlled failures",
              ["Hypothesis", "Blast radius", "Experiment", "Observation"],
              ["Chaos Experiment Report"]),
    ]))

    register(AgentSkillSet("10", "Telegram-Reporter", [
        Skill("Event-Driven Notification", SkillCategory.PROCESS, SkillLevel.EXPERT,
              "Priority-based Telegram alert delivery on mission events",
              ["Event filtering", "Priority routing", "Rate limiting"],
              ["Notification log"]),
        Skill("Report Summarization", SkillCategory.PROCESS, SkillLevel.PRACTITIONER,
              "Daily/weekly digest generation from mission logs",
              ["Log aggregation", "Key metrics extraction", "Narrative summary"],
              ["Daily Report", "Weekly Summary"]),
    ]))


_build_registry()
