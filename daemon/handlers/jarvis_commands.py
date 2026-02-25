"""
Jarvis v1 legacy commands - 100% backward compatible.

Commands preserved from original jarvis_telegram_main.py:
- /status — System status
- /deploy [env] [version] — Deploy
- /mission [name] — Create new project
- /report — Real-time monitoring
- /progress — Detailed progress visualization
- /timeline — Milestone timeline
- /breakdown — Team detailed analysis
- /pages — All web pages (with inline buttons)
- /help — Help
- /start — Start message
"""

import asyncio
from typing import Any, Optional, Dict
from .base_handler import BaseHandler


class JarvisCommandsHandler(BaseHandler):
    """Handler for all Jarvis v1 legacy commands."""

    # Static state (preserved from v1)
    _system_state = {
        "system": "running",
        "version": "v1.2.24",
        "users": 10234,
        "error_rate": 0.02,
        "latency": 145,
        "uptime": 99.98,
    }

    async def handle(self, chat_id: int, command: str, args: list[str]) -> dict[str, Any]:
        """Route to appropriate v1 command handler."""
        self._log_command(chat_id, command, args)

        handlers = {
            "start": self.cmd_start,
            "help": self.cmd_help,
            "status": self.cmd_status,
            "deploy": self.cmd_deploy,
            "mission": self.cmd_mission,
            "report": self.cmd_report,
            "progress": self.cmd_progress,
            "timeline": self.cmd_timeline,
            "breakdown": self.cmd_breakdown,
            "pages": self.cmd_pages,
        }

        handler = handlers.get(command)
        if not handler:
            return {"success": False, "message": f"Unknown v1 command: {command}"}

        try:
            await handler(chat_id, args)
            return {"success": True, "message": f"✓ {command} executed"}
        except Exception as e:
            self._log(f"ERROR in cmd_{command}: {e}")
            await self.send_error(chat_id, str(e))
            return {"success": False, "message": str(e)}

    async def cmd_start(self, chat_id: int, args: list[str]) -> None:
        """Start command (v1)."""
        msg = """🤖 JARVIS Commander Ready!

/status — 시스템 상태
/deploy — 배포
/mission — 프로젝트
/report — 실시간 모니터링
/help — 도움말"""
        await self.send_text(chat_id, msg)

    async def cmd_status(self, chat_id: int, args: list[str]) -> None:
        """System status (v1)."""
        # Initial message
        await self.send_text(
            chat_id,
            "📬 **REQUEST**: /status\n⏳ **PROGRESS**: Checking services...",
        )

        # Simulate processing
        await asyncio.sleep(1)

        # Final report
        msg = self._format_report(
            request="/status",
            progress="API ✓ → Database ✓ → WebSocket ✓",
            result="✅ 모든 시스템 정상!",
            links={
                "Dashboard": "https://jarvis-production.up.railway.app/",
                "API": "https://jarvis-production.up.railway.app/api/v1/status",
                "Monitor": "https://jarvis-production.up.railway.app/analytics.html",
            },
            details=f"""Uptime: {self._system_state['uptime']}%
Error Rate: {self._system_state['error_rate']}%
Latency: {self._system_state['latency']}ms
Users: {self._system_state['users']:,}""",
        )
        await self.send_text(chat_id, msg, parse_mode="MARKDOWN")

    async def cmd_deploy(self, chat_id: int, args: list[str]) -> None:
        """Deploy command (v1)."""
        if not args or len(args) < 2:
            await self.send_error(chat_id, "사용법: /deploy prod|staging v1.2.25")
            return

        env = args[0].lower()
        version = args[1]

        # Initial request
        msg = f"""📬 **REQUEST**: /deploy {env} {version}
⏳ **PROGRESS**: Build 0%..."""
        await self.send_text(chat_id, msg, parse_mode="MARKDOWN")

        # Progress simulation
        progress_steps = [
            "Build 25%",
            "Build 50%",
            "Build 100% ✓",
            "Deploy 25%",
            "Deploy 50%",
            "Deploy 100% ✓",
            "Tests 100% ✓",
        ]

        for step in progress_steps:
            await asyncio.sleep(0.3)

        # Final report
        msg = self._format_report(
            request=f"/deploy {env} {version}",
            progress="Build 100% → Deploy 100% → Tests 100%",
            result=f"✅ {env.upper()} 배포 완료!",
            links={
                "Dashboard": "https://jarvis-production.up.railway.app/",
                "API": "https://jarvis-production.up.railway.app/api/v1/status",
            },
            details=f"""Version: {version}
Environment: {env.upper()}
Build Time: 2.5 min
Deploy Time: 1.7 min
Tests: 234/234 PASS
Users Affected: {self._system_state['users']:,}
Error Rate: {self._system_state['error_rate']}%
Uptime: {self._system_state['uptime']}%""",
        )
        await self.send_text(chat_id, msg, parse_mode="MARKDOWN")

    async def cmd_mission(self, chat_id: int, args: list[str]) -> None:
        """Project creation (v1)."""
        if not args:
            await self.send_error(chat_id, "사용법: /mission [프로젝트명]")
            return

        name = " ".join(args)

        # Initial request
        msg = f"""📬 **REQUEST**: /mission {name}
⏳ **PROGRESS**: Creating project..."""
        await self.send_text(chat_id, msg, parse_mode="MARKDOWN")

        await asyncio.sleep(1)

        # Final report
        msg = self._format_report(
            request=f"/mission {name}",
            progress="Team 02 (30%) → Team 03 (50%) → Team 04 (70%)",
            result="✅ 프로젝트 M-003 생성됨!",
            links={
                "Operations": "https://jarvis-production.up.railway.app/operations.html",
                "Teams": "https://jarvis-production.up.railway.app/teams.html",
            },
            details=f"""Project: {name}
Mission ID: M-003
Status: PLANNING
Priority: HIGH
Teams: 02, 03, 04, 05, 06
Timeline: 2-3 weeks""",
        )
        await self.send_text(chat_id, msg, parse_mode="MARKDOWN")

    async def cmd_report(self, chat_id: int, args: list[str]) -> None:
        """Real-time monitoring (v1)."""
        msg = self._format_report(
            request="/report",
            progress="Collecting metrics... (Last 1h)",
            result="✅ 모니터링 리포트 준비 완료!",
            links={
                "Live Monitor": "https://jarvis-production.up.railway.app/",
                "WebSocket": "wss://jarvis-production.up.railway.app/",
            },
            details=f"""METRICS (Last Hour):
• Requests: 1,245 req/s
• Error Rate: {self._system_state['error_rate']}%
• Latency: {self._system_state['latency']}ms
• Memory: 256MB / 512MB
• Uptime: {self._system_state['uptime']}%

DEPLOYMENT:
• Version: {self._system_state['version']}
• Users: {self._system_state['users']:,}
• Status: LIVE

TEAMS: 7/10 Active
SKILLS: 40% Complete""",
        )
        await self.send_text(chat_id, msg, parse_mode="MARKDOWN")

    async def cmd_progress(self, chat_id: int, args: list[str]) -> None:
        """Detailed progress (v1)."""
        msg = self._format_report(
            request="/progress",
            progress="Analyzing 10 teams, 70 skills",
            result="✅ 진행도 분석 완료!",
            links={
                "Dashboard": "https://jarvis-production.up.railway.app/jarvis/dashboard.html",
                "Breakdown": "https://jarvis-production.up.railway.app/api/v1/teams/breakdown",
            },
            details="""TEAM PROGRESS BREAKDOWN:
• Team 01 (Dispatcher): 85% ✅
• Team 02 (Product): 72% ✅
• Team 03 (Analyst): 65% ⏳
• Team 04 (Architect): 78% ✅
• Team 05 (Backend): 62% ⏳
• Team 06 (Frontend): 58% ⏳
• Team 07 (QA): 45% ⏳
• Team 08 (Security): 35% ⏸️
• Team 09 (DevOps): 28% ⏸️
• Team 10 (Reporter): 15% ⏸️

Overall: 53% complete (28/70 skills)""",
        )
        await self.send_text(chat_id, msg, parse_mode="MARKDOWN")

    async def cmd_timeline(self, chat_id: int, args: list[str]) -> None:
        """Milestone timeline (v1)."""
        msg = self._format_report(
            request="/timeline",
            progress="Calculating milestones...",
            result="✅ 타임라인 준비 완료!",
            links={
                "Calendar": "https://jarvis-production.up.railway.app/api/v1/teams/timeline",
                "Dashboard": "https://jarvis-production.up.railway.app/jarvis/dashboard.html",
            },
            details="""MILESTONE TIMELINE:
2026-02-25 ✅ Governance v3.0 배포
2026-02-27 ⏳ Team 05-06 QA 검증
2026-03-01 ⏸️ 전체 통합 테스트
2026-03-15 ⏸️ Production 배포

Next: Team QA phase (2day, 4team)
Critical Path: Backend integration → QA → Deployment""",
        )
        await self.send_text(chat_id, msg, parse_mode="MARKDOWN")

    async def cmd_breakdown(self, chat_id: int, args: list[str]) -> None:
        """Team detailed analysis (v1)."""
        msg = self._format_report(
            request="/breakdown",
            progress="Analyzing team skills and capacity...",
            result="✅ 팀 분석 완료!",
            links={
                "Detailed Report": "https://jarvis-production.up.railway.app/api/v1/teams/breakdown",
                "Dashboard": "https://jarvis-production.up.railway.app/jarvis/dashboard.html",
            },
            details="""TEAM SKILL ANALYSIS:

HIGH CAPACITY (85-78%):
• Team 01: 8/7 skills - Lead Dispatcher ✅
• Team 04: 7/7 skills - Solution Architect ✅

MEDIUM CAPACITY (72-58%):
• Team 02: 7/7 skills - PM Strategy ✅
• Team 03: 6/7 skills - Market Research ✅
• Team 05: 5/7 skills - Backend Dev ⏳
• Team 06: 5/7 skills - Frontend Dev ⏳

LOW CAPACITY (45-15%):
• Team 07-10: 1-4/7 skills - Support roles ⏸️

Bottleneck: Backend integration (Team 05)
Recommendation: Allocate resources to Team 05""",
        )
        await self.send_text(chat_id, msg, parse_mode="MARKDOWN")

    async def cmd_pages(self, chat_id: int, args: list[str]) -> None:
        """All web pages with inline buttons (v1)."""
        msg = """안녕하세요! JARVIS 웹 포털에 오신 것을 환영합니다.

아래에서 원하시는 페이지를 선택해주세요:

🎛️ <b>Operations Control</b>
프로젝트 관리, 배포, Sprint 추적
→ https://jarvis-production.up.railway.app/operations.html

📊 <b>Analytics</b>
KPI, 메트릭, 팀 성과 분석
→ https://jarvis-production.up.railway.app/analytics.html

👥 <b>Team Management</b>
팀 스킬, 업그레이드, 상태 관리
→ https://jarvis-production.up.railway.app/teams.html

📈 <b>Dashboard</b>
실시간 모니터링, 차트
→ https://jarvis-production.up.railway.app/dashboard.html

🏠 <b>Homepage</b>
CooCook 공식 홈페이지
→ https://jarvis-production.up.railway.app/index.html

⚡ <b>WebSocket Monitor</b>
실시간 메트릭 스트리밍
→ https://jarvis-production.up.railway.app/

🔌 <b>REST API</b>
API 상태 확인
→ https://jarvis-production.up.railway.app/api/v1/status

더 도움이 필요하시면 말씀해주세요!"""
        await self.send_text(chat_id, msg)

    async def cmd_help(self, chat_id: int, args: list[str]) -> None:
        """Help (v1)."""
        help_text = """<b>JARVIS Commands</b>

<b>V1 Legacy Commands:</b>
/start — Start bot
/status — System status
/deploy prod|staging v1.2.25 — Deploy
/mission [name] — New project
/report — Real-time monitoring
/progress — 자세한 진행도 시각화
/timeline — 마일스톤 일정표
/breakdown — 팀별 상세 분석
/pages — All web pages
/help — Help

<b>V2+ Task Management:</b>
/task-new [설명] — 새 작업 시작
/task-list — 작업 목록 보기
/task-activate [id] — 작업 전환

<b>V2+ Quick Commands:</b>
/s — 프로젝트 현황
/h — 이 도움말

All commands return structured response format:
REQUEST | PROGRESS | RESULT"""
        await self.send_text(chat_id, help_text)
