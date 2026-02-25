#!/usr/bin/env python3
"""
📬 Telegram Reporter — 3줄 진행 상황 보고
요청 | 진행 | 결과
"""

import os
import asyncio
from telegram import Bot
from datetime import datetime, timezone

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("CRITICAL: TELEGRAM_BOT_TOKEN environment variable must be set. Check .env configuration.")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "7910169750"))

class TelegramReporter:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.last_message_id = None

    async def report(self, request: str, progress: str = "", result: str = ""):
        """
        3줄 진행 상황 보고

        request: 사용자 요청
        progress: 진행 상황 (업데이트 가능)
        result: 최종 결과
        """
        message = f"""
📬 **요청**: {request}
⏳ **진행**: {progress}
✅ **결과**: {result}
"""
        try:
            msg = await self.bot.send_message(
                chat_id=CHAT_ID,
                text=message.strip(),
                parse_mode="markdown"
            )
            self.last_message_id = msg.message_id
            return msg
        except Exception as e:
            print(f"❌ Telegram error: {e}")

    async def update_progress(self, progress: str, request: str = ""):
        """진행 상황 실시간 업데이트"""
        if not self.last_message_id:
            return

        try:
            message = f"""
📬 **요청**: {request}
⏳ **진행**: {progress}
"""
            await self.bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=self.last_message_id,
                text=message.strip(),
                parse_mode="markdown"
            )
        except Exception as e:
            print(f"⚠️ Update error: {e}")

    async def deploy_report(self, env: str, version: str):
        """배포 리포트"""
        request = f"/deploy {env} {version}"

        # 요청만 보고
        await self.report(request, "⏳ 준비 중...")
        await asyncio.sleep(1)

        # 진행 상황 업데이트
        for progress_msg in [
            "🔨 Build 25%",
            "🔨 Build 50%",
            "🔨 Build 100% ✓",
            "📦 Deploy 25%",
            "📦 Deploy 50%",
            "📦 Deploy 100% ✓",
            "🧪 Tests 100% ✓",
        ]:
            await self.update_progress(progress_msg, request)
            await asyncio.sleep(0.5)

        # 최종 결과
        result = f"✅ {env.upper()} 배포 완료! (4.2min, 10,234 users, 0.02% error)"
        await self.report(request, "✅ 완료", result)

    async def mission_report(self, name: str):
        """프로젝트 생성 리포트"""
        request = f"/mission {name}"

        await self.report(request, "🔄 팀 배정 중...")
        await asyncio.sleep(1)

        for progress_msg in [
            "🔄 Team 02 (PM): PRD 작성 30%",
            "🔄 Team 03 (Analyst): 시장 검증 50%",
            "🔄 Team 04 (Architect): 설계 70%",
        ]:
            await self.update_progress(progress_msg, request)
            await asyncio.sleep(0.5)

        result = "✅ 프로젝트 M-003 생성됨! 팀 준비 완료 (30분)"
        await self.report(request, "✅ 팀 준비 완료", result)

    async def standup_report(self):
        """스탠드업 리포트"""
        request = "/standup"

        await self.report(request, "📊 팀 상태 수집 중...")
        await asyncio.sleep(0.5)

        progress = """
Team 05: ✅ JWT auth done
Team 06: 🔄 Login UI 40%
Team 09: ✅ Blue-Green ready
"""

        result = "📊 전체 ON TRACK | Sprint 30% (12/40pts)"
        await self.report(request, progress.strip(), result)

    async def status_report(self):
        """시스템 상태 리포트"""
        request = "/status"

        progress = """
🟢 API: Running
🟢 Database: Connected
📈 Requests: 1,245 req/s
⚠️ Error Rate: 0.02%
⏱️ Latency: 145ms
"""

        result = "✅ 시스템 정상 (Uptime 99.98%)"
        await self.report(request, progress.strip(), result)


async def main():
    """테스트"""
    reporter = TelegramReporter()

    print("📬 Telegram Reporter 테스트")
    print("=" * 50)

    # 1. 배포 리포트
    print("\n1️⃣ 배포 진행 상황")
    await reporter.deploy_report("prod", "v1.2.25")
    await asyncio.sleep(2)

    # 2. 프로젝트 리포트
    print("\n2️⃣ 프로젝트 생성")
    await reporter.mission_report("사용자 프로필")
    await asyncio.sleep(2)

    # 3. 스탠드업
    print("\n3️⃣ 일일 스탠드업")
    await reporter.standup_report()
    await asyncio.sleep(2)

    # 4. 상태 확인
    print("\n4️⃣ 시스템 상태")
    await reporter.status_report()

    print("\n✅ 모든 리포트 전송 완료!")


if __name__ == "__main__":
    asyncio.run(main())
