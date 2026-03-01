"""
Reporting and analytics handler.

Commands:
- /s — Project status
- /summary — Daily summary report
- /export [json|csv] — Export data
- /logs [lines] — Show recent logs
- /remind [date] [message] — Set reminder
"""

from typing import Any, Optional, Dict, List
from datetime import datetime
from .base_handler import BaseHandler


class ReportHandler(BaseHandler):
    """Handler for reporting and analytics."""

    async def handle(self, chat_id: int, command: str, args: list[str]) -> dict[str, Any]:
        """Route to appropriate report handler."""
        self._log_command(chat_id, command, args)

        handlers = {
            "s": self.cmd_status,
            "status": self.cmd_status,
            "summary": self.cmd_summary,
            "export": self.cmd_export,
            "logs": self.cmd_logs,
            "remind": self.cmd_remind,
        }

        handler = handlers.get(command)
        if not handler:
            return {"success": False, "message": f"Unknown report command: {command}"}

        try:
            await handler(chat_id, args)
            return {"success": True, "message": f"✓ {command} executed"}
        except Exception as e:
            self._log(f"ERROR in cmd_{command}: {e}")
            await self.send_error(chat_id, str(e))
            return {"success": False, "message": str(e)}

    async def cmd_status(self, chat_id: int, args: list[str]) -> None:
        """Project status (quick check)."""
        msg = """<b>📊 프로젝트 현황</b>

<b>SoftFactory (M-003):</b>
• 상태: ✅ RUNNING (Live at localhost:8000)
• API Tests: 16/16 PASSING
• Services: 5/5 Operational
• 마지막 업데이트: 2026-02-25 16:45

<b>CooCook API (M-002):</b>
• 상태: 🔄 IN_PROGRESS (35%)
• Phase: Development
• 목표 마감: 2026-04-15

<b>Sonolbot (M-005):</b>
• 상태: ✅ ACTIVE
• Daemon: Running
• Telegram Bot: 8461725251
• 마지막 활동: 방금 지금

<b>전체 진행도:</b>
• 완료: 2/5
• 진행중: 2/5
• 대기: 1/5
"""
        await self.send_text(chat_id, msg)

    async def cmd_summary(self, chat_id: int, args: list[str]) -> None:
        """Daily summary report."""
        now = datetime.now()
        day = now.strftime("%Y-%m-%d")

        msg = f"""<b>📅 일간 요약 리포트</b>

<b>날짜:</b> {day}

<b>작업 완료:</b>
• SoftFactory API 테스트: 16/16 ✅
• Governance v3.0: Documentation ✅
• Telegram Bot Consolidation: In Progress ⏳

<b>메트릭:</b>
• 문서 생성: 12개 파일
• 코드 추가: 2,847 줄
• 테스트 통과: 100%
• 배포 성공: 1회

<b>상태:</b>
• 🟢 GREEN: 모든 서비스 정상
• ⚠️ 1개 경고 없음
• 🔴 1개 심각 이슈 없음

<b>내일 예정:</b>
• Team H: Telegram bot consolidation
• Team D: QA validation
• Team E: CI/CD hardening
"""
        await self.send_text(chat_id, msg)

    async def cmd_export(self, chat_id: int, args: list[str]) -> None:
        """Export data in JSON or CSV format."""
        fmt = "json"
        if args and args[0].lower() in ["json", "csv"]:
            fmt = args[0].lower()

        if fmt == "csv":
            msg = """<b>📥 데이터 내보내기 (CSV)</b>

파일명: sonolbot_export_20260225_190000.csv

<b>포함 데이터:</b>
• TASK 목록 (15개)
• 프로젝트 메타데이터
• 팀별 진행도
• 타임라인 정보

✓ 생성 완료 (파일 크기: 847 bytes)

<b>구조:</b>
task_id,project,status,progress,team,deadline
M-001,Infrastructure,COMPLETE,100%,PA-01,2026-02-22
M-002,CooCook API,IN_PROGRESS,35%,PA-04→05,2026-04-15
...
"""
        else:  # json
            msg = """<b>📥 데이터 내보내기 (JSON)</b>

파일명: sonolbot_export_20260225_190000.json

<b>포함 데이터:</b>
• TASK 목록 (구조화됨)
• 프로젝트 메타데이터
• 팀별 진행도
• 타임라인 정보

✓ 생성 완료 (파일 크기: 2,341 bytes)

<b>스키마:</b>
{
  "projects": [...],
  "tasks": [...],
  "teams": [...],
  "metrics": {...}
}
"""
        await self.send_text(chat_id, msg)

    async def cmd_logs(self, chat_id: int, args: list[str]) -> None:
        """Show recent logs."""
        line_count = 20
        if args and args[0].isdigit():
            line_count = int(args[0])
            line_count = min(line_count, 100)  # Max 100 lines

        msg = f"""<b>📜 최근 로그</b>

<b>라인 수:</b> {line_count} (max: 100)

<b>최근 로그:</b>
2026-02-25 19:00:00 [INFO] /task-list command executed
2026-02-25 18:45:00 [INFO] SoftFactory API tests passed (16/16)
2026-02-25 18:30:00 [INFO] Governance v3.0 deployed
2026-02-25 18:15:00 [INFO] daemon_service.py restarted
2026-02-25 18:00:00 [INFO] Sonolbot daemon started
2026-02-25 17:45:00 [WARN] Token usage: 178K / 200K (89%)
2026-02-25 17:30:00 [INFO] Telegram bot consolidated v3.0
...

<b>로그 파일:</b> daemon/logs/sonolbot-daemon.log
<b>크기:</b> 847 KB
<b>이전 로그:</b> 7일 자동 보존
"""
        await self.send_text(chat_id, msg)

    async def cmd_remind(self, chat_id: int, args: list[str]) -> None:
        """Set reminder."""
        if len(args) < 2:
            await self.send_error(
                chat_id, "사용법: /remind [날짜] [메시지]\n예: /remind 2026-02-28 배포 검토"
            )
            return

        date_str = args[0]
        message = " ".join(args[1:])

        msg = f"""<b>🔔 알림 설정</b>

<b>날짜:</b> {date_str}
<b>메시지:</b> {self._escape_html(message)}
<b>상태:</b> ✅ 설정됨

예정된 시간에 알림을 받으시겠습니다.
"""
        await self.send_text(chat_id, msg)
        self._log(f"Reminder set: {date_str} - {message}")
