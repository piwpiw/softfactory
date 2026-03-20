#!/usr/bin/env python3
"""
Project Status Reporter for Telegram
Reads token-tracker.json and generates human-friendly project reports
"""

import json
from pathlib import Path
from datetime import datetime


class ProjectReporter:
    """Generate project status reports for Telegram."""

    def __init__(self, tracker_path: str | None = None):
        if tracker_path is None:
            tracker_path = Path(__file__).parent.parent / "shared-intelligence" / "token-tracker.json"
        self.tracker_path = Path(tracker_path)

    def load_tracker(self) -> dict:
        if not self.tracker_path.exists():
            return {"status": "No tracker file found"}
        with self.tracker_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def generate_summary_report(self) -> str:
        tracker = self.load_tracker()
        if tracker.get("status") == "No tracker file found":
            return "Tracker file not found."

        session = tracker.get("session_summary", {})
        projects = tracker.get("projects", [])

        report = "PROJECT STATUS SUMMARY\n"
        report += "=" * 40 + "\n\n"
        report += f"Budget Status: {session.get('budget_efficiency', 'N/A')}\n"
        report += f"Total Used: {session.get('total_tokens_used', 0):,} tokens\n"
        report += f"Remaining: {session.get('remaining_tokens', 0):,} tokens\n"
        report += f"Session Status: {session.get('session_status', 'UNKNOWN')}\n\n"
        report += "PROJECT BREAKDOWN:\n"
        report += "-" * 40 + "\n"

        for proj in projects:
            status = proj.get("status", "UNKNOWN")
            name = proj.get("name", "Unknown")
            efficiency = proj.get("efficiency", "N/A")

            icon = "[OK]" if "COMPLETE" in status else "[IN_PROGRESS]" if "PROGRESS" in status else "[PENDING]"
            report += f"{icon} {name}\n"
            report += f"  Status: {status}\n"
            report += f"  Efficiency: {efficiency}\n"
            report += f"  Tokens: {proj.get('tokens_actual', 0)}/{proj.get('tokens_budgeted', 0)}\n\n"

        return report

    def generate_detailed_report(self) -> str:
        tracker = self.load_tracker()
        if "status" in tracker:
            return tracker["status"]

        projects = tracker.get("projects", [])
        report = "DETAILED PROJECT REPORT\n"
        report += "=" * 50 + "\n\n"

        for proj in projects:
            name = proj.get("name", "Unknown")
            status = proj.get("status", "UNKNOWN")

            report += f"PROJECT: {name}\n"
            report += f"Status: {status}\n"
            report += f"Lines of Code: {proj.get('lines_of_code', 0)}\n"
            report += f"Efficiency: {proj.get('lines_per_token', 0):.2f} lines/token\n"

            phases = proj.get("phases", {})
            if phases:
                report += "Phases:\n"
                for phase_name, phase_data in phases.items():
                    if isinstance(phase_data, dict):
                        budgeted = phase_data.get("budgeted", 0)
                        actual = phase_data.get("actual", 0)
                        report += f"  {phase_name}: {actual}/{budgeted} tokens\n"
            report += "\n"

        return report

    def generate_alerts_report(self) -> str:
        tracker = self.load_tracker()
        if "status" in tracker:
            return "No alerts available"

        alerts = tracker.get("alerts", [])
        if not alerts:
            return "No alerts at this time. System running smoothly!"

        report = "ALERTS & RECOMMENDATIONS\n"
        report += "=" * 50 + "\n\n"
        for alert in alerts:
            report += f"{alert.get('severity', 'INFO')}\n"
            report += f"Message: {alert.get('message', '')}\n"
            report += f"Recommendation: {alert.get('recommendation', '')}\n\n"
        return report

    def generate_recovery_plan(self) -> str:
        tracker = self.load_tracker()
        if "status" in tracker:
            return "No recovery plan available"

        recovery = tracker.get("recovery_plan", {})
        if not recovery:
            return "All systems nominal!"

        report = "RECOVERY PLAN\n"
        report += f"Status: {recovery.get('status', 'UNKNOWN')}\n"
        report += f"Goal: {recovery.get('goal', '')}\n\n"
        for i, strat in enumerate(recovery.get("strategy", []), 1):
            report += f"{i}. {strat.get('phase', 'Unknown')}\n"
            report += f"   Result: {strat.get('expected_result', '')}\n\n"
        return report

    def generate_optimizations(self) -> str:
        tracker = self.load_tracker()
        if "status" in tracker:
            return "No optimization data available"

        opportunities = tracker.get("optimization_opportunities", [])
        if not opportunities:
            return "All optimizations already applied!"

        report = "OPTIMIZATION OPPORTUNITIES\n"
        report += "=" * 50 + "\n\n"
        for opp in opportunities:
            report += f"Opportunity: {opp.get('opportunity', 'Unknown')}\n"
            report += f"Savings: {opp.get('estimated_savings', '')}\n"
            report += f"Effort: {opp.get('effort', '')}\n\n"
        return report

    def format_for_telegram(self, report_type: str = "summary") -> str:
        if report_type == "detailed":
            text = self.generate_detailed_report()
        elif report_type == "alerts":
            text = self.generate_alerts_report()
        elif report_type == "recovery":
            text = self.generate_recovery_plan()
        elif report_type == "optimizations":
            text = self.generate_optimizations()
        else:
            text = self.generate_summary_report()

        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"<b>Generated: {timestamp}</b>\\n\\n<pre>{text}</pre>"


if __name__ == "__main__":
    import sys

    report_type = sys.argv[1] if len(sys.argv) > 1 else "summary"
    reporter = ProjectReporter()
    if report_type == "all":
        print("\\n" + "=" * 60)
        print(reporter.generate_summary_report())
        print("\\n" + "=" * 60)
        print(reporter.generate_detailed_report())
        print("\\n" + "=" * 60)
        print(reporter.generate_alerts_report())
    else:
        print(
            reporter.generate_summary_report()
            if report_type == "summary"
            else reporter.generate_detailed_report()
            if report_type == "detailed"
            else reporter.generate_alerts_report()
            if report_type == "alerts"
            else reporter.generate_recovery_plan()
            if report_type == "recovery"
            else reporter.generate_optimizations()
        )
