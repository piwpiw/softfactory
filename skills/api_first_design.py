"""
skills/api_first_design.py
API-First Design — OpenAPI 3.1, REST Richardson Maturity Model, contract-first.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class APIFirstDesign:
    name: str = "API-First Design"
    principles: List[str] = field(default_factory=lambda: [
        "Contract First — define the API spec before writing code",
        "Consumer Driven — APIs designed from consumer's perspective",
        "Stable Contracts — versioning strategy prevents breaking changes",
        "OpenAPI 3.1 — machine-readable spec enables tooling generation",
        "REST Level 3 — HATEOAS for maximum discoverability",
        "Idempotency — safe retry semantics for all mutating operations",
    ])
    methodology: List[str] = field(default_factory=lambda: [
        "1. DOMAIN MODELING — Map resources from domain entities",
        "2. SPEC WRITING    — Draft openapi.yaml with resources/operations/schemas",
        "3. MOCK SERVER     — Generate mock server from spec (Prism/Stoplight)",
        "4. CONSUMER REVIEW — Frontend/mobile validate the contract",
        "5. IMPLEMENT       — Backend implements against the spec",
        "6. CONTRACT TEST   — Automated tests validate spec compliance",
        "7. PUBLISH         — Publish to developer portal (Swagger UI/Redoc)",
    ])
    tools: List[str] = field(default_factory=lambda: [
        "OpenAPI 3.1 (YAML/JSON)", "Swagger UI / Redoc",
        "Stoplight Studio / Insomnia", "Prism Mock Server",
        "Pact (consumer-driven contract testing)",
        "OpenAPI Generator (SDK generation)",
        "Spectral (OpenAPI linting)", "Dredd (spec compliance testing)",
    ])
    output_templates: List[str] = field(default_factory=lambda: [
        "openapi.yaml (OpenAPI 3.1 spec)",
        "API Changelog (breaking vs non-breaking changes)",
        "SDK generation config",
        "Consumer Contract tests",
        "API Design Guidelines document",
    ])

    RICHARDSON_LEVELS = {
        0: "Plain Old XML/JSON — single endpoint, no HTTP semantics",
        1: "Resources — separate URIs per resource type",
        2: "HTTP Verbs — GET/POST/PUT/DELETE with proper status codes",
        3: "HATEOAS — responses include hypermedia links (Level 3 = REST maturity)",
    }

    def apply(self, context: dict) -> dict:
        resources = context.get("resources", ["users", "recipes", "bookings", "chefs"])
        version = context.get("api_version", "v1")
        base_url = context.get("base_url", f"/api/{version}")

        endpoints = []
        for resource in resources:
            endpoints.extend([
                {"method": "GET",    "path": f"{base_url}/{resource}",
                 "summary": f"List {resource}", "operationId": f"list{resource.title()}"},
                {"method": "POST",   "path": f"{base_url}/{resource}",
                 "summary": f"Create {resource[:-1]}", "operationId": f"create{resource[:-1].title()}"},
                {"method": "GET",    "path": f"{base_url}/{resource}/{{id}}",
                 "summary": f"Get {resource[:-1]}", "operationId": f"get{resource[:-1].title()}"},
                {"method": "PUT",    "path": f"{base_url}/{resource}/{{id}}",
                 "summary": f"Update {resource[:-1]}", "operationId": f"update{resource[:-1].title()}"},
                {"method": "DELETE", "path": f"{base_url}/{resource}/{{id}}",
                 "summary": f"Delete {resource[:-1]}", "operationId": f"delete{resource[:-1].title()}"},
            ])

        return {
            "skill": self.name,
            "spec": {
                "openapi": "3.1.0",
                "info": {"title": "API", "version": version},
                "base_url": base_url,
                "resources": resources,
                "endpoint_count": len(endpoints),
                "sample_endpoints": endpoints[:6],
            },
            "richardson_level": {
                "target": 3,
                "description": self.RICHARDSON_LEVELS[3],
                "levels": self.RICHARDSON_LEVELS,
            },
            "versioning_strategy": {
                "method": "URL path versioning",
                "breaking_change_policy": "New major version with 6-month deprecation notice",
                "non_breaking": ["Adding optional fields", "Adding new endpoints"],
                "breaking": ["Removing fields", "Changing field types", "Removing endpoints"],
            },
            "security": {
                "authentication": "OAuth 2.0 / JWT Bearer",
                "authorization": "Scope-based (read:recipes, write:bookings)",
                "rate_limiting": "100 req/min per client; 429 Too Many Requests",
            },
        }

    def openapi_stub(self, title: str, version: str, resources: List[str]) -> str:
        paths = ""
        for r in resources:
            paths += f"""
  /{r}:
    get:
      operationId: list{r.title()}
      summary: List {r}
      responses:
        '200':
          description: Success
    post:
      operationId: create{r[:-1].title()}
      summary: Create {r[:-1]}
      responses:
        '201':
          description: Created
  /{r}/{{id}}:
    get:
      operationId: get{r[:-1].title()}
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
        '404':
          description: Not Found"""
        return f"""openapi: 3.1.0
info:
  title: {title}
  version: {version}
paths:{paths}
"""

    def checklist(self) -> List[str]:
        return [
            "[ ] openapi.yaml written BEFORE any backend code",
            "[ ] API contract reviewed by consumer teams",
            "[ ] Mock server running from spec",
            "[ ] All resources follow noun-plural naming convention",
            "[ ] Appropriate HTTP status codes for all operations",
            "[ ] Authentication/authorization documented in spec",
            "[ ] Versioning strategy documented",
            "[ ] Breaking change policy enforced",
            "[ ] API linted with Spectral (zero errors)",
            "[ ] Consumer contract tests in CI pipeline",
        ]
