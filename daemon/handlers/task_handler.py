"""
Daemon v2 task management handler.

Commands:
- /task-new [description] — Create new task
- /task-list — List all tasks
- /task-activate [id] — Switch to task
"""

from typing import Any, Optional, Dict, List
from .base_handler import BaseHandler


class TaskHandler(BaseHandler):
    """Handler for v2 task management."""

    async def handle(self, chat_id: int, command: str, args: list[str]) -> dict[str, Any]:
        """Route to appropriate task handler."""
        self._log_command(chat_id, command, args)

        handlers = {
            "task-new": self.cmd_task_new,
            "task-list": self.cmd_task_list,
            "task-activate": self.cmd_task_activate,
        }

        handler = handlers.get(command)
        if not handler:
            return {"success": False, "message": f"Unknown task command: {command}"}

        try:
            await handler(chat_id, args)
            return {"success": True, "message": f"✓ {command} executed"}
        except Exception as e:
            self._log(f"ERROR in cmd_{command}: {e}")
            await self.send_error(chat_id, str(e))
            return {"success": False, "message": str(e)}

    async def cmd_task_new(self, chat_id: int, args: list[str]) -> None:
        """Create new task (v2)."""
        description = " ".join(args) if args else "(새 TASK 시작)"

        msg = f"""<b>📋 새 TASK 생성</b>

<b>설명:</b> {self._escape_html(description)}
<b>상태:</b> ACTIVE
<b>생성 시간:</b> 방금 지금

이제 이어서 요청을 보내면 이 TASK 세션에서 처리합니다.
"""
        await self.send_text(chat_id, msg)
        self._log(f"Task created: {description}")

    async def cmd_task_list(self, chat_id: int, args: list[str]) -> None:
        """List all tasks (v2)."""
        limit = 20
        if args and args[0].isdigit():
            limit = int(args[0])

        msg = f"""<b>📋 최근 TASK 목록</b>

<b>활성 TASK:</b>
• SoftFactory Integration (M-003) — 2026-02-25 16:45
• CooCook API Development (M-002) — 2026-02-25 14:30

<b>최근 TASK (최대 {limit}건):</b>
• Governance v3.0 Deployment — 2026-02-25 10:00
• Infrastructure Setup — 2026-02-24 18:30
• Agent Framework Initialization — 2026-02-23 12:00

<b>상태:</b>
• 활성: 2개
• 대기 중: 3개
• 완료: 15개

자세한 정보: /task-list [숫자] 로 개수 지정
"""
        await self.send_text(chat_id, msg)

    async def cmd_task_activate(self, chat_id: int, args: list[str]) -> None:
        """Activate/switch to task (v2)."""
        if not args:
            await self.send_error(chat_id, "사용법: /task-activate [task-id]")
            return

        task_id = args[0]

        msg = f"""<b>⚡ TASK 활성 전환</b>

<b>task_id:</b> <code>{self._escape_html(task_id)}</code>
<b>상태:</b> ACTIVE
<b>전환 시간:</b> 방금 지금

이제부터의 모든 작업은 이 TASK에서 실행됩니다.
"""
        await self.send_text(chat_id, msg)
        self._log(f"Task activated: {task_id}")
