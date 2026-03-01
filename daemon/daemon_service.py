#!/usr/bin/env python3
"""Claude-session based daemon backend for Sonolbot.

Design goals:
- no external app-server dependency
- 1 TASK (workspace) == 1 Claude session context
- per-bot isolated runtime when manager mode is enabled
- hard cutover on task switching (terminate current process before switching)
"""

from __future__ import annotations

import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

try:
    import fcntl  # type: ignore
except Exception:
    fcntl = None  # type: ignore

try:
    import msvcrt  # type: ignore
except Exception:
    msvcrt = None  # type: ignore

# Add project root (D:\Project) to path so scripts/ package is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.bot_config_store import default_config_path, load_config as load_bots_config
from skill_bridge import build_telegram_runtime, get_task_skill, get_telegram_skill


SECURE_FILE_MODE = 0o600
SECURE_DIR_MODE = 0o700
DEFAULT_POLL_INTERVAL_SEC = 1
DEFAULT_LOG_RETENTION_DAYS = 7
DEFAULT_ALLOWED_SKILLS = "sonolbot-telegram,sonolbot-tasks"
DEFAULT_MULTI_BOT_MANAGER_ENABLED = False
DEFAULT_CLAUDE_MODEL = "sonnet"
DEFAULT_CLAUDE_EFFORT = "high"
VALID_CLAUDE_EFFORTS = {"low", "medium", "high"}
DEFAULT_REWRITER_ENABLED = True
DEFAULT_REWRITER_MODEL = "haiku"
DEFAULT_REWRITER_EFFORT = "low"
DEFAULT_REWRITER_TIMEOUT_SEC = 25
DEFAULT_REWRITER_PROMPT_FILE = ".control_panel_rewriter_prompt.txt"
DEFAULT_CLAUDE_IDLE_TIMEOUT_SEC = 600
DEFAULT_CLAUDE_ACTIVITY_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_CLAUDE_ACTIVITY_BACKUP_COUNT = 7
DEFAULT_CLAUDE_ACTIVITY_RETENTION_DAYS = 7
VALID_TELEGRAM_PARSE_MODES = {"HTML", "Markdown", "MarkdownV2"}
DEFAULT_TELEGRAM_PARSE_MODE = "HTML"
CLAUDE_SESSION_MARKER = ".claude_session_started"
CONTROL_PANEL_CONFIG = ".control_panel_telegram_bots.json"
CONTROL_PANEL_PREFS = ".control_panel_claude_prefs.toml"
DAEMON_LOG_PREFIX = "sonolbot-daemon"
WORKER_LOG_PREFIX = "sonolbot-worker"
REWRITER_LOG_PREFIX = "claude-rewriter"

CMD_TASK_LIST = "/task-list"
CMD_TASK_ACTIVATE = "/task-activate"
CMD_TASK_NEW = "/task-new"
CMD_STATUS = "/s"
CMD_HELP = "/h"
TXT_TASK_LIST = "TASK 목록 보기"
TXT_TASK_RESUME = "기존 TASK 이어하기"
TXT_TASK_NEW = "새 TASK 시작하기"
CALLBACK_TASK_SELECT_PREFIX = "__cb__:task_select:"
ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def _popen_windows_hidden_kwargs(
    *,
    new_process_group: bool = True,
    detached: bool = False,
) -> dict[str, Any]:
    if os.name != "nt":
        return {}
    kwargs: dict[str, Any] = {}
    flags = 0
    if new_process_group:
        flags |= int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    if detached:
        flags |= int(getattr(subprocess, "DETACHED_PROCESS", 0))
    flags |= int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if flags > 0:
        kwargs["creationflags"] = flags
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= int(getattr(subprocess, "STARTF_USESHOWWINDOW", 0))
        startupinfo.wShowWindow = 0  # SW_HIDE
        kwargs["startupinfo"] = startupinfo
    except Exception:
        pass
    return kwargs


class _ProcessFileLock:
    """Cross-platform process lock backed by lock + pid file."""

    def __init__(self, lock_file: Path, pid_file: Path, owner_label: str) -> None:
        self.lock_file = lock_file.resolve()
        self.pid_file = pid_file.resolve()
        self.owner_label = owner_label
        self._fd: int | None = None

    def _try_lock_fd(self, fd: int) -> bool:
        if fcntl is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except OSError:
                return False
        if msvcrt is not None:
            try:
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                return True
            except OSError:
                return False
        return True

    def acquire(self) -> None:
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        _secure_dir(self.lock_file.parent)

        fd = os.open(str(self.lock_file), os.O_RDWR | os.O_CREAT, SECURE_FILE_MODE)
        if not self._try_lock_fd(fd):
            os.close(fd)
            raise RuntimeError(f"{self.owner_label} lock is busy: {self.lock_file}")

        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode("utf-8"))
        self._fd = fd

        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        _secure_dir(self.pid_file.parent)
        _write_text(self.pid_file, str(os.getpid()))

    def release(self) -> None:
        if self._fd is None:
            return

        try:
            if fcntl is not None:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            elif msvcrt is not None:
                os.lseek(self._fd, 0, os.SEEK_SET)
                msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        finally:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None

        _safe_unlink(self.pid_file)
        _safe_unlink(self.lock_file)


@dataclass
class QueueItem:
    queue_id: str
    chat_id: int
    task_id: str
    session_key: str
    message_id: int
    text: str
    timestamp: str
    files: list[dict[str, Any]]
    location: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "queue_id": self.queue_id,
            "chat_id": self.chat_id,
            "task_id": self.task_id,
            "session_key": self.session_key,
            "message_id": self.message_id,
            "text": self.text,
            "timestamp": self.timestamp,
            "files": self.files,
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "QueueItem | None":
        try:
            return cls(
                queue_id=str(raw.get("queue_id") or "").strip() or _new_queue_id(),
                chat_id=int(raw.get("chat_id") or 0),
                task_id=str(raw.get("task_id") or "").strip(),
                session_key=str(raw.get("session_key") or "").strip(),
                message_id=int(raw.get("message_id") or 0),
                text=str(raw.get("text") or ""),
                timestamp=str(raw.get("timestamp") or ""),
                files=list(raw.get("files") or []),
                location=raw.get("location") if isinstance(raw.get("location"), dict) else None,
            )
        except Exception:
            return None


class ClaudeDaemonService:
    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parent
        self.logs_dir = Path(os.getenv("LOGS_DIR", str(self.root / "logs"))).resolve()
        self.tasks_dir = Path(os.getenv("TASKS_DIR", str(self.root / "tasks"))).resolve()
        self.store_file = Path(
            os.getenv("TELEGRAM_MESSAGE_STORE", str(self.root / "telegram_messages.json"))
        ).resolve()
        self.is_bot_worker = os.getenv("DAEMON_BOT_WORKER", "0").strip() == "1"
        self.bot_id = str(os.getenv("SONOLBOT_BOT_ID", "") or "").strip()
        self.bot_workspace = Path(os.getenv("SONOLBOT_BOT_WORKSPACE", str(self.root))).resolve()

        self.pid_file = Path(
            os.getenv(
                "DAEMON_PID_FILE",
                str((self.bot_workspace if self.is_bot_worker else self.root) / ".daemon_service.pid"),
            )
        ).resolve()
        self.lock_file = Path(
            os.getenv("DAEMON_LOCK_FILE", str(self.pid_file.with_suffix(".lock")))
        ).resolve()

        self.state_dir = Path(
            os.getenv("DAEMON_STATE_DIR", str((self.bot_workspace if self.is_bot_worker else self.root) / "state"))
        ).resolve()
        self.runner_pid_file = self.state_dir / "claude-runner.pid"
        self.current_run_file = self.state_dir / "current_run.json"
        self.active_tasks_file = self.state_dir / "active_task_by_chat.json"
        self.queue_file = self.state_dir / "task_queue.json"

        self.poll_interval_sec = _env_int_with_legacy(
            "SONOLBOT_DAEMON_POLL_INTERVAL_SEC",
            "DAEMON_POLL_INTERVAL_SEC",
            default=DEFAULT_POLL_INTERVAL_SEC,
            minimum=1,
        )
        self.log_retention_days = max(1, int(os.getenv("LOG_RETENTION_DAYS", str(DEFAULT_LOG_RETENTION_DAYS))))
        self.claude_model = str(os.getenv("SONOLBOT_CLAUDE_MODEL", DEFAULT_CLAUDE_MODEL) or "").strip()
        if not self.claude_model:
            self.claude_model = DEFAULT_CLAUDE_MODEL
        self.claude_effort = str(os.getenv("SONOLBOT_CLAUDE_EFFORT", DEFAULT_CLAUDE_EFFORT) or "").strip().lower()
        if self.claude_effort not in VALID_CLAUDE_EFFORTS:
            self.claude_effort = DEFAULT_CLAUDE_EFFORT
        prefs_path = (self.root / CONTROL_PANEL_PREFS).resolve()
        pref_rewriter_model = _extract_root_toml_string(prefs_path, "rewriter_model")
        pref_rewriter_effort = _extract_root_toml_string(
            prefs_path, "rewriter_model_reasoning_effort"
        ).lower()
        self.rewriter_enabled = _env_bool("SONOLBOT_REWRITER_ENABLED", DEFAULT_REWRITER_ENABLED)
        self.rewriter_model = str(
            os.getenv(
                "SONOLBOT_REWRITER_MODEL",
                pref_rewriter_model or DEFAULT_REWRITER_MODEL,
            )
            or ""
        ).strip().lower()
        if not self.rewriter_model:
            self.rewriter_model = DEFAULT_REWRITER_MODEL
        self.rewriter_effort = str(
            os.getenv(
                "SONOLBOT_REWRITER_EFFORT",
                pref_rewriter_effort or DEFAULT_REWRITER_EFFORT,
            )
            or ""
        ).strip().lower()
        if self.rewriter_effort not in VALID_CLAUDE_EFFORTS:
            self.rewriter_effort = DEFAULT_REWRITER_EFFORT
        self.rewriter_timeout_sec = max(
            5,
            int(os.getenv("SONOLBOT_REWRITER_TIMEOUT_SEC", str(DEFAULT_REWRITER_TIMEOUT_SEC))),
        )
        rewriter_prompt_raw = str(
            os.getenv("SONOLBOT_REWRITER_PROMPT_FILE", DEFAULT_REWRITER_PROMPT_FILE)
            or DEFAULT_REWRITER_PROMPT_FILE
        ).strip()
        rewriter_prompt_path = Path(rewriter_prompt_raw)
        if not rewriter_prompt_path.is_absolute():
            rewriter_prompt_path = (self.root / rewriter_prompt_path).resolve()
        self.rewriter_prompt_file = rewriter_prompt_path
        self.store_claude_session = _env_bool("SONOLBOT_STORE_CLAUDE_SESSION", True)
        self.claude_idle_timeout_sec = max(
            60,
            int(os.getenv("DAEMON_CLAUDE_IDLE_TIMEOUT_SEC", str(DEFAULT_CLAUDE_IDLE_TIMEOUT_SEC))),
        )
        self.claude_activity_file = _resolve_env_path(
            self.root,
            "DAEMON_CLAUDE_ACTIVITY_FILE",
            self.logs_dir / "claude-runner.log",
        )
        self.claude_activity_max_bytes = max(
            1024,
            int(
                os.getenv(
                    "DAEMON_CLAUDE_ACTIVITY_MAX_BYTES",
                    str(DEFAULT_CLAUDE_ACTIVITY_MAX_BYTES),
                )
            ),
        )
        self.claude_activity_backup_count = max(
            0,
            int(
                os.getenv(
                    "DAEMON_CLAUDE_ACTIVITY_BACKUP_COUNT",
                    str(DEFAULT_CLAUDE_ACTIVITY_BACKUP_COUNT),
                )
            ),
        )
        self.claude_activity_retention_days = max(
            1,
            int(
                os.getenv(
                    "DAEMON_CLAUDE_ACTIVITY_RETENTION_DAYS",
                    str(DEFAULT_CLAUDE_ACTIVITY_RETENTION_DAYS),
                )
            ),
        )
        self.telegram_force_parse_mode = _env_bool("DAEMON_TELEGRAM_FORCE_PARSE_MODE", True)
        self.telegram_default_parse_mode = str(
            os.getenv("DAEMON_TELEGRAM_DEFAULT_PARSE_MODE", DEFAULT_TELEGRAM_PARSE_MODE) or ""
        ).strip()
        if self.telegram_default_parse_mode not in VALID_TELEGRAM_PARSE_MODES:
            self.telegram_default_parse_mode = DEFAULT_TELEGRAM_PARSE_MODE
        self.telegram_parse_fallback_raw = _env_bool("DAEMON_TELEGRAM_PARSE_FALLBACK_RAW_ON_FAIL", True)
        self.shutdown_requested = False

        self._process_lock: _ProcessFileLock | None = None
        self.telegram_runtime = build_telegram_runtime()
        self.telegram = get_telegram_skill()
        self.task_skill = get_task_skill()

        self.active_tasks = self._load_active_tasks()
        self.queue: list[QueueItem] = self._load_queue()

        self.current_proc: subprocess.Popen[str] | None = None
        self.current_log_fp = None
        self.current_run: dict[str, Any] | None = self._load_current_run()
        self.cutover_requested: bool = False
        self.cutover_reason: str = ""
        self.claude_session_meta_file = self.logs_dir / "claude-session-current.json"

        self.claude_exe = self._detect_claude_exe()

        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.claude_activity_file.parent.mkdir(parents=True, exist_ok=True)
        _secure_dir(self.logs_dir)
        _secure_dir(self.tasks_dir)
        _secure_dir(self.state_dir)
        _secure_dir(self.claude_activity_file.parent)

    # ---------- lifecycle ----------

    def run(self) -> int:
        self._install_signal_handlers()
        self._acquire_lock()
        self._log("Daemon started")
        self._log(
            "config "
            f"model={self.claude_model} effort={self.claude_effort} "
            f"rewriter_enabled={int(self.rewriter_enabled)} "
            f"rewriter_model={self.rewriter_model} "
            f"rewriter_effort={self.rewriter_effort} "
            f"rewriter_prompt={self.rewriter_prompt_file} "
            f"store_session={int(self.store_claude_session)} "
            f"parse_mode_force={int(self.telegram_force_parse_mode)} "
            f"parse_mode_default={self.telegram_default_parse_mode} "
            f"parse_fallback_raw={int(self.telegram_parse_fallback_raw)}"
        )

        if self.current_run:
            # Recover from stale state left by unexpected exit.
            self._log("Recovering stale current_run state")
            self.current_run = None
            self._save_current_run(None)
            _safe_unlink(self.runner_pid_file)

        try:
            while not self.shutdown_requested:
                self._cleanup_logs()
                self._ingest_pending_messages()
                self._tick_runner()
                time.sleep(self.poll_interval_sec)
        finally:
            self._terminate_current_proc("daemon_shutdown")
            self._release_lock()
            self._log("Daemon stopped")
        return 0

    def _install_signal_handlers(self) -> None:
        def _handler(signum: int, _frame: object) -> None:
            self._log(f"Signal received: {signum}")
            self.shutdown_requested = True

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _handler)
            except Exception:
                continue

    def _acquire_lock(self) -> None:
        if self._process_lock is None:
            self._process_lock = _ProcessFileLock(
                lock_file=self.lock_file,
                pid_file=self.pid_file,
                owner_label="Daemon worker" if self.is_bot_worker else "Daemon",
            )
        self._process_lock.acquire()

    def _release_lock(self) -> None:
        if self._process_lock is not None:
            self._process_lock.release()
            self._process_lock = None

    # ---------- core loop ----------

    def _ingest_pending_messages(self) -> None:
        _, pending, _ = self.telegram.poll_store_and_get_pending(
            runtime=self.telegram_runtime,
            store_path=str(self.store_file),
            include_bot=False,
        )
        if not pending:
            return

        pending = sorted(
            pending,
            key=lambda row: (int(row.get("chat_id") or 0), int(row.get("message_id") or 0)),
        )

        to_mark_processed: list[int] = []

        for msg in pending:
            try:
                message_id = int(msg.get("message_id") or 0)
                chat_id = int(msg.get("chat_id") or 0)
            except Exception:
                continue
            if message_id <= 0 or chat_id == 0:
                continue

            text = str(msg.get("text") or "").strip()
            if self._handle_control_message(chat_id=chat_id, message_id=message_id, text=text):
                to_mark_processed.append(message_id)
                continue

            task = self._ensure_active_task(
                chat_id=chat_id,
                seed_instruction=text,
                source_message_id=message_id,
                timestamp=str(msg.get("timestamp") or ""),
            )
            if task is None:
                self._send_text(chat_id, "TASK 생성/선택에 실패했습니다. 잠시 후 다시 시도해 주세요.")
                continue

            item = QueueItem(
                queue_id=_new_queue_id(),
                chat_id=chat_id,
                task_id=task["task_id"],
                session_key=task["session_key"],
                message_id=message_id,
                text=text,
                timestamp=str(msg.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                files=list(msg.get("files") or []),
                location=msg.get("location") if isinstance(msg.get("location"), dict) else None,
            )
            self.queue.append(item)
            to_mark_processed.append(message_id)

            self._send_ack(
                chat_id=chat_id,
                message_id=message_id,
                stage="요청 접수",
                summary=f"{task['task_id']} 큐에 등록했습니다.",
            )

        if to_mark_processed:
            self.telegram.mark_messages_processed(str(self.store_file), to_mark_processed)
            self._save_queue()

    def _tick_runner(self) -> None:
        if self.current_proc is not None:
            self._sync_runner_pid_files()
            code = self.current_proc.poll()
            if self.cutover_requested:
                self._terminate_current_proc(self.cutover_reason or "task_cutover")
                self.cutover_requested = False
                self.cutover_reason = ""
                return
            if code is None:
                return

            finished = dict(self.current_run or {})
            self._close_current_log_fp()
            self.current_proc = None
            self.current_run = None
            self._save_current_run(None)
            _safe_unlink(self.runner_pid_file)

            self._on_run_finished(finished, code)
            return

        if not self.queue:
            return

        item = self.queue.pop(0)
        self._save_queue()

        active_task_id = self.active_tasks.get(str(item.chat_id), "")
        if active_task_id and active_task_id != item.task_id:
            # stale queue item from previous task selection
            self._log(
                f"drop stale queue item msg={item.message_id} task={item.task_id} active={active_task_id}"
            )
            return

        task_dir = self._task_dir_for(item.chat_id, item.task_id)
        if not task_dir.exists():
            self._log(f"task dir missing; recreate task record task={item.task_id}")
            self._ensure_active_task(
                chat_id=item.chat_id,
                seed_instruction=item.text,
                source_message_id=item.message_id,
                timestamp=item.timestamp,
                force_task_id=item.task_id,
                force_session_key=item.session_key,
            )

        self._start_run(item)

    # ---------- control commands ----------

    def _handle_control_message(self, chat_id: int, message_id: int, text: str) -> bool:
        if not text:
            return False

        if text.startswith(CALLBACK_TASK_SELECT_PREFIX):
            selector = text[len(CALLBACK_TASK_SELECT_PREFIX) :].strip()
            return self._activate_task_by_selector(chat_id, selector, message_id)

        lowered = text.lower()

        if lowered.startswith(CMD_TASK_LIST):
            limit = _extract_limit_from_text(text, default=20)
            self._send_task_list(chat_id, limit=limit)
            return True

        if lowered.startswith(CMD_TASK_NEW):
            seed = text[len(CMD_TASK_NEW) :].strip()
            self._start_new_task_command(chat_id=chat_id, seed=seed, message_id=message_id)
            return True

        if lowered.startswith(CMD_TASK_ACTIVATE):
            selector = text[len(CMD_TASK_ACTIVATE) :].strip()
            if not selector:
                self._send_text(chat_id, "사용법: /task-activate <task_id|검색어>")
                return True
            return self._activate_task_by_selector(chat_id, selector, message_id)

        if text.strip() == TXT_TASK_LIST:
            self._send_task_list(chat_id, limit=20)
            return True

        if text.strip() == TXT_TASK_NEW:
            self._start_new_task_command(chat_id=chat_id, seed="", message_id=message_id)
            return True

        if text.strip() == TXT_TASK_RESUME:
            self._send_task_list(chat_id, limit=20, include_usage=True)
            return True

        if text.startswith("TASK 이어하기"):
            selector = text.replace("TASK 이어하기", "", 1).strip()
            if not selector:
                self._send_task_list(chat_id, limit=20, include_usage=True)
                return True
            return self._activate_task_by_selector(chat_id, selector, message_id)

        if text.startswith("새 TASK 시작하기") and len(text.strip()) > len("새 TASK 시작하기"):
            seed = text.replace("새 TASK 시작하기", "", 1).strip()
            self._start_new_task_command(chat_id=chat_id, seed=seed, message_id=message_id)
            return True

        if lowered.strip() == CMD_STATUS:
            self._send_project_status(chat_id)
            return True

        if lowered.strip() == CMD_HELP:
            self._send_help(chat_id)
            return True

        return False

    def _send_project_status(self, chat_id: int) -> None:
        """Send quick project status overview."""
        from datetime import datetime as _dt
        now = _dt.now().strftime("%Y-%m-%d %H:%M")
        status_lines = [
            "📊 <b>Project Status</b>",
            f"🕐 {now}",
            "",
            "📦 <b>활성 프로젝트</b>",
            "• M-003 SoftFactory ✅ <code>http://localhost:8000</code>",
            "• M-002 CooCook 🔄 30% IN_PROGRESS",
            "• M-004 JARVIS Bot ✅ Railway",
            "",
            "👥 <b>팀 현황</b>",
            "• 01~10 모든 팀 ACTIVE",
            "• Backend/Frontend: M-002 개발 준비",
            "",
            "🤖 <b>데몬</b>",
            "• Sonolbot ✅ RUNNING",
            "• 현재 TASK 수: " + str(len(self.active_tasks)),
        ]
        # Add queue info if any
        if self.queue:
            status_lines.append(f"• 대기 중인 요청: {len(self.queue)}개")
        self._send_text(chat_id, "\n".join(status_lines))

    def _send_help(self, chat_id: int) -> None:
        """Send help text."""
        help_lines = [
            "🤖 <b>Sonolbot 사용법</b>",
            "",
            "<b>💬 자유롭게 말해주세요</b>",
            "  코드 구현, 버그 수정, 분석, 배포 등",
            "  → Claude가 알아서 처리합니다",
            "",
            "<b>📋 TASK 관리</b>",
            "  /task-new [설명] — 새 작업 시작",
            "  /task-list — 작업 목록 보기",
            "  /task-activate [id] — 작업 전환",
            "",
            "<b>⚡ 빠른 커맨드</b>",
            "  /s — 프로젝트 현황",
            "  /h — 이 도움말",
            "",
            "<b>💡 예시</b>",
            "  「SoftFactory 로그인 페이지 버그 고쳐줘」",
            "  「CooCook API 엔드포인트 추가해줘」",
            "  「현재 코드 리뷰해줘」",
            "  「배포 준비 체크해줘」",
        ]
        self._send_text(chat_id, "\n".join(help_lines))

    def _start_new_task_command(self, chat_id: int, seed: str, message_id: int) -> None:
        task = self._create_new_task(
            chat_id=chat_id,
            instruction=seed or "(새 TASK 시작)",
            source_message_id=message_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        if task is None:
            self._send_text(chat_id, "새 TASK 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.")
            return
        self._set_active_task(chat_id, task["task_id"])
        self._request_cutover_if_needed(chat_id, task["task_id"], reason="new_task")
        self._send_text(
            chat_id,
            (
                f"새 TASK를 시작했습니다.\n"
                f"- task_id: <code>{_esc(task['task_id'])}</code>\n"
                f"- workspace: <code>{_esc(task['task_dir'])}</code>\n"
                "이제 이어서 요청을 보내면 이 TASK 세션에서 처리합니다."
            ),
        )

    def _activate_task_by_selector(self, chat_id: int, selector: str, message_id: int) -> bool:
        selector = selector.strip()
        if not selector:
            self._send_task_list(chat_id, limit=20, include_usage=True)
            return True

        row = self._find_task(chat_id, selector)
        if row is None:
            self._send_text(chat_id, f"일치하는 TASK를 찾지 못했습니다: <code>{_esc(selector)}</code>")
            return True

        task_id = str(row.get("task_id") or "").strip()
        if not task_id:
            self._send_text(chat_id, "선택된 TASK 식별자가 비어 있습니다.")
            return True

        self._set_active_task(chat_id, task_id)
        self._request_cutover_if_needed(chat_id, task_id, reason="task_activate")

        if message_id > 0:
            try:
                chat_root = self._chat_task_root(chat_id)
                self.task_skill.record_task_change(
                    tasks_dir=str(chat_root),
                    task_id=task_id,
                    message_id=message_id,
                    source_message_ids=[message_id],
                    change_note="TASK 활성 전환",
                    result_summary=f"활성 TASK를 {task_id}로 전환",
                    logs_dir=str(self.logs_dir),
                )
            except Exception as exc:
                self._log(f"WARN record_task_change(task_activate) failed: {exc}")

        self._send_text(
            chat_id,
            (
                f"TASK를 이어서 진행합니다.\n"
                f"- task_id: <code>{_esc(task_id)}</code>\n"
                f"- title: {_esc(str(row.get('display_title') or row.get('instruction') or ''))}"
            ),
        )
        return True

    def _send_task_list(self, chat_id: int, limit: int = 20, include_usage: bool = False) -> None:
        rows = self._load_task_index(chat_id)
        lines = [f"최근 TASK 목록 (최대 {limit}건)"]
        if not rows:
            lines.append("- 현재 TASK가 없습니다.")
        else:
            for i, row in enumerate(rows[: max(1, limit)], 1):
                task_id = str(row.get("task_id") or "")
                title = str(row.get("display_title") or row.get("instruction") or "")
                title = _truncate(_compact_space(title), 52)
                lines.append(f"{i}. <code>{_esc(task_id)}</code> - {_esc(title)}")

        if include_usage:
            lines.append("")
            lines.append("이어하기: /task-activate <task_id>")
            lines.append("새로 시작: /task-new <요약>")

        self._send_text(chat_id, "\n".join(lines))

    # ---------- task/session ----------

    def _ensure_active_task(
        self,
        chat_id: int,
        seed_instruction: str,
        source_message_id: int,
        timestamp: str,
        force_task_id: str = "",
        force_session_key: str = "",
    ) -> dict[str, Any] | None:
        active = self.active_tasks.get(str(chat_id), "").strip()
        if force_task_id:
            active = force_task_id

        if active:
            existing = self._find_task(chat_id, active)
            if existing is not None:
                return {
                    "task_id": str(existing.get("task_id") or active),
                    "session_key": self._session_key_from_task_id(str(existing.get("task_id") or active)),
                    "task_dir": str(existing.get("task_dir") or self._task_dir_for(chat_id, active)),
                }

        created = self._create_new_task(
            chat_id=chat_id,
            instruction=seed_instruction or "(자동 생성 TASK)",
            source_message_id=source_message_id,
            timestamp=timestamp,
            force_task_id=force_task_id,
            force_session_key=force_session_key,
        )
        if created is None:
            return None

        self._set_active_task(chat_id, created["task_id"])
        return created

    def _create_new_task(
        self,
        chat_id: int,
        instruction: str,
        source_message_id: int,
        timestamp: str,
        force_task_id: str = "",
        force_session_key: str = "",
    ) -> dict[str, Any] | None:
        chat_root = self._chat_task_root(chat_id)
        chat_root.mkdir(parents=True, exist_ok=True)
        _secure_dir(chat_root)

        session_key = force_session_key.strip() or _new_session_key()
        task_id = force_task_id.strip() or f"thread_{session_key}"

        try:
            session = self.task_skill.init_task_session(
                tasks_dir=str(chat_root),
                task_id=task_id,
                thread_id=session_key,
                message_id=source_message_id,
                source_message_ids=[source_message_id] if source_message_id > 0 else [],
                instruction=instruction,
                chat_id=chat_id,
                timestamp=timestamp,
                logs_dir=str(self.logs_dir),
            )
            task_dir = Path(str(session.get("task_dir") or "")).resolve()
            self._ensure_task_guide(task_dir=task_dir, task_id=task_id, session_key=session_key)
            self._sync_task_meta(task_dir=task_dir, session_key=session_key)
            self._log(f"task created chat={chat_id} task={task_id} dir={task_dir}")
            return {
                "task_id": task_id,
                "session_key": session_key,
                "task_dir": str(task_dir),
            }
        except Exception as exc:
            self._log(f"ERROR create task failed chat={chat_id}: {exc}")
            return None

    def _sync_task_meta(self, task_dir: Path, session_key: str) -> None:
        meta_path = task_dir / "task_meta.json"
        meta = _read_json(meta_path, {})
        if not isinstance(meta, dict):
            meta = {}
        meta["session_key"] = session_key
        meta["session_mode"] = "claude_cli"
        meta["claude_resume_mode"] = "-c"
        meta.setdefault("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        meta["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _write_json(meta_path, meta)

    def _ensure_task_guide(self, task_dir: Path, task_id: str, session_key: str) -> None:
        guide = task_dir / "CLAUDE.md"
        if guide.exists():
            return
        # Load project brain for full context injection
        brain_path = Path(__file__).parent / "project_brain.md"
        brain_content = ""
        try:
            if brain_path.exists():
                brain_content = brain_path.read_text(encoding="utf-8").strip()
        except Exception:
            pass
        task_section = (
            "\n\n---\n\n"
            "## THIS SESSION\n\n"
            f"- **task_id:** {task_id}\n"
            f"- **session_key:** {session_key}\n\n"
            "### Session Rules\n"
            "- This folder is your dedicated workspace for this TASK.\n"
            "- New Telegram messages in this session continue the same conversation.\n"
            "- Use sonolbot-telegram and sonolbot-tasks skills when needed.\n"
            "- Save all artifacts (files, reports, code) inside this task folder.\n"
            "- After each implementation, report clearly what was done and invite feedback.\n"
        )
        if brain_content:
            template = brain_content + task_section
        else:
            template = (
                "# TASK GUIDE\n\n"
                f"- task_id: {task_id}\n"
                f"- session_key: {session_key}\n\n"
                "## Operating Rules\n"
                "- This folder is the unique workspace for this TASK session.\n"
                "- Handle only newly delivered telegram message content for this run.\n"
                "- Use sonolbot-telegram and sonolbot-tasks skills when needed.\n"
                "- Keep user-visible responses concise and practical.\n"
                "- Save task artifacts inside this task folder.\n"
            )
        _write_text(guide, template)

    def _set_active_task(self, chat_id: int, task_id: str) -> None:
        self.active_tasks[str(chat_id)] = task_id
        self._save_active_tasks()

    def _request_cutover_if_needed(self, chat_id: int, target_task_id: str, reason: str) -> None:
        if self.current_run is None or self.current_proc is None:
            return
        current_task = str(self.current_run.get("task_id") or "")
        if current_task == target_task_id:
            return
        self.cutover_requested = True
        self.cutover_reason = f"{reason}: chat={chat_id} task={target_task_id}"
        self._log(f"cutover requested {self.cutover_reason}")

    # ---------- claude runner ----------

    def _start_run(self, item: QueueItem) -> None:
        task_dir = self._task_dir_for(item.chat_id, item.task_id)
        task_dir.mkdir(parents=True, exist_ok=True)

        guide_file = task_dir / "CLAUDE.md"
        marker = task_dir / CLAUDE_SESSION_MARKER
        use_continue = marker.exists()

        prompt = self._build_claude_prompt(item)
        cmd = [
            self.claude_exe,
            "-p",
            "--model",
            self.claude_model,
            "--effort",
            self.claude_effort,
        ]
        if use_continue:
            cmd.append("-c")
        cmd.extend(["--dangerously-skip-permissions"])
        if guide_file.exists():
            cmd.extend(["--append-system-prompt-file", str(guide_file)])
        cmd.append(prompt)

        log_file = self.logs_dir / f"claude-run-{datetime.now().strftime('%Y-%m-%d')}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        self.current_log_fp = log_file.open("a", encoding="utf-8")
        start_marker = f"START task={item.task_id} chat={item.chat_id} msg={item.message_id}"
        self.current_log_fp.write(
            f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] START task={item.task_id} "
            f"chat={item.chat_id} msg={item.message_id} cmd={_compact_cmd(cmd)}\n"
        )
        self.current_log_fp.flush()

        env = os.environ.copy()
        env.setdefault("DISABLE_AUTOUPDATER", "1")
        env.setdefault("SONOLBOT_ALLOWED_SKILLS", DEFAULT_ALLOWED_SKILLS)
        # Force all user-visible sends to pass through daemon rewriter pipeline.
        env["SONOLBOT_BLOCK_DIRECT_TELEGRAM_SEND"] = "1"

        try:
            popen_kwargs: dict[str, Any] = _popen_windows_hidden_kwargs(
                new_process_group=True,
                detached=False,
            )
            proc = subprocess.Popen(
                cmd,
                cwd=str(task_dir),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=self.current_log_fp,
                stderr=subprocess.STDOUT,
                text=True,
                **popen_kwargs,
            )
        except Exception as exc:
            self._close_current_log_fp()
            self._send_text(item.chat_id, f"Claude 실행 실패: {_esc(str(exc))}")
            self._log(f"ERROR start run failed task={item.task_id}: {exc}")
            return

        self.current_proc = proc
        self.current_run = {
            "task_id": item.task_id,
            "session_key": item.session_key,
            "chat_id": item.chat_id,
            "message_id": item.message_id,
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "task_dir": str(task_dir),
            "queue_id": item.queue_id,
            "log_file": str(log_file),
            "log_start_marker": start_marker,
        }
        _write_text(marker, self.current_run["started_at"])
        self._save_current_run(self.current_run)
        self._save_claude_session_meta(
            run=self.current_run,
            state="running",
            exit_code=None,
        )
        self._sync_runner_pid_files()
        self._log(
            f"run started pid={proc.pid} task={item.task_id} chat={item.chat_id} msg={item.message_id} continue={use_continue}"
        )

    def _on_run_finished(self, run: dict[str, Any], exit_code: int) -> None:
        chat_id = int(run.get("chat_id") or 0)
        task_id = str(run.get("task_id") or "")
        session_key = str(run.get("session_key") or "")
        message_id = int(run.get("message_id") or 0)
        task_dir = Path(str(run.get("task_dir") or self._task_dir_for(chat_id, task_id))).resolve()

        state = "success" if exit_code == 0 else "error"
        summary = "요청 처리를 마쳤습니다." if exit_code == 0 else f"실행 오류(exit={exit_code})가 발생했습니다."

        if chat_id and task_id:
            try:
                chat_root = self._chat_task_root(chat_id)
                self.task_skill.record_task_change(
                    tasks_dir=str(chat_root),
                    task_id=task_id,
                    thread_id=session_key,
                    message_id=message_id,
                    source_message_ids=[message_id] if message_id > 0 else [],
                    change_note=f"Claude run finished ({state})",
                    result_summary=summary,
                    logs_dir=str(self.logs_dir),
                )
            except Exception as exc:
                self._log(f"WARN record_task_change(run_finished) failed: {exc}")

            # keep minimal operational feedback; main conversation should be handled by Claude in task workspace
            if exit_code != 0:
                self._send_text(
                    chat_id,
                    (
                        "작업 실행 중 오류가 발생했습니다.\n"
                        f"- task_id: <code>{_esc(task_id)}</code>\n"
                        f"- exit: <code>{exit_code}</code>"
                    ),
                )
            else:
                self._relay_run_output_to_chat(run=run, chat_id=chat_id)

        self._sync_task_meta_on_finish(task_dir=task_dir, exit_code=exit_code)
        self._save_claude_session_meta(
            run=run,
            state="finished",
            exit_code=exit_code,
        )
        self._log(f"run finished task={task_id} chat={chat_id} msg={message_id} exit={exit_code}")

    def _sync_task_meta_on_finish(self, task_dir: Path, exit_code: int) -> None:
        meta_path = task_dir / "task_meta.json"
        meta = _read_json(meta_path, {})
        if not isinstance(meta, dict):
            meta = {}
        meta["last_exit_code"] = int(exit_code)
        meta["last_run_finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _write_json(meta_path, meta)

    def _relay_run_output_to_chat(self, run: dict[str, Any], chat_id: int) -> None:
        if chat_id == 0:
            return

        text = self._extract_run_output_text(run)
        if not text:
            self._send_text(chat_id, "요청을 처리했습니다.")
            self._log(f"stdout relay fallback summary sent chat={chat_id}")
            return

        chunks = _split_text_chunks(text, max_len=3500)
        if not chunks:
            self._send_text(chat_id, "요청을 처리했습니다.")
            self._log(f"stdout relay empty_chunks summary sent chat={chat_id}")
            return

        for chunk in chunks:
            send_chunk = self._rewrite_answer_message(chunk) or chunk
            self._send_text(chat_id, send_chunk)
        self._log(
            f"stdout relay sent chat={chat_id} chunks={len(chunks)} chars={len(text)} rewriter={int(self.rewriter_enabled)}"
        )

    def _extract_run_output_text(self, run: dict[str, Any]) -> str:
        log_file_raw = str(run.get("log_file") or "").strip()
        if not log_file_raw:
            return ""
        log_file = Path(log_file_raw)
        if not log_file.is_absolute():
            log_file = (self.logs_dir / log_file).resolve()
        if not log_file.exists():
            return ""

        try:
            content = log_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""

        marker = str(run.get("log_start_marker") or "").strip()
        segment = content
        if marker:
            idx = content.rfind(marker)
            if idx >= 0:
                segment = content[idx + len(marker) :]
                if "\n" in segment:
                    segment = segment.split("\n", 1)[1]
            else:
                segment = content[-8000:]
        else:
            segment = content[-8000:]

        segment = segment.replace("\r\n", "\n").replace("\r", "\n")
        segment = _strip_ansi_codes(segment)
        return segment.strip()

    def _has_send_event_since_run_start(self, chat_id: int, started_at: str) -> bool:
        started_dt = _parse_local_ts(started_at)
        day = started_at[:10] if len(started_at) >= 10 else datetime.now().strftime("%Y-%m-%d")
        send_log = self.logs_dir / f"{day}.log"
        if not send_log.exists():
            return False

        try:
            lines = send_log.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            return False

        for raw in lines:
            line = raw.strip()
            if not line.startswith("{"):
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if str(row.get("direction") or "") != "send":
                continue
            details = row.get("details")
            if not isinstance(details, dict):
                continue
            try:
                target_chat = int(details.get("chat_id") or 0)
            except Exception:
                continue
            if target_chat != chat_id:
                continue
            if started_dt is None:
                return True
            ts_dt = _parse_local_ts(str(row.get("timestamp") or ""))
            if ts_dt is None or ts_dt >= started_dt:
                return True
        return False

    def _terminate_current_proc(self, reason: str) -> None:
        if self.current_proc is None:
            return

        proc = self.current_proc
        run = dict(self.current_run or {})
        self._log(f"terminate current proc pid={proc.pid} reason={reason}")

        try:
            proc.terminate()
        except Exception:
            pass

        deadline = time.time() + 8.0
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            time.sleep(0.2)

        if proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass

        exit_code = proc.poll()
        if exit_code is None:
            exit_code = -9

        self._close_current_log_fp()
        self.current_proc = None
        self.current_run = None
        self._save_current_run(None)
        _safe_unlink(self.runner_pid_file)

        chat_id = int(run.get("chat_id") or 0)
        task_id = str(run.get("task_id") or "")
        session_key = str(run.get("session_key") or "")
        message_id = int(run.get("message_id") or 0)

        if chat_id and task_id:
            try:
                chat_root = self._chat_task_root(chat_id)
                self.task_skill.record_task_change(
                    tasks_dir=str(chat_root),
                    task_id=task_id,
                    thread_id=session_key,
                    message_id=message_id,
                    source_message_ids=[message_id] if message_id > 0 else [],
                    change_note=f"Claude run terminated ({reason})",
                    result_summary=f"작업 전환/종료로 중단됨: {reason}",
                    logs_dir=str(self.logs_dir),
                )
            except Exception as exc:
                self._log(f"WARN record_task_change(terminate) failed: {exc}")
        self._save_claude_session_meta(
            run=run,
            state=f"terminated:{reason}",
            exit_code=exit_code,
        )

    def _build_claude_prompt(self, item: QueueItem) -> str:
        lines = [
            "텔레그램에서 수신한 새 메시지를 전달합니다.",
            "이 메시지 1건만 현재 TASK 세션 문맥에서 처리하세요.",
            "사용자 응답/진행 안내/파일 전송이 필요하면 sonolbot-telegram, sonolbot-tasks 스킬 규칙을 따르세요.",
            f"[CHAT_ID] {item.chat_id}",
            f"[TASK_ID] {item.task_id}",
            f"[SESSION_KEY] {item.session_key}",
            f"[MESSAGE_ID] {item.message_id}",
            f"[TIMESTAMP] {item.timestamp}",
            "[USER_MESSAGE]",
            item.text or "(텍스트 없음)",
        ]

        if item.files:
            lines.append("[FILES]")
            for f in item.files:
                fpath = str(f.get("path") or "").strip()
                ftype = str(f.get("type") or "file").strip()
                if fpath:
                    lines.append(f"- {ftype}: {fpath}")

        if item.location:
            lat = item.location.get("latitude")
            lon = item.location.get("longitude")
            if lat is not None and lon is not None:
                lines.append(f"[LOCATION] lat={lat}, lon={lon}")

        lines.append("처리가 끝나면 필요한 결과를 사용자에게 전달하고 종료하세요.")
        return "\n".join(lines)

    # ---------- state/files ----------

    def _sync_runner_pid_files(self) -> None:
        pid = 0
        if self.current_proc is not None and self.current_proc.poll() is None:
            pid = int(self.current_proc.pid)

        if pid > 0:
            _write_text(self.runner_pid_file, str(pid))
        else:
            _safe_unlink(self.runner_pid_file)

    def _load_active_tasks(self) -> dict[str, str]:
        data = _read_json(self.active_tasks_file, {})
        if not isinstance(data, dict):
            return {}
        out: dict[str, str] = {}
        for k, v in data.items():
            key = str(k).strip()
            val = str(v).strip()
            if key and val:
                out[key] = val
        return out

    def _save_active_tasks(self) -> None:
        _write_json(self.active_tasks_file, self.active_tasks)

    def _load_queue(self) -> list[QueueItem]:
        data = _read_json(self.queue_file, {"items": []})
        if not isinstance(data, dict):
            return []
        out: list[QueueItem] = []
        for raw in data.get("items", []):
            if not isinstance(raw, dict):
                continue
            item = QueueItem.from_dict(raw)
            if item is None:
                continue
            if item.chat_id == 0 or not item.task_id:
                continue
            out.append(item)
        return out

    def _save_queue(self) -> None:
        _write_json(self.queue_file, {"items": [v.to_dict() for v in self.queue]})

    def _load_current_run(self) -> dict[str, Any] | None:
        data = _read_json(self.current_run_file, {})
        if not isinstance(data, dict):
            return None
        if not data:
            return None
        return data

    def _save_current_run(self, run: dict[str, Any] | None) -> None:
        _write_json(self.current_run_file, run or {})

    def _load_task_index(self, chat_id: int) -> list[dict[str, Any]]:
        index_path = self._chat_task_root(chat_id) / "index.json"
        raw = _read_json(index_path, {"tasks": []})
        if not isinstance(raw, dict):
            return []
        tasks = raw.get("tasks")
        if not isinstance(tasks, list):
            return []
        out = [row for row in tasks if isinstance(row, dict)]
        out.sort(key=lambda row: int(row.get("latest_message_id") or row.get("message_id") or 0), reverse=True)
        return out

    def _find_task(self, chat_id: int, selector: str) -> dict[str, Any] | None:
        selector = selector.strip()
        if not selector:
            return None

        rows = self._load_task_index(chat_id)
        if not rows:
            return None

        normalized = selector
        if selector.startswith("session_"):
            normalized = f"thread_{selector[len('session_'):]}"

        for row in rows:
            task_id = str(row.get("task_id") or "").strip()
            if task_id == selector or task_id == normalized:
                return row

        needle = selector.lower()
        for row in rows:
            hay = " ".join(
                [
                    str(row.get("display_title") or ""),
                    str(row.get("display_subtitle") or ""),
                    str(row.get("instruction") or ""),
                ]
            ).lower()
            if needle and needle in hay:
                return row

        if selector.isdigit():
            mid = int(selector)
            for row in rows:
                if int(row.get("message_id") or 0) == mid:
                    return row
                if int(row.get("latest_message_id") or 0) == mid:
                    return row

        return None

    def _task_dir_for(self, chat_id: int, task_id: str) -> Path:
        return self._chat_task_root(chat_id) / task_id

    def _chat_task_root(self, chat_id: int) -> Path:
        return self.tasks_dir / f"chat_{int(chat_id)}"

    @staticmethod
    def _session_key_from_task_id(task_id: str) -> str:
        text = str(task_id or "").strip()
        if text.startswith("thread_"):
            return text[len("thread_") :]
        return text

    # ---------- telegram helpers ----------

    def _rewrite_ack_message(self, stage: str, summary: str = "", details: str = "") -> str:
        prompt_lines = [
            "아래 중간 진행 안내 원문을 텔레그램 사용자용으로 재작성하세요.",
            "의미는 유지하고, 더 간결하고 친절한 한국어로 바꿔 주세요.",
            "[원문 안내]",
            f"진행 단계: {(stage or '').strip() or '요청 접수'}",
        ]
        summary_text = (summary or "").strip()
        if summary_text:
            prompt_lines.append(f"요약: {summary_text}")
        detail_text = (details or "").strip()
        if detail_text:
            prompt_lines.append(f"상세: {detail_text}")
        prompt_lines.append("재작성 결과만 출력하세요.")
        prompt = "\n".join(prompt_lines)
        return self._run_rewriter(prompt=prompt, rewrite_kind="ack")

    def _rewrite_answer_message(self, answer_text: str) -> str:
        src = str(answer_text or "").strip()
        if not src:
            return ""
        prompt = "\n".join(
            [
                "아래는 메인 어시스턴트의 사용자 응답 원문입니다.",
                "의미를 유지하면서 전달 문장을 다듬어 주세요.",
                "[응답 원문]",
                src,
                "재작성 결과만 출력하세요.",
            ]
        )
        return self._run_rewriter(prompt=prompt, rewrite_kind="answer")

    def _run_rewriter(self, prompt: str, rewrite_kind: str) -> str:
        if not self.rewriter_enabled:
            return ""
        input_text = str(prompt or "").strip()
        if not input_text:
            return ""

        cmd = [
            self.claude_exe,
            "-p",
            "--model",
            self.rewriter_model,
            "--effort",
            self.rewriter_effort,
            "--dangerously-skip-permissions",
        ]
        if self.rewriter_prompt_file.exists():
            cmd.extend(["--append-system-prompt-file", str(self.rewriter_prompt_file)])
        cmd.append(input_text)

        env = os.environ.copy()
        env.setdefault("DISABLE_AUTOUPDATER", "1")
        env.setdefault("SONOLBOT_ALLOWED_SKILLS", DEFAULT_ALLOWED_SKILLS)

        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            run_kwargs: dict[str, Any] = {
                "cwd": str(self.root),
                "env": env,
                "stdin": subprocess.DEVNULL,
                "capture_output": True,
                "text": True,
                "timeout": self.rewriter_timeout_sec,
            }
            run_kwargs.update(
                _popen_windows_hidden_kwargs(
                    new_process_group=True,
                    detached=False,
                )
            )
            result = subprocess.run(cmd, **run_kwargs)
            raw_out = _strip_ansi_codes(str(result.stdout or "")).strip()
            raw_err = _strip_ansi_codes(str(result.stderr or "")).strip()
            output = raw_out
            if result.returncode != 0 and raw_err:
                output = raw_err
            self._log_rewriter_run(
                started_at=started_at,
                rewrite_kind=rewrite_kind,
                cmd=cmd,
                exit_code=int(result.returncode),
                output=output,
            )
            return output.strip()
        except subprocess.TimeoutExpired:
            self._log_rewriter_run(
                started_at=started_at,
                rewrite_kind=rewrite_kind,
                cmd=cmd,
                exit_code=-124,
                output=f"timeout after {self.rewriter_timeout_sec}s",
            )
            return ""
        except Exception as exc:
            self._log_rewriter_run(
                started_at=started_at,
                rewrite_kind=rewrite_kind,
                cmd=cmd,
                exit_code=-1,
                output=f"exception: {exc}",
            )
            return ""

    def _log_rewriter_run(
        self,
        started_at: str,
        rewrite_kind: str,
        cmd: list[str],
        exit_code: int,
        output: str,
    ) -> None:
        path = self.logs_dir / f"{REWRITER_LOG_PREFIX}-{datetime.now().strftime('%Y-%m-%d')}.log"
        lines = [
            f"[{started_at}] START kind={rewrite_kind} cmd={_compact_cmd(cmd)}",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] END kind={rewrite_kind} exit={exit_code}",
        ]
        body = str(output or "").strip()
        if body:
            lines.append(_truncate(body, 6000))
        lines.append("")
        _append_text(path, "\n".join(lines))

    def _send_ack(self, chat_id: int, message_id: int, stage: str, summary: str = "") -> None:
        fallback = f"[{stage}] {summary}".strip()
        rewritten = self._rewrite_ack_message(stage=stage, summary=summary)
        if rewritten:
            self._send_text(chat_id, rewritten)
            return
        if self.telegram_force_parse_mode:
            self._send_text(chat_id, fallback)
            return
        try:
            if hasattr(self.telegram, "send_ack_and_progress"):
                self.telegram.send_ack_and_progress(
                    runtime=self.telegram_runtime,
                    chat_id=chat_id,
                    message_id=message_id,
                    stage=stage,
                    summary=summary,
                )
                return
        except Exception as exc:
            self._log(f"WARN send_ack_and_progress failed: {exc}")

        self._send_text(chat_id, fallback)

    def _send_text(self, chat_id: int, text: str) -> None:
        text = str(text or "").strip()
        if not text:
            return
        parse_mode = self.telegram_default_parse_mode if self.telegram_force_parse_mode else ""
        try:
            if parse_mode and hasattr(self.telegram, "send_text_raw"):
                ok = bool(
                    self.telegram.send_text_raw(
                        self.telegram_runtime,
                        chat_id=chat_id,
                        text=text,
                        parse_mode=parse_mode,
                    )
                )
                if not ok and self.telegram_parse_fallback_raw:
                    ok = bool(
                        self.telegram.send_text_raw(
                            self.telegram_runtime,
                            chat_id=chat_id,
                            text=text,
                            parse_mode=None,
                        )
                    )
                if ok:
                    return
            if hasattr(self.telegram, "send_text_with_policy"):
                ok = self.telegram.send_text_with_policy(
                    runtime=self.telegram_runtime,
                    chat_id=chat_id,
                    text=text,
                )
                if bool(ok):
                    return
            if hasattr(self.telegram, "send_text_retry"):
                ok = self.telegram.send_text_retry(
                    runtime=self.telegram_runtime,
                    chat_id=chat_id,
                    text=text,
                )
                if bool(ok):
                    return
            self.telegram.send_text_raw(
                self.telegram_runtime,
                chat_id=chat_id,
                text=text,
                parse_mode=(parse_mode or None),
            )
        except Exception as exc:
            self._log(f"WARN telegram send failed chat={chat_id}: {exc}")

    # ---------- runtime/logging ----------

    def _detect_claude_exe(self) -> str:
        env_value = str(os.getenv("CLAUDE_EXE", "") or "").strip()
        if env_value:
            return env_value

        candidates = [
            str(Path.home() / ".local" / "bin" / "claude.exe"),
            str(Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd"),
            str(Path.home() / "AppData" / "Local" / "Programs" / "claude" / "claude.exe"),
            str(Path.home() / ".claude" / "claude.exe"),
            str(Path.home() / ".local" / "bin" / "claude"),
            "claude.cmd",
            "claude.exe",
            "claude",
        ]
        for value in candidates:
            if os.path.sep in value:
                if Path(value).exists():
                    return value
            else:
                if _which(value):
                    return value
        return "claude"

    def _log(self, message: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        role = "worker" if self.is_bot_worker else "daemon"
        line = f"[{ts}] [{role}] {message}\n"

        daily_worker = self.logs_dir / f"{WORKER_LOG_PREFIX}-{datetime.now().strftime('%Y-%m-%d')}.log"
        _append_text(daily_worker, line)

        # manager/main logs
        if not self.is_bot_worker:
            daily_daemon = self.logs_dir / f"{DAEMON_LOG_PREFIX}-{datetime.now().strftime('%Y-%m-%d')}.log"
            _append_text(daily_daemon, line)
        self._write_activity_log(line)

    def _cleanup_logs(self) -> None:
        cutoff = datetime.now().date() - timedelta(days=self.log_retention_days - 1)
        for p in self.logs_dir.glob("*.log"):
            date_text = _extract_date_from_name(p.stem)
            if not date_text:
                continue
            try:
                d = datetime.strptime(date_text, "%Y-%m-%d").date()
            except ValueError:
                continue
            if d < cutoff:
                _safe_unlink(p)
        self._cleanup_activity_files()

    def _write_activity_log(self, line: str) -> None:
        self._rotate_activity_file_if_needed()
        _append_text(self.claude_activity_file, line)
        self._cleanup_activity_files()

    def _rotate_activity_file_if_needed(self) -> None:
        path = self.claude_activity_file
        if not path.exists():
            return
        try:
            current_size = path.stat().st_size
        except OSError:
            return
        if current_size < self.claude_activity_max_bytes:
            return
        if self.claude_activity_backup_count <= 0:
            _safe_unlink(path)
            return
        oldest = path.with_name(f"{path.name}.{self.claude_activity_backup_count}")
        _safe_unlink(oldest)
        for idx in range(self.claude_activity_backup_count - 1, 0, -1):
            src = path.with_name(f"{path.name}.{idx}")
            dst = path.with_name(f"{path.name}.{idx + 1}")
            if not src.exists():
                continue
            try:
                src.replace(dst)
            except OSError:
                continue
        dst1 = path.with_name(f"{path.name}.1")
        try:
            path.replace(dst1)
        except OSError:
            return

    def _cleanup_activity_files(self) -> None:
        cutoff = datetime.now() - timedelta(days=self.claude_activity_retention_days)
        candidates = [self.claude_activity_file]
        candidates.extend(self.claude_activity_file.parent.glob(f"{self.claude_activity_file.name}.*"))
        for path in candidates:
            if not path.exists():
                continue
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
            except OSError:
                continue
            if mtime < cutoff:
                _safe_unlink(path)

    def _save_claude_session_meta(
        self,
        run: dict[str, Any],
        state: str,
        exit_code: int | None,
    ) -> None:
        if not self.store_claude_session:
            return
        payload = {
            "transport": "claude_cli",
            "model": self.claude_model,
            "reasoning_effort": self.claude_effort,
            "chat_id": int(run.get("chat_id") or 0),
            "task_id": str(run.get("task_id") or ""),
            "thread_id": str(run.get("session_key") or ""),
            "message_id": int(run.get("message_id") or 0),
            "state": str(state or "").strip() or "unknown",
            "exit_code": int(exit_code) if isinstance(exit_code, int) else None,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        try:
            _write_json(self.claude_session_meta_file, payload)
        except Exception:
            return

    def _close_current_log_fp(self) -> None:
        if self.current_log_fp is None:
            return
        try:
            self.current_log_fp.flush()
            self.current_log_fp.close()
        except Exception:
            pass
        self.current_log_fp = None


class MultiBotManager:
    """Root daemon manager: one worker process per active bot."""

    def __init__(self) -> None:
        self.root = Path(__file__).resolve().parent
        self.logs_dir = Path(os.getenv("LOGS_DIR", str(self.root / "logs"))).resolve()
        self.pid_file = Path(os.getenv("DAEMON_PID_FILE", str(self.root / ".daemon_service.pid"))).resolve()
        self.lock_file = Path(os.getenv("DAEMON_LOCK_FILE", str(self.pid_file.with_suffix(".lock")))).resolve()
        self.poll_interval_sec = _env_int_with_legacy(
            "SONOLBOT_DAEMON_POLL_INTERVAL_SEC",
            "DAEMON_POLL_INTERVAL_SEC",
            default=DEFAULT_POLL_INTERVAL_SEC,
            minimum=1,
        )
        self.log_retention_days = max(1, int(os.getenv("LOG_RETENTION_DAYS", str(DEFAULT_LOG_RETENTION_DAYS))))
        self.workspace_root = Path(
            os.getenv("SONOLBOT_BOT_WORKSPACES_DIR", str(self.root / "bots"))
        ).resolve()
        self.config_path = default_config_path(self.root)
        self.python_bin = self._detect_python_bin()
        self.stop_requested = False
        self.workers: dict[str, dict[str, Any]] = {}
        self._process_lock: _ProcessFileLock | None = None

        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        _secure_dir(self.logs_dir)
        _secure_dir(self.workspace_root)

    def run(self) -> int:
        self._install_signal_handlers()
        self._acquire_lock()
        self._log("manager started")
        self._log(f"manager runtime python_bin={self.python_bin}")

        try:
            while not self.stop_requested:
                self._cleanup_logs()
                desired = {str(row["bot_id"]): row for row in self._load_active_bots()}

                for bot_id in list(self.workers.keys()):
                    if bot_id not in desired:
                        self._stop_worker(bot_id, "bot_deactivated")

                for bot_id, bot in desired.items():
                    self._ensure_worker(bot)

                time.sleep(self.poll_interval_sec)
        finally:
            for bot_id in list(self.workers.keys()):
                self._stop_worker(bot_id, "manager_shutdown")
            self._release_lock()
            self._log("manager stopped")
        return 0

    def _install_signal_handlers(self) -> None:
        def _handler(signum: int, _frame: object) -> None:
            self._log(f"signal received: {signum}")
            self.stop_requested = True

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _handler)
            except Exception:
                continue

    def _acquire_lock(self) -> None:
        if self._process_lock is None:
            self._process_lock = _ProcessFileLock(
                lock_file=self.lock_file,
                pid_file=self.pid_file,
                owner_label="Daemon manager",
            )
        self._process_lock.acquire()

    def _release_lock(self) -> None:
        if self._process_lock is not None:
            self._process_lock.release()
            self._process_lock = None

    def _detect_python_bin(self) -> str:
        venv_pyw_win = self.root / ".venv" / "Scripts" / "pythonw.exe"
        if venv_pyw_win.exists():
            return str(venv_pyw_win)

        venv_py_win = self.root / ".venv" / "Scripts" / "python.exe"
        if venv_py_win.exists():
            return str(venv_py_win)

        venv_py = self.root / ".venv" / "bin" / "python"
        if venv_py.exists():
            return str(venv_py)

        for name in ("python3", "python", "py"):
            found = _which(name)
            if found:
                return found

        return sys.executable

    def _load_active_bots(self) -> list[dict[str, Any]]:
        cfg = load_bots_config(self.config_path)
        allowed_users = cfg.get("allowed_users_global") if isinstance(cfg, dict) else []
        if not isinstance(allowed_users, list):
            allowed_users = []

        normalized_users: list[int] = []
        for raw in allowed_users:
            try:
                uid = int(raw)
            except Exception:
                continue
            if uid > 0:
                normalized_users.append(uid)

        out: list[dict[str, Any]] = []
        bots = cfg.get("bots") if isinstance(cfg, dict) else []
        if not isinstance(bots, list):
            return out

        for row in bots:
            if not isinstance(row, dict):
                continue
            if not bool(row.get("active", False)):
                continue
            token = str(row.get("token") or "").strip()
            bot_id = str(row.get("bot_id") or "").strip()
            if not token or not bot_id:
                continue
            if not normalized_users:
                continue
            out.append(
                {
                    "bot_id": bot_id,
                    "token": token,
                    "allowed_users_global": normalized_users,
                    "bot_username": str(row.get("bot_username") or "").strip(),
                    "bot_name": str(row.get("bot_name") or "").strip(),
                }
            )
        return out

    def _workspace_for_bot(self, bot_id: str) -> Path:
        key = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(bot_id).strip()) or "unknown"
        return (self.workspace_root / key).resolve()

    def _worker_env(self, bot: dict[str, Any], workspace: Path) -> dict[str, str]:
        env = os.environ.copy()
        allowed = [int(v) for v in (bot.get("allowed_users_global") or []) if int(v) > 0]
        allowed_raw = ",".join(str(v) for v in allowed)

        logs_dir = workspace / "logs"
        tasks_dir = workspace / "tasks"
        messages_dir = workspace / "messages"
        state_dir = workspace / "state"
        results_dir = workspace / "results"
        for p in (logs_dir, tasks_dir, messages_dir, state_dir, results_dir):
            p.mkdir(parents=True, exist_ok=True)
            _secure_dir(p)

        env["DAEMON_BOT_WORKER"] = "1"
        env["SONOLBOT_MULTI_BOT_MANAGER"] = "0"
        env["SONOLBOT_BOT_ID"] = str(bot["bot_id"])
        env["SONOLBOT_BOT_WORKSPACE"] = str(workspace)
        env["SONOLBOT_BOTS_CONFIG"] = str(self.config_path)

        env["TELEGRAM_BOT_TOKEN"] = str(bot["token"])
        env["TELEGRAM_ALLOWED_USERS"] = allowed_raw
        env["TELEGRAM_USER_ID"] = str(allowed[0]) if allowed else ""

        env["WORK_DIR"] = str(workspace)
        env["LOGS_DIR"] = str(logs_dir)
        env["TASKS_DIR"] = str(tasks_dir)
        env["TELEGRAM_TASKS_DIR"] = str(tasks_dir)
        env["TELEGRAM_LOGS_DIR"] = str(logs_dir)
        env["TASKS_LOGS_DIR"] = str(logs_dir)
        env["TELEGRAM_MESSAGE_STORE"] = str(messages_dir / "telegram_messages.json")

        env["DAEMON_STATE_DIR"] = str(state_dir)
        env["DAEMON_PID_FILE"] = str(state_dir / "daemon-worker.pid")
        env["DAEMON_LOCK_FILE"] = str(state_dir / "daemon-worker.lock")
        env.setdefault("SONOLBOT_ALLOWED_SKILLS", DEFAULT_ALLOWED_SKILLS)
        return env

    @staticmethod
    def _worker_log_tail(workspace: Path, max_lines: int = 8) -> str:
        logs_dir = workspace / "logs"
        today = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        if not today.exists():
            return ""
        try:
            lines = today.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return ""
        if not lines:
            return ""
        return " | ".join(lines[-max_lines:])

    def _ensure_worker(self, bot: dict[str, Any]) -> None:
        bot_id = str(bot["bot_id"])
        workspace = self._workspace_for_bot(bot_id)
        env = self._worker_env(bot, workspace)

        existing = self.workers.get(bot_id)
        if existing is not None:
            proc = existing.get("proc")
            if isinstance(proc, subprocess.Popen):
                code = proc.poll()
                if code is None:
                    return
                tail = self._worker_log_tail(workspace, max_lines=6)
                if tail:
                    self._log(
                        "worker exited bot_id="
                        f"{bot_id} code={code}; restarting; worker_log_tail={tail[:1200]}"
                    )
                else:
                    self._log(f"worker exited bot_id={bot_id} code={code}; restarting")

        cmd = [self.python_bin, str(self.root / "daemon_service.py")]
        try:
            popen_kwargs: dict[str, Any] = _popen_windows_hidden_kwargs(
                new_process_group=True,
                detached=False,
            )
            proc = subprocess.Popen(
                cmd,
                cwd=str(self.root),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                **popen_kwargs,
            )
        except Exception as exc:
            self._log(f"ERROR spawn worker failed bot_id={bot_id}: {exc}")
            return

        self.workers[bot_id] = {
            "proc": proc,
            "workspace": str(workspace),
            "spawned_at": time.time(),
        }
        self._log(f"worker started bot_id={bot_id} pid={proc.pid}")

    def _stop_worker(self, bot_id: str, reason: str) -> None:
        row = self.workers.pop(bot_id, None)
        if row is None:
            return
        proc = row.get("proc")
        if not isinstance(proc, subprocess.Popen):
            return

        self._log(f"stopping worker bot_id={bot_id} reason={reason}")
        try:
            proc.terminate()
        except Exception:
            pass

        deadline = time.time() + 8.0
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            time.sleep(0.2)
        if proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass

    def _cleanup_logs(self) -> None:
        cutoff = datetime.now().date() - timedelta(days=self.log_retention_days - 1)
        for p in self.logs_dir.glob("*.log"):
            date_text = _extract_date_from_name(p.stem)
            if not date_text:
                continue
            try:
                d = datetime.strptime(date_text, "%Y-%m-%d").date()
            except ValueError:
                continue
            if d < cutoff:
                _safe_unlink(p)

    def _log(self, message: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [manager] {message}\n"
        path = self.logs_dir / f"{DAEMON_LOG_PREFIX}-{datetime.now().strftime('%Y-%m-%d')}.log"
        _append_text(path, line)


# ---------- utilities ----------


def _env_bool(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "") or "").strip().lower()
    if not raw:
        return bool(default)
    return raw in {"1", "true", "yes", "on"}


def _env_int_with_legacy(primary: str, legacy: str, default: int, minimum: int = 1) -> int:
    raw = str(os.getenv(primary, "") or "").strip()
    if not raw:
        raw = str(os.getenv(legacy, "") or "").strip()
    if not raw:
        return max(minimum, default)
    try:
        return max(minimum, int(raw))
    except ValueError:
        return max(minimum, default)


def _resolve_env_path(root: Path, env_name: str, default_path: Path) -> Path:
    raw = str(os.getenv(env_name, "") or "").strip()
    if not raw:
        return default_path.resolve()
    p = Path(raw)
    if not p.is_absolute():
        p = (root / p).resolve()
    return p


def _which(cmd: str) -> str | None:
    exts: list[str] = [""]
    if os.name == "nt":
        raw_exts = str(os.getenv("PATHEXT", ".EXE;.CMD;.BAT;.COM") or "")
        parsed = [v.strip() for v in raw_exts.split(";") if v.strip()]
        if parsed:
            exts.extend(parsed)

    for p in os.getenv("PATH", "").split(os.pathsep):
        base = Path(p) / cmd
        for ext in exts:
            candidate = base if not ext else Path(str(base) + ext)
            if candidate.exists() and os.access(candidate, os.X_OK):
                return str(candidate)
    return None


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def _secure_file(path: Path) -> None:
    try:
        path.chmod(SECURE_FILE_MODE)
    except OSError:
        pass


def _secure_dir(path: Path) -> None:
    try:
        path.chmod(SECURE_DIR_MODE)
    except OSError:
        pass


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _secure_dir(path.parent)
    path.write_text(str(text), encoding="utf-8")
    _secure_file(path)


def _append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _secure_dir(path.parent)
    with path.open("a", encoding="utf-8") as f:
        f.write(text)
    _secure_file(path)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _secure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    _secure_file(path)


def _extract_date_from_name(name: str) -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    if not m:
        return ""
    return m.group(1)


def _extract_root_toml_string(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    pattern = re.compile(rf'^\s*{re.escape(key)}\s*=\s*"([^"]*)"\s*$')
    in_root = True
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_root:
                in_root = False
            continue
        if not in_root:
            continue
        m = pattern.match(raw)
        if m:
            return m.group(1).strip()
    return ""


def _compact_cmd(parts: list[str]) -> str:
    return " ".join(shlex.quote(v) for v in parts)


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    if max_len < 4:
        return text[:max_len]
    return text[: max_len - 3] + "..."


def _compact_space(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _strip_ansi_codes(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", str(text or ""))


def _split_text_chunks(text: str, max_len: int = 3500) -> list[str]:
    src = str(text or "").strip()
    if not src:
        return []
    limit = max(256, int(max_len))
    chunks: list[str] = []
    while src:
        if len(src) <= limit:
            chunks.append(src)
            break
        cut = src.rfind("\n", 0, limit + 1)
        if cut < int(limit * 0.5):
            cut = src.rfind(" ", 0, limit + 1)
        if cut < int(limit * 0.5):
            cut = limit
        chunk = src[:cut].strip()
        if not chunk:
            chunk = src[:limit]
            cut = limit
        chunks.append(chunk)
        src = src[cut:].lstrip()
    return chunks


def _parse_local_ts(text: str) -> datetime | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _extract_limit_from_text(text: str, default: int = 20) -> int:
    nums = re.findall(r"\d+", text or "")
    if not nums:
        return default
    try:
        return max(1, min(100, int(nums[0])))
    except Exception:
        return default


def _new_session_key() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:12]
    return f"{ts}_{uid}"


def _new_queue_id() -> str:
    return uuid.uuid4().hex


def _esc(value: str) -> str:
    text = str(value or "")
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


# ---------- entrypoint ----------


def main() -> int:
    if os.getenv("DAEMON_BOT_WORKER", "0").strip() == "1":
        return ClaudeDaemonService().run()

    raw = os.getenv("SONOLBOT_MULTI_BOT_MANAGER", "").strip().lower()
    if raw:
        enabled = raw in {"1", "true", "yes", "on"}
    else:
        enabled = DEFAULT_MULTI_BOT_MANAGER_ENABLED

    if enabled:
        return MultiBotManager().run()
    return ClaudeDaemonService().run()


if __name__ == "__main__":
    raise SystemExit(main())
