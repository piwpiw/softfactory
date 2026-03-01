"""
skills/tdd_bdd.py
TDD/BDD — Red-Green-Refactor cycle, Gherkin/Cucumber, Given-When-Then.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class TDDBDD:
    name: str = "TDD/BDD"
    principles: List[str] = field(default_factory=lambda: [
        "Test First — write the test before the code",
        "Single assertion per test — test one behavior at a time",
        "FIRST: Fast, Independent, Repeatable, Self-validating, Timely",
        "Executable specifications — tests are living documentation",
        "Outside-in BDD — start from user behavior, work inward",
        "Three Amigos — BA + Dev + QA define scenarios together",
    ])
    methodology: List[str] = field(default_factory=lambda: [
        "TDD CYCLE:",
        "  1. RED    — Write a failing test for new behavior",
        "  2. GREEN  — Write minimum code to make the test pass",
        "  3. REFACTOR — Improve code without breaking tests",
        "BDD CYCLE:",
        "  1. DISCOVER — Three Amigos session, write Gherkin scenarios",
        "  2. FORMULATE — Refine scenarios into Given-When-Then",
        "  3. AUTOMATE  — Implement step definitions",
        "  4. VALIDATE  — Scenarios pass = feature delivered",
    ])
    tools: List[str] = field(default_factory=lambda: [
        "pytest / JUnit / Jest", "Cucumber / Behave / SpecFlow",
        "Gherkin (.feature files)", "Mockito / unittest.mock",
        "Factory Boy / Test Fixtures", "Coverage.py / Istanbul",
        "Mutation Testing (mutmut / PIT)", "Contract Testing (Pact)",
    ])
    output_templates: List[str] = field(default_factory=lambda: [
        "Feature file (Given-When-Then scenarios)",
        "Unit test suite (Red-Green-Refactor evidence)",
        "Test coverage report (≥80% lines, ≥70% branches)",
        "Mutation score report",
        "Integration test suite",
    ])

    def apply(self, context: dict) -> dict:
        feature = context.get("feature", "User Authentication")
        scenarios = context.get("scenarios", [])

        default_scenarios = [
            {
                "name": f"Successful {feature}",
                "given": "a registered user exists",
                "when": f"the user performs {feature}",
                "then": "the system grants access and returns a session token",
            },
            {
                "name": f"Failed {feature} with invalid credentials",
                "given": "an unregistered user attempts access",
                "when": f"the user performs {feature} with wrong credentials",
                "then": "the system returns 401 Unauthorized",
            },
        ]

        return {
            "skill": self.name,
            "feature": feature,
            "tdd_cycle": {
                "red": f"Write test: test_{feature.lower().replace(' ', '_')}_succeeds()",
                "green": "Implement minimum viable logic to pass",
                "refactor": "Extract, rename, simplify — no new behavior",
            },
            "bdd_gherkin": {
                "feature_file": f"Feature: {feature}",
                "scenarios": scenarios if scenarios else default_scenarios,
            },
            "coverage_targets": {
                "line_coverage": "≥ 80%",
                "branch_coverage": "≥ 70%",
                "mutation_score": "≥ 60%",
            },
            "test_pyramid": {
                "unit": "70% — fast, isolated, mock dependencies",
                "integration": "20% — test component interactions",
                "e2e": "10% — critical user journeys only",
            },
        }

    def gherkin_template(self, feature: str, persona: str, action: str, outcome: str) -> str:
        return (
            f"Feature: {feature}\n"
            f"  As a {persona}\n"
            f"  I want to {action}\n"
            f"  So that {outcome}\n\n"
            f"  Scenario: Successful {feature}\n"
            f"    Given {persona} is authenticated\n"
            f"    When the {persona} {action}s\n"
            f"    Then the system confirms {outcome}\n\n"
            f"  Scenario: {feature} fails on invalid input\n"
            f"    Given {persona} provides invalid data\n"
            f"    When the {persona} attempts to {action}\n"
            f"    Then the system returns a validation error\n"
        )

    def checklist(self) -> List[str]:
        return [
            "[ ] Each test has a single, clear assertion",
            "[ ] Tests are independent (no shared mutable state)",
            "[ ] Red phase confirmed (test fails before implementation)",
            "[ ] Green phase minimal (no extra logic)",
            "[ ] Refactor phase completed without breaking tests",
            "[ ] Gherkin feature files reviewed by Three Amigos",
            "[ ] Step definitions map 1:1 to Gherkin steps",
            "[ ] Coverage ≥ 80% lines measured and reported",
            "[ ] All tests run in CI on every commit",
        ]
