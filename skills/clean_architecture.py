"""
skills/clean_architecture.py
Clean Architecture — SOLID principles, Clean Code, 12-Factor App.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class CleanArchitecture:
    name: str = "Clean Architecture"
    principles: List[str] = field(default_factory=lambda: [
        "SRP — Single Responsibility Principle: one reason to change",
        "OCP — Open/Closed: open for extension, closed for modification",
        "LSP — Liskov Substitution: subtypes must be substitutable",
        "ISP — Interface Segregation: prefer specific interfaces over fat ones",
        "DIP — Dependency Inversion: depend on abstractions, not concretions",
        "Dependency Rule: dependencies ALWAYS point inward (Domain ← Use Cases ← Adapters ← Frameworks)",
        "12-Factor: treat code as stateless, config in environment, backing services as attached resources",
    ])
    methodology: List[str] = field(default_factory=lambda: [
        "LAYERS (outer → inner):",
        "  4. Frameworks & Drivers (DB, Web, UI, External APIs)",
        "  3. Interface Adapters (Controllers, Presenters, Gateways)",
        "  2. Application Use Cases (Business rules specific to app)",
        "  1. Domain Entities (Enterprise-wide business rules)",
        "RULES:",
        "  - Source code dependencies must only point inward",
        "  - Inner circles know nothing about outer circles",
        "  - Use Dependency Inversion to cross boundaries",
    ])
    tools: List[str] = field(default_factory=lambda: [
        "Clean Code linting (pylint/flake8/eslint)",
        "Dependency injection containers",
        "Interface/Abstract Base Classes",
        "Repository pattern", "Use Case classes",
        "DTO (Data Transfer Objects)",
        "CQRS (Command/Query separation)",
    ])
    output_templates: List[str] = field(default_factory=lambda: [
        "Layer dependency diagram",
        "Use Case specification (actor, preconditions, steps, postconditions)",
        "Interface/Port definitions",
        "12-Factor compliance checklist",
        "SOLID violation report",
    ])

    TWELVE_FACTORS = [
        "I.   Codebase — One codebase, many deploys",
        "II.  Dependencies — Explicitly declare and isolate",
        "III. Config — Store config in the environment (never in code)",
        "IV.  Backing Services — Treat as attached resources",
        "V.   Build/Release/Run — Strictly separate stages",
        "VI.  Processes — Execute as stateless processes",
        "VII. Port Binding — Export services via port binding",
        "VIII.Concurrency — Scale out via process model",
        "IX.  Disposability — Fast startup, graceful shutdown",
        "X.   Dev/Prod Parity — Keep dev, staging, prod as similar as possible",
        "XI.  Logs — Treat as event streams",
        "XII. Admin Processes — Run admin/management tasks as one-off processes",
    ]

    def apply(self, context: dict) -> dict:
        domain = context.get("domain_entities", ["User", "Recipe", "Booking"])
        use_cases = context.get("use_cases", ["CreateUser", "BookChef", "DiscoverRecipe"])

        return {
            "skill": self.name,
            "layer_structure": {
                "entities": {
                    "description": "Core business objects and rules",
                    "examples": domain,
                    "rule": "No dependencies on anything outside this layer",
                },
                "use_cases": {
                    "description": "Application-specific business rules",
                    "examples": use_cases,
                    "rule": "May use entities; no knowledge of UI/DB/frameworks",
                },
                "interface_adapters": {
                    "description": "Convert data between use cases and external formats",
                    "components": ["REST Controllers", "Repository implementations", "Serializers"],
                    "rule": "Implements ports defined by use cases",
                },
                "frameworks_drivers": {
                    "description": "External tools and frameworks (glue code only)",
                    "components": ["FastAPI/Django", "SQLAlchemy", "Redis client"],
                    "rule": "Should be swappable without changing business logic",
                },
            },
            "solid_compliance": {
                "SRP": "Each class has one reason to change",
                "OCP": "Use abstract interfaces to add features without modification",
                "LSP": "Validate substitutability in test suite",
                "ISP": f"Define {len(use_cases)} focused use case interfaces",
                "DIP": "Inject dependencies via constructors, not global singletons",
            },
            "twelve_factor": self.TWELVE_FACTORS,
        }

    def checklist(self) -> List[str]:
        return [
            "[ ] Domain layer has zero external dependencies",
            "[ ] Use Cases depend only on Domain + Port interfaces",
            "[ ] No framework imports in Domain or Use Case layers",
            "[ ] All I/O accessed through Repository/Service interfaces",
            "[ ] Config read from environment variables (not hardcoded)",
            "[ ] App can start/stop within 5 seconds (Disposability)",
            "[ ] No state stored in process memory between requests",
            "[ ] Each class has a single stated responsibility",
            "[ ] Interfaces are used at every layer boundary",
        ]
