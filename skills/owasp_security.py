"""
skills/owasp_security.py
OWASP Security — Top 10 2021, STRIDE threat modeling, CVSS 3.1 scoring.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class OWASPSecurity:
    name: str = "OWASP Security"
    principles: List[str] = field(default_factory=lambda: [
        "Defense in Depth — multiple security layers; no single point of failure",
        "Least Privilege — grant minimum permissions required",
        "Fail Securely — errors should default to secure state",
        "Security by Design — integrate security from day 1, not as afterthought",
        "Trust Nothing — validate all input, authenticate all access",
        "Security is Everyone's Responsibility — devs, ops, QA, PM",
    ])
    methodology: List[str] = field(default_factory=lambda: [
        "1. THREAT MODEL — STRIDE analysis on Data Flow Diagrams",
        "2. OWASP SCAN   — Test against Top 10 categories",
        "3. CVSS SCORE   — Quantify severity (Base + Temporal + Environmental)",
        "4. REMEDIATE    — Prioritize by CVSS score; P0 (9.0+) → immediate",
        "5. VERIFY       — Confirm fix, re-scan, close finding",
        "6. HARDEN       — Apply security headers, CSP, HSTS, rate limiting",
    ])
    tools: List[str] = field(default_factory=lambda: [
        "OWASP ZAP (DAST)", "Bandit (Python SAST)",
        "Snyk / Dependabot (SCA)", "Trivy (container scan)",
        "Semgrep (custom SAST rules)",
        "OWASP Threat Dragon (threat modeling)",
        "Burp Suite (manual pentesting)",
    ])
    output_templates: List[str] = field(default_factory=lambda: [
        "STRIDE Threat Model (per DFD element)",
        "OWASP Top 10 Compliance Matrix",
        "Finding Report (ID/Category/CVSS/Description/Remediation)",
        "Security Report per docs/standards/SECURITY_REPORT_TEMPLATE.md",
    ])

    OWASP_TOP_10 = {
        "A01": {"name": "Broken Access Control", "risk": "CRITICAL",
                "controls": ["RBAC/ABAC", "Principle of least privilege", "Audit logging"]},
        "A02": {"name": "Cryptographic Failures", "risk": "HIGH",
                "controls": ["TLS 1.2+", "bcrypt/argon2 for passwords", "No MD5/SHA1"]},
        "A03": {"name": "Injection", "risk": "CRITICAL",
                "controls": ["Parameterized queries", "Input validation", "WAF"]},
        "A04": {"name": "Insecure Design", "risk": "HIGH",
                "controls": ["Threat modeling", "Secure design patterns", "Defense in depth"]},
        "A05": {"name": "Security Misconfiguration", "risk": "HIGH",
                "controls": ["Hardening guides", "IaC scanning", "Disable debug in prod"]},
        "A06": {"name": "Vulnerable & Outdated Components", "risk": "HIGH",
                "controls": ["SCA (Snyk)", "Dependabot alerts", "SBOM"]},
        "A07": {"name": "Identification & Auth Failures", "risk": "CRITICAL",
                "controls": ["MFA", "Secure session management", "Brute force protection"]},
        "A08": {"name": "Software & Data Integrity Failures", "risk": "HIGH",
                "controls": ["Signed artifacts", "SLSA framework", "Dependency pinning"]},
        "A09": {"name": "Security Logging & Monitoring Failures", "risk": "MEDIUM",
                "controls": ["Centralized logging", "Alert on anomalies", "SIEM"]},
        "A10": {"name": "SSRF", "risk": "HIGH",
                "controls": ["Allowlist outbound URLs", "Block metadata endpoints", "Firewall egress"]},
    }

    STRIDE = {
        "S": "Spoofing Identity — Authentication controls",
        "T": "Tampering with Data — Integrity controls (HMAC, signatures)",
        "R": "Repudiation — Non-repudiation (audit logs, digital signatures)",
        "I": "Information Disclosure — Confidentiality controls (encryption, ACL)",
        "D": "Denial of Service — Availability controls (rate limiting, CDN)",
        "E": "Elevation of Privilege — Authorization controls (RBAC, least privilege)",
    }

    def apply(self, context: dict) -> dict:
        components = context.get("components", ["API Gateway", "Auth Service", "Database"])
        findings = context.get("findings", [])

        return {
            "skill": self.name,
            "threat_model": {
                "methodology": "STRIDE per DFD element",
                "components_analyzed": components,
                "stride_categories": self.STRIDE,
                "threats_per_component": {
                    c: [k for k in "STRIDE"] for c in components
                },
            },
            "owasp_assessment": {
                category: {
                    "name": info["name"],
                    "risk_level": info["risk"],
                    "status": "TODO",
                    "controls": info["controls"],
                }
                for category, info in self.OWASP_TOP_10.items()
            },
            "finding_summary": {
                "total": len(findings),
                "critical": sum(1 for f in findings if f.get("severity") == "CRITICAL"),
                "high": sum(1 for f in findings if f.get("severity") == "HIGH"),
                "medium": sum(1 for f in findings if f.get("severity") == "MEDIUM"),
                "low": sum(1 for f in findings if f.get("severity") == "LOW"),
            },
        }

    def cvss_score(
        self,
        av: str = "N",   # Attack Vector: N(etwork)/A(djacent)/L(ocal)/P(hysical)
        ac: str = "L",   # Attack Complexity: L(ow)/H(igh)
        pr: str = "N",   # Privileges Required: N(one)/L(ow)/H(igh)
        ui: str = "N",   # User Interaction: N(one)/R(equired)
        s: str = "U",    # Scope: U(nchanged)/C(hanged)
        c: str = "H",    # Confidentiality: N/L/H
        i: str = "H",    # Integrity: N/L/H
        a: str = "H",    # Availability: N/L/H
    ) -> dict:
        """Return CVSS 3.1 vector string and qualitative rating."""
        vector = f"CVSS:3.1/AV:{av}/AC:{ac}/PR:{pr}/UI:{ui}/S:{s}/C:{c}/I:{i}/A:{a}"
        # Simplified scoring approximation
        impact_map = {"N": 0.0, "L": 0.22, "H": 0.56}
        exploitability = 1.0 if av == "N" else (0.85 if av == "A" else 0.55)
        impact = 1 - (1 - impact_map.get(c, 0)) * (1 - impact_map.get(i, 0)) * (1 - impact_map.get(a, 0))
        score = min(10.0, round(exploitability * impact * 10, 1))
        rating = "CRITICAL" if score >= 9 else "HIGH" if score >= 7 else "MEDIUM" if score >= 4 else "LOW"
        return {"vector": vector, "score": score, "rating": rating}

    def checklist(self) -> List[str]:
        return [
            "[ ] STRIDE threat model completed for all DFD elements",
            "[ ] OWASP Top 10 assessment completed",
            "[ ] All CRITICAL findings have remediation plans",
            "[ ] CVSS scores assigned to all findings",
            "[ ] Secrets scanner run (no hardcoded credentials)",
            "[ ] Dependencies scanned for known CVEs",
            "[ ] Security headers configured (HSTS, CSP, X-Frame-Options)",
            "[ ] Input validation on all user-controlled inputs",
            "[ ] Security findings logged per SECURITY_REPORT_TEMPLATE.md",
        ]
