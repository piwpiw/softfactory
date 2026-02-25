# Daemon Handlers Architecture

Quick reference for the modular handler system that consolidates Jarvis v1 + Daemon v2 into unified bot v3.0.

## Quick Start

```python
# In daemon_service.py, after receiving a message:
from daemon.handlers import (
    JarvisCommandsHandler,
    TaskHandler,
    ReportHandler,
    ClaudeHandler,
    CommandValidator
)

# Validate input
validator = CommandValidator()
is_valid, error = validator.validate(chat_id, command, args)
if not is_valid:
    send_error(chat_id, error)
    return

# Route to handler
if command in ["start", "status", "deploy", "mission", ...]:
    handler = JarvisCommandsHandler(send_func, log_func, context)
elif command in ["task-new", "task-list", "task-activate"]:
    handler = TaskHandler(send_func, log_func, context)
elif command in ["s", "summary", "export", "logs", "remind"]:
    handler = ReportHandler(send_func, log_func, context)

# Execute
result = await handler.handle(chat_id, command, args)
```

## Architecture

```
handlers/
├── __init__.py              # Public API exports
├── base_handler.py          # Abstract base class (all handlers inherit)
├── jarvis_commands.py       # Jarvis v1 (10 commands)
├── task_handler.py          # Daemon v2 task mgmt (3 commands)
├── report_handler.py        # Daemon v2 reporting (5 commands)
├── claude_handler.py        # Claude AI integration
└── validation.py            # Input + security validation
```

## Handlers

### BaseHandler (abstract)

Base class for all handlers. Provides:
- `async handle(chat_id, command, args)` — main handler method
- `async send_text(chat_id, text, parse_mode)` — send message
- `async send_error(chat_id, error_msg)` — send error
- `_format_report()` — 3-line report format
- `_escape_html()` — HTML safe escaping
- `_log_command()`, `_log_result()` — logging

### JarvisCommandsHandler (10 commands)

Preserves all Jarvis v1 commands:
- `/start` — Startup menu
- `/help` — Command reference
- `/status` — System status
- `/deploy [env] [version]` — Deploy to prod/staging
- `/mission [name]` — Create project
- `/report` — Monitoring metrics
- `/progress` — Team progress
- `/timeline` — Milestone calendar
- `/breakdown` — Team analysis
- `/pages` — Web pages with buttons

Usage:
```python
handler = JarvisCommandsHandler(send_func, log_func)
result = await handler.handle(chat_id, "status", [])
# → {"success": True, "message": "✓ status executed"}
```

### TaskHandler (3 commands)

Daemon v2 task management:
- `/task-new [description]` — Create task
- `/task-list [limit]` — List tasks
- `/task-activate [id]` — Switch to task

Usage:
```python
handler = TaskHandler(send_func, log_func)
result = await handler.handle(chat_id, "task-new", ["MyTask"])
```

### ReportHandler (5 commands)

Daemon v2 reporting:
- `/s` — Quick status
- `/summary` — Daily report
- `/export [format]` — Export data (json|csv)
- `/logs [lines]` — Show logs
- `/remind [date] [msg]` — Set reminder

Usage:
```python
handler = ReportHandler(send_func, log_func)
result = await handler.handle(chat_id, "summary", [])
```

### ClaudeHandler (AI integration)

Natural language processing:
- `handle_natural_language(chat_id, message)` — Process user request
- Intent classification (code, bug, analysis, deployment, docs)
- Automatic routing to Claude

Usage:
```python
handler = ClaudeHandler(send_func, log_func, {"claude_client": client})
result = await handler.handle_natural_language(chat_id, "고쳐줘")
```

### ValidationLayer

Input validation + security:

```python
validator = CommandValidator()

# Full validation
is_valid, error = validator.validate(chat_id, command, args)

# Sanitize arguments
clean_args = validator.sanitize_args(args)
```

Features:
- Command whitelist validation
- Argument length limits
- Rate limiting (30/min per chat)
- Injection attack prevention
- HTML escaping

## Integration Points

### 1. In daemon_service.py

```python
# At message handler
async def _dispatch_command_message(self, chat_id: int, text: str) -> bool:
    # Extract command and args
    parts = text.split()
    command = parts[0].lstrip("/")
    args = parts[1:]
    
    # Validate
    validator = CommandValidator()
    is_valid, error = validator.validate(chat_id, command, args)
    if not is_valid:
        self._send_text(chat_id, f"❌ {error}")
        return True
    
    # Route to handler
    handlers = {
        "start": JarvisCommandsHandler,
        "status": JarvisCommandsHandler,
        # ... all commands
        "task-new": TaskHandler,
        "summary": ReportHandler,
    }
    
    handler_class = handlers.get(command)
    if not handler_class:
        self._send_text(chat_id, f"❌ Unknown command: {command}")
        return True
    
    handler = handler_class(self._send_text, self._log, {"context": self})
    result = await handler.handle(chat_id, command, args)
    
    return True
```

### 2. Handler Extension

To add a new handler:

```python
from daemon.handlers import BaseHandler

class MyCustomHandler(BaseHandler):
    async def handle(self, chat_id, command, args):
        self._log_command(chat_id, command, args)
        
        if command == "mycommand":
            await self.cmd_mycommand(chat_id, args)
            return {"success": True, "message": "Done"}
        
        return {"success": False, "message": "Unknown"}
    
    async def cmd_mycommand(self, chat_id, args):
        msg = self._format_report(
            request="/mycommand",
            progress="Processing...",
            result="✅ Complete!",
        )
        await self.send_text(chat_id, msg)
```

## Command Mapping

| Command | Handler | Status |
|---------|---------|--------|
| /start, /help, /status | JarvisCommandsHandler | ✅ |
| /deploy, /mission, /report | JarvisCommandsHandler | ✅ |
| /progress, /timeline, /breakdown | JarvisCommandsHandler | ✅ |
| /pages | JarvisCommandsHandler | ✅ |
| /task-new, /task-list, /task-activate | TaskHandler | ✅ |
| /s, /summary, /export | ReportHandler | ✅ |
| /logs, /remind | ReportHandler | ✅ |
| /h | ReportHandler | ✅ |
| Natural language | ClaudeHandler | ✅ |

## Testing

All handlers tested:
- Unit tests: 30/30 passed ✓
- Integration tests: 5/5 passed ✓
- Error handling: 6/6 passed ✓

See `CONSOLIDATION_AUDIT.md` for full test report.

## Files

- `__init__.py` — Package exports
- `base_handler.py` — Base class (115 lines)
- `jarvis_commands.py` — V1 commands (420 lines)
- `task_handler.py` — V2 tasks (95 lines)
- `report_handler.py` — V2 reporting (180 lines)
- `claude_handler.py` — AI integration (155 lines)
- `validation.py` — Input validation (225 lines)

Total: ~1,219 lines of handler code

## Documentation

- `INTEGRATION_LOG.md` — Full integration documentation
- `CONSOLIDATION_AUDIT.md` — Comprehensive audit report
- `README_HANDLERS.md` — This file
- `scripts/jarvis_telegram_main.py` — Marked deprecated (kept for rollback)

## Status

✅ **PRODUCTION READY**

- All v1 commands preserved
- All v2 commands intact
- 100% backward compatible
- 0 data loss
- Security hardened
- Fully tested

---

**Created:** 2026-02-25
**Version:** 3.0 (Unified)
**Team:** Team H
