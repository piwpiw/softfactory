"""
skills/domain_driven_design.py
Domain-Driven Design — Bounded Contexts, Aggregates, Domain Events, Repository pattern.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class DomainDrivenDesign:
    name: str = "Domain-Driven Design"
    principles: List[str] = field(default_factory=lambda: [
        "Ubiquitous Language — shared vocabulary between domain experts and developers",
        "Bounded Context — explicit boundaries around domain models",
        "Context Mapping — understand relationships between bounded contexts",
        "Aggregate — cluster of domain objects treated as a unit (1 root)",
        "Domain Events — capture state-changing business facts explicitly",
        "Anti-Corruption Layer — translate between contexts without polluting models",
    ])
    methodology: List[str] = field(default_factory=lambda: [
        "1. EVENT STORMING — Workshop to discover domain events (orange stickies)",
        "2. SUBDOMAINS    — Identify Core, Supporting, Generic subdomains",
        "3. BOUNDED CONTEXT — Draw explicit model boundaries (1 BC = 1 ubiquitous language)",
        "4. CONTEXT MAP   — Define relationships (Partnership, Customer/Supplier, ACL, etc.)",
        "5. AGGREGATE DESIGN — Define Aggregate Roots; enforce invariants within boundary",
        "6. DOMAIN EVENTS — Name events in past tense ('OrderPlaced', 'ChefBooked')",
        "7. REPOSITORIES  — One repository per Aggregate Root",
    ])
    tools: List[str] = field(default_factory=lambda: [
        "Event Storming Board", "Context Map", "Aggregate Canvas",
        "Domain Event Log", "Ubiquitous Language Glossary",
        "C4 Container Diagram per Bounded Context",
        "CQRS (Command Query Responsibility Segregation)",
        "Event Sourcing",
    ])
    output_templates: List[str] = field(default_factory=lambda: [
        "Ubiquitous Language Glossary (term → definition × context)",
        "Bounded Context Canvas",
        "Context Map with relationships labeled",
        "Aggregate specification (root, entities, value objects, invariants)",
        "Domain Event catalog",
        "Repository interface definition",
    ])

    def apply(self, context: dict) -> dict:
        domain = context.get("domain", "Travel-Tech")
        subdomains = context.get("subdomains", ["User", "Recipe", "Booking", "Payment"])

        return {
            "skill": self.name,
            "domain": domain,
            "event_storming_steps": [
                "1. Unlimited modelling space (whiteboard/Miro)",
                "2. Domain Events (orange) — all business facts in past tense",
                "3. Commands (blue) — what triggered each event",
                "4. Aggregates (yellow) — which entity processed the command",
                "5. Bounded Context lines — natural language boundaries",
                "6. Policy (lilac) — automated reactions to events",
                "7. External Systems (pink) — third-party integrations",
            ],
            "bounded_contexts": [
                {
                    "name": sd,
                    "type": "Core" if i == 0 else ("Supporting" if i < len(subdomains) - 1 else "Generic"),
                    "key_aggregates": [f"{sd}Profile", f"{sd}Preference"],
                    "domain_events": [f"{sd}Created", f"{sd}Updated"],
                }
                for i, sd in enumerate(subdomains)
            ],
            "context_map_patterns": {
                "Shared Kernel": "Shared User Identity between contexts",
                "Customer/Supplier": "Recipe → Booking (Recipe is upstream)",
                "Anti-Corruption Layer": "Payment gateway isolation",
                "Open Host Service": "Public API for third-party integration",
            },
            "aggregate_design_rules": [
                "Only one Aggregate Root per Aggregate",
                "Protect invariants inside the Aggregate boundary",
                "Reference other Aggregates by ID only",
                "Keep Aggregates small (< 10 domain objects)",
                "One transaction per Aggregate",
            ],
        }

    def checklist(self) -> List[str]:
        return [
            "[ ] Event Storming completed with domain experts",
            "[ ] Ubiquitous Language glossary maintained",
            "[ ] Bounded Contexts explicitly drawn and named",
            "[ ] Context Map with relationship patterns documented",
            "[ ] Each Aggregate has exactly one root",
            "[ ] Domain Events named in past tense",
            "[ ] One Repository per Aggregate Root",
            "[ ] ACL implemented for external integrations",
        ]
