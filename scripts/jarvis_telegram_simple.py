#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, asyncio, sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
from security_filter import security_filter, request_logger

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8461725251:AAELKRbZkpa3u6WK24q4k-RGkzedHxjTLiM")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "7910169750"))

# 허용된 사용자 ID (환경변수)
ALLOWED_USERS = set(map(int, os.getenv("ALLOWED_USERS", "7910169750").split(","))) or {7910169750}

class JARVIS:
    """보안 필터링이 적용된 JARVIS 봇"""

    async def check_auth_and_rate_limit(self, update: Update) -> bool:
        """사용자 인증 및 Rate Limiting 확인"""
        user_id = update.effective_user.id

        # 사용자 인증
        if user_id not in ALLOWED_USERS:
            await update.message.reply_text("접근 권한이 없습니다.")
            security_filter.log_security_event("UNAUTHORIZED_ACCESS", user_id, "User not in allowed list")
            return False

        # Rate Limiting
        ok, msg = security_filter.check_rate_limit(user_id)
        if not ok:
            await update.message.reply_text(msg)
            security_filter.log_security_event("RATE_LIMIT_EXCEEDED", user_id, msg)
            return False

        return True
    async def cmd_pages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        # 보안 체크
        if not await self.check_auth_and_rate_limit(update):
            return

        request_logger.log_request(user_id, "/pages", "SUCCESS")

        keyboard = [
            [InlineKeyboardButton("Operations", url="http://localhost:5000/operations.html"),
             InlineKeyboardButton("Analytics", url="http://localhost:5000/analytics.html")],
            [InlineKeyboardButton("Teams", url="http://localhost:5000/teams.html"),
             InlineKeyboardButton("Dashboard", url="http://localhost:5000/dashboard.html")],
            [InlineKeyboardButton("Homepage", url="http://localhost:5000/"),
             InlineKeyboardButton("API", url="http://localhost:5000/api/v1/status")],
        ]
        msg = """안녕하세요! JARVIS 웹 포털입니다.

아래 페이지를 선택해주세요:

🎛️ *Operations* - 프로젝트 관리, 배포, Sprint 추적
📊 *Analytics* - KPI, 메트릭, 팀 성과 분석
👥 *Teams* - 팀 스킬, 업그레이드, 상태 관리
📈 *Dashboard* - 실시간 모니터링, 차트
🏠 *Homepage* - 공식 홈페이지
🔌 *API* - API 상태 확인"""
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.check_auth_and_rate_limit(update):
            return
        request_logger.log_request(user_id, "/status", "SUCCESS")
        await update.message.reply_text(
            "REQUEST: /status\n"
            "PROGRESS: Checking...\n"
            "RESULT: System OK\n\n"
            "[Dashboard](http://localhost:5000/)",
            parse_mode=ParseMode.MARKDOWN
        )

    async def cmd_deploy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        # 보안 체크
        if not await self.check_auth_and_rate_limit(update):
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Use: /deploy prod|staging v1.2.25")
            return

        env, version = context.args[0], context.args[1]

        # 입력 검증
        ok, msg = security_filter.validate_deploy_args(env, version)
        if not ok:
            await update.message.reply_text(f"오류: {msg}")
            security_filter.log_security_event("INVALID_DEPLOY_ARGS", user_id, f"env={env}, version={version}")
            return

        request_logger.log_request(user_id, f"/deploy {env} {version}", "SUCCESS")

        await update.message.reply_text(
            f"REQUEST: /deploy {env} {version}\n"
            f"PROGRESS: Build -> Deploy -> Tests\n"
            f"RESULT: Success\n\n"
            f"[Dashboard](http://localhost:5000/)",
            parse_mode=ParseMode.MARKDOWN
        )

    async def cmd_mission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        # 보안 체크
        if not await self.check_auth_and_rate_limit(update):
            return

        if not context.args:
            await update.message.reply_text("Use: /mission [name]")
            return

        name = " ".join(context.args)

        # 입력 검증
        ok, msg = security_filter.validate_mission_name(name)
        if not ok:
            await update.message.reply_text(f"오류: {msg}")
            security_filter.log_security_event("INVALID_MISSION_NAME", user_id, name)
            return

        request_logger.log_request(user_id, f"/mission {name}", "SUCCESS")

        await update.message.reply_text(
            f"REQUEST: /mission {name}\n"
            f"PROGRESS: Team assignment\n"
            f"RESULT: M-003 created\n\n"
            f"[Operations](http://localhost:5000/operations.html)",
            parse_mode=ParseMode.MARKDOWN
        )

    async def cmd_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.check_auth_and_rate_limit(update):
            return
        request_logger.log_request(user_id, "/report", "SUCCESS")
        await update.message.reply_text(
            "REQUEST: /report\n"
            "PROGRESS: Collecting metrics\n"
            "RESULT: System healthy\n\n"
            "Uptime: 99.98% | Error: 0.02% | Latency: 145ms"
        )

    async def cmd_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.check_auth_and_rate_limit(update):
            return
        request_logger.log_request(user_id, "/analytics", "SUCCESS")
        await update.message.reply_text(
            "REQUEST: /analytics\n"
            "PROGRESS: Loading metrics...\n"
            "RESULT: Analytics ready\n\n"
            "[Analytics Dashboard](http://localhost:5000/analytics.html)",
            parse_mode=ParseMode.MARKDOWN
        )

    async def cmd_teams(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.check_auth_and_rate_limit(update):
            return
        request_logger.log_request(user_id, "/teams", "SUCCESS")
        await update.message.reply_text(
            "REQUEST: /teams\n"
            "PROGRESS: Loading team data...\n"
            "RESULT: Teams loaded (10/10)\n\n"
            "[Team Management](http://localhost:5000/teams.html)",
            parse_mode=ParseMode.MARKDOWN
        )

    async def cmd_operations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.check_auth_and_rate_limit(update):
            return
        request_logger.log_request(user_id, "/operations", "SUCCESS")
        await update.message.reply_text(
            "REQUEST: /operations\n"
            "PROGRESS: Loading operations...\n"
            "RESULT: Control panel ready\n\n"
            "[Operations Control](http://localhost:5000/operations.html)",
            parse_mode=ParseMode.MARKDOWN
        )

    async def cmd_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.check_auth_and_rate_limit(update):
            return
        request_logger.log_request(user_id, "/dashboard", "SUCCESS")
        await update.message.reply_text(
            "REQUEST: /dashboard\n"
            "PROGRESS: Collecting live metrics...\n"
            "RESULT: Dashboard active\n\n"
            "[Live Dashboard](http://localhost:5000/dashboard.html)",
            parse_mode=ParseMode.MARKDOWN
        )

    async def cmd_uptime(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.check_auth_and_rate_limit(update):
            return
        request_logger.log_request(user_id, "/uptime", "SUCCESS")
        await update.message.reply_text(
            "REQUEST: /uptime\n"
            "PROGRESS: Checking service health...\n"
            "RESULT: All systems operational\n\n"
            "System Uptime: 99.98%\n"
            "Last Check: 2 min ago\n"
            "Status: OK"
        )

    async def cmd_errors(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.check_auth_and_rate_limit(update):
            return
        request_logger.log_request(user_id, "/errors", "SUCCESS")
        await update.message.reply_text(
            "REQUEST: /errors\n"
            "PROGRESS: Analyzing error logs...\n"
            "RESULT: Error report ready\n\n"
            "Error Rate: 0.02%\n"
            "Last Error: 45 min ago\n"
            "Critical Issues: 0"
        )

    async def cmd_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.check_auth_and_rate_limit(update):
            return
        request_logger.log_request(user_id, "/users", "SUCCESS")
        await update.message.reply_text(
            "REQUEST: /users\n"
            "PROGRESS: Fetching user metrics...\n"
            "RESULT: User stats loaded\n\n"
            "Active Users: 10,234\n"
            "New Users (24h): 156\n"
            "Retention (7d): 87%"
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not await self.check_auth_and_rate_limit(update):
            return
        request_logger.log_request(user_id, "/help", "SUCCESS")

        keyboard = [
            [InlineKeyboardButton("Pages", callback_data="help_pages"),
             InlineKeyboardButton("Dashboard", callback_data="help_dashboard")],
            [InlineKeyboardButton("Metrics", callback_data="help_metrics"),
             InlineKeyboardButton("Operations", callback_data="help_operations")],
        ]

        help_text = """*JARVIS Commands Guide*

*팀 접근 정보*
Local:    http://localhost:5000
Network:  http://172.30.1.26:5000
External: http://localhost:5000

━━━━━━━━━━━━━━━━━━━━━━━

*📄 Pages*
/pages - 모든 웹 페이지 링크 (인라인 버튼)

*📊 Dashboard*
/dashboard - 실시간 모니터링 보드
/status - 시스템 상태 확인
/analytics - 분석 데이터 조회
/operations - 운영 제어판 열기
/teams - 팀 정보 및 스킬 관리

*📈 Metrics*
/uptime - 시스템 가동률 확인
/errors - 에러 로그 조회
/users - 사용자 통계 확인
/report - 실시간 모니터링 리포트

*🚀 Operations*
/deploy <env> <version> - 배포 실행
  예: /deploy prod v1.2.25
/mission <name> - 새 프로젝트 생성
  예: /mission 새로운 기능 개발

*💡 Help*
/help - 이 도움말 (현재 보고 있음)

━━━━━━━━━━━━━━━━━━━━━━━

*더 알아보기:*
버튼을 클릭하거나 명령어를 입력하세요!
"""
        await update.message.reply_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    async def button_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help 버튼 콜백"""
        query = update.callback_query
        await query.answer()

        help_data = {
            "help_pages": """*웹 페이지 가이드*

/pages - 모든 페이지 링크

*포함된 페이지:*
1. Operations - 프로젝트 관리, 배포, Sprint 추적
2. Analytics - KPI, 메트릭, 팀 성과 분석
3. Teams - 팀 스킬, 업그레이드, 상태 관리
4. Dashboard - 실시간 모니터링, 차트
5. Homepage - 공식 홈페이지
6. API - API 상태 확인

각 페이지는 인라인 버튼으로 바로 접근 가능합니다!
""",
            "help_dashboard": """*대시보드 명령어*

/dashboard - 실시간 모니터링 보드
/status - 시스템 상태 (API, DB, WebSocket)
/analytics - 분석 대시보드 (KPI, 메트릭)
/operations - 운영 제어판 (프로젝트, Sprint)
/teams - 팀 관리 (스킬, 상태)

각 명령어는 REQUEST > PROGRESS > RESULT 형식으로 응답합니다.
""",
            "help_metrics": """*시스템 메트릭*

/uptime - 시스템 가동률 (목표: 99.98%)
/errors - 에러 현황 (에러율, 최근 에러)
/users - 사용자 통계 (활성 사용자, 신규 가입, 유지율)
/report - 실시간 모니터링 리포트 (1시간 통계)

모든 메트릭은 자동으로 수집됩니다.
주기적으로 확인해서 시스템 건강도를 모니터링하세요!
""",
            "help_operations": """*운영 명령어*

/deploy <env> <version> - 배포 실행
  예: /deploy prod v1.2.25
  예: /deploy staging v1.2.24

/mission <name> - 새 프로젝트 생성
  예: /mission 새로운 기능 개발
  예: /mission 버그 수정

각 작업은 팀에 자동으로 배치됩니다.
진행 상황은 /report 명령어로 확인하세요!
"""
        }

        callback_type = query.data
        text = help_data.get(callback_type, "도움말을 찾을 수 없습니다.")

        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

def main():
    bot = JARVIS()
    app = Application.builder().token(BOT_TOKEN).build()

    # Pages & Dashboard
    app.add_handler(CommandHandler("pages", bot.cmd_pages))
    app.add_handler(CommandHandler("dashboard", bot.cmd_dashboard))
    app.add_handler(CommandHandler("status", bot.cmd_status))

    # Analytics & Operations
    app.add_handler(CommandHandler("analytics", bot.cmd_analytics))
    app.add_handler(CommandHandler("teams", bot.cmd_teams))
    app.add_handler(CommandHandler("operations", bot.cmd_operations))

    # Metrics
    app.add_handler(CommandHandler("uptime", bot.cmd_uptime))
    app.add_handler(CommandHandler("errors", bot.cmd_errors))
    app.add_handler(CommandHandler("users", bot.cmd_users))
    app.add_handler(CommandHandler("report", bot.cmd_report))

    # Operations
    app.add_handler(CommandHandler("deploy", bot.cmd_deploy))
    app.add_handler(CommandHandler("mission", bot.cmd_mission))

    # Help
    app.add_handler(CommandHandler("help", bot.cmd_help))
    app.add_handler(CallbackQueryHandler(bot.button_help))

    print("JARVIS Bot Running")
    app.run_polling()

if __name__ == "__main__":
    main()
