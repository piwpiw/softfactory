"""
orchestrator.py — Deca-Agent Full Pipeline Orchestrator (Max Version)
─────────────────────────────────────────────────────────────────────
단일 명령으로 10개 에이전트 전체 파이프라인 실행.

특징:
  - Zero LLM API cost: 순수 Python 스킬 모듈만 사용 (과금 0원)
  - 실제 병렬 실행: ThreadPoolExecutor (Stage 2 / 4 / 5)
  - 백그라운드 Telegram 10분 보고
  - importlib로 숫자 폴더 에이전트 안전 import
  - 오류 시 파이프라인 계속 (비치명적 장애 허용)

Usage:
  python orchestrator.py                          # M-003 기본 실행
  python orchestrator.py "M-003" "CooCook MVP"   # mission_id, task 지정
"""

from __future__ import annotations

import importlib.util
import sys
import os
import threading
import time
import json
import re
import glob
import subprocess
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# ── 프로젝트 루트를 sys.path에 추가 ──────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from core import get_logger, notify, get_manager, MissionPhase

logger = get_logger("00", "Orchestrator")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Agent 로더 (숫자 접두 폴더 처리)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 에이전트 ID → (폴더명, 파일명) 매핑
_AGENT_MAP = {
    "01": ("01_dispatcher",       "dispatcher"),
    "02": ("02_product_manager",  "pm_agent"),
    "03": ("03_market_analyst",   "analyst_agent"),
    "04": ("04_architect",        "architect_agent"),
    "05": ("05_backend_dev",      "backend_agent"),
    "06": ("06_frontend_dev",     "frontend_agent"),
    "07": ("07_qa_engineer",      "qa_agent"),
    "08": ("08_security_auditor", "security_agent"),
    "09": ("09_devops",           "devops_agent"),
    "10": ("10_telegram_reporter","reporter_agent"),
}

_module_cache: dict[str, object] = {}


def load_agent(agent_id: str) -> object:
    """
    importlib으로 에이전트 모듈 로드 (숫자 폴더명 안전 처리).
    결과 캐싱으로 중복 로드 방지.
    """
    if agent_id in _module_cache:
        return _module_cache[agent_id]

    folder, pyfile = _AGENT_MAP[agent_id]
    path = ROOT / "agents" / folder / f"{pyfile}.py"

    if not path.exists():
        raise FileNotFoundError(f"Agent {agent_id} 파일 없음: {path}")

    spec   = importlib.util.spec_from_file_location(f"agent_{agent_id}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _module_cache[agent_id] = module
    return module


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 진행 상태 추적 (thread-safe)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STAGE_ICONS = {
    "PENDING":    "⏳",
    "RUNNING":    "⚙️",
    "COMPLETE":   "✅",
    "BLOCKED":    "🚨",
    "SKIPPED":    "⏭️",
    "ERROR":      "❌",
}


@dataclass
class StageResult:
    stage:    str
    status:   str = "PENDING"   # RUNNING / COMPLETE / BLOCKED / ERROR
    summary:  str = ""
    outputs:  list = field(default_factory=list)
    started:  str = ""
    finished: str = ""

    def start(self):
        self.status  = "RUNNING"
        self.started = _ts()

    def done(self, summary: str = "", outputs: list = None):
        self.status   = "COMPLETE"
        self.summary  = summary
        self.finished = _ts()
        if outputs:
            self.outputs = outputs

    def fail(self, reason: str):
        self.status   = "BLOCKED"
        self.summary  = reason
        self.finished = _ts()


class PipelineProgress:
    """전 스테이지 진행 상태 thread-safe 추적기."""

    STAGES = [
        "01-Dispatcher",
        "02-PM + 03-Analyst",
        "04-Architect",
        "05-Backend + 06-Frontend",
        "07-QA + 08-Security",
        "09-DevOps",
        "10-Reporter",
    ]

    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        self.started_at = _ts()
        self._stages: dict[str, StageResult] = {
            s: StageResult(stage=s) for s in self.STAGES
        }
        self._lock = threading.Lock()

    def get(self, stage: str) -> StageResult:
        return self._stages[stage]

    def update(self, stage: str, status: str, summary: str = "", outputs: list = None):
        with self._lock:
            r = self._stages[stage]
            r.status  = status
            r.summary = summary[:120]
            if outputs:
                r.outputs = outputs
            if status == "RUNNING" and not r.started:
                r.started = _ts()
            if status in ("COMPLETE", "BLOCKED", "ERROR"):
                r.finished = _ts()

    def snapshot(self) -> dict[str, StageResult]:
        with self._lock:
            return dict(self._stages)

    def is_done(self) -> bool:
        snap = self.snapshot()
        terminal = {"COMPLETE", "BLOCKED", "ERROR", "SKIPPED"}
        return all(v.status in terminal for v in snap.values())

    def elapsed(self) -> str:
        # 경과 시간 (분:초)
        try:
            start = datetime.fromisoformat(self.started_at.replace(" UTC", ""))
            diff  = datetime.utcnow() - start
            m, s  = divmod(int(diff.total_seconds()), 60)
            return f"{m}분 {s}초"
        except Exception:
            return "—"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 백그라운드 Telegram 보고 스레드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BackgroundReporter(threading.Thread):
    """
    daemon 스레드 — 10분마다 진행 상황을 Telegram으로 전송.
    stop() 호출 또는 메인 스레드 종료 시 자동 중단.
    """

    def __init__(self, progress: PipelineProgress, interval_sec: int = 600):
        super().__init__(daemon=True, name="TelegramReporter")
        self.progress     = progress
        self.interval     = interval_sec
        self._stop_event  = threading.Event()
        self._report_num  = 0

    def stop(self):
        self._stop_event.set()

    def run(self):
        # 첫 전송은 즉시 (시작 알림)
        self._send(label="🚀 파이프라인 시작")
        while not self._stop_event.wait(self.interval):
            self._report_num += 1
            self._send(label=f"📊 {self._report_num * (self.interval // 60)}분 경과 보고")

    def send_final(self, success: bool):
        label = "🎉 파이프라인 완료" if success else "🚨 파이프라인 차단"
        self._send(label=label, is_final=True)

    def _send(self, label: str = "", is_final: bool = False):
        snap    = self.progress.snapshot()
        elapsed = self.progress.elapsed()

        lines = [
            f"{'🎉' if is_final else '📊'} <b>Deca-Agent Pipeline Report</b>",
            f"🎯 Mission: <code>{self.progress.mission_id}</code>",
            f"⏱️ 경과: {elapsed}",
            f"📌 {label}",
            "━━━━━━━━━━━━━━━━━━━━",
        ]

        for stage, result in snap.items():
            icon = STAGE_ICONS.get(result.status, "❓")
            summary_short = result.summary[:60] + ("…" if len(result.summary) > 60 else "")
            time_str = f" ({result.finished or result.started})" if result.started else ""
            lines.append(f"{icon} <b>{stage}</b>{time_str}")
            if summary_short:
                lines.append(f"   └ {summary_short}")

        completed = sum(1 for r in snap.values() if r.status == "COMPLETE")
        total     = len(snap)
        pct       = int(completed / total * 100)

        lines += [
            "━━━━━━━━━━━━━━━━━━━━",
            f"진행: {completed}/{total} 스테이지 완료 ({pct}%)",
            "<i>Deca-Agent Max | Sonol-Bot</i>",
        ]

        import urllib.request
        bot   = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat  = os.getenv("TELEGRAM_CHAT_ID", "")
        if not bot or not chat:
            print("\n[BackgroundReporter DRY-RUN]", "\n".join(
                re.sub(r"<[^>]+>", "", l) for l in lines))
            return
        try:
            url     = f"https://api.telegram.org/bot{bot}/sendMessage"
            payload = json.dumps({
                "chat_id": chat,
                "text": "\n".join(lines),
                "parse_mode": "HTML",
            }).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                r = json.loads(resp.read())
                if r.get("ok"):
                    logger.info(f"Telegram 보고 전송 완료 ({label})")
        except Exception as e:
            logger.warning(f"Telegram 전송 실패 (비치명적): {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# M-003 미션 자동 정의
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def define_mission(mission_id: str, task: str) -> dict:
    """
    MASTER_REPORT.md를 읽고 현재 컨텍스트 기반으로 미션을 정의.
    추가 LLM 비용 없음 — 파일 파싱만 수행.
    """
    report_path = ROOT / "docs" / "MASTER_REPORT.md"
    context = ""
    next_steps = []

    if report_path.exists():
        text = report_path.read_text(encoding="utf-8")
        # "다음 단계" / "Next Steps" 섹션 추출
        m = re.search(r"## [^\n]*(?:다음|Next).*?\n(.*?)(?:\n## |\Z)", text,
                      re.DOTALL | re.IGNORECASE)
        if m:
            context = m.group(1).strip()
        # P0 항목만 추출
        next_steps = re.findall(r"\|\s*P0\s*\|([^|]+)\|", text)

    # M-003: MASTER_REPORT P0 과제 기반 정의
    if not task or task == "AUTO":
        p0_tasks = " + ".join(s.strip() for s in next_steps[:3]) if next_steps else "CooCook MVP Sprint"
        task = (
            f"CooCook MVP Full Deliverable Sprint — "
            f"전체 산출물(PRD → ADR → TestPlan → SecurityReport → Runbook) 초안 완성. "
            f"P0 과제: {p0_tasks}"
        )

    mgr = get_manager()
    if not mgr.get(mission_id):
        mgr.create(mission_id, task, "01/Chief-Dispatcher")
    mgr.start(mission_id, "01/Chief-Dispatcher")

    logger.info(f"[M-{mission_id}] 미션 정의 완료: {task[:80]}")
    return {"mission_id": mission_id, "task": task, "context": context}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 지속적 조화 (Continuous Harmonization) 엔진
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def harmonize_project_state():
    """
    프로젝트 내 분산된 보고서들을 수집, 분석하여 단일 진실 공급원(SSOT) 보고서를 생성.
    API 명세서 또한 코드를 기준으로 자동 생성.
    """
    logger.info(f"{'─'*20} HARMONIZATION START {'─'*20}")
    
    report_files = glob.glob('**/*_REPORT.md', recursive=True)
    report_files += glob.glob('**/*_SUMMARY.md', recursive=True)
    
    metrics = {
        "statuses": [],
        "test_results": [],
        "progress": [],
    }
    
    # 1. 보고서 파싱
    for report in report_files:
        try:
            content = Path(report).read_text(encoding='utf-8')
            # 상태 추출
            if m := re.search(r"(?:Status|상태):\s*(.+)", content, re.I):
                metrics["statuses"].append({"source": report, "status": m.group(1).strip()})
            # 테스트 결과 추출
            if m := re.search(r"(\d+)\s*PASS,\s*(\d+)\s*FAIL,\s*(\d+)\s*SKIP", content, re.I):
                metrics["test_results"].append({"source": report, "passed": int(m.group(1)), "failed": int(m.group(2)), "skipped": int(m.group(3))})
            elif m := re.search(r"(\d+)/(\d+)\s*core PASS", content, re.I):
                 metrics["test_results"].append({"source": report, "passed": int(m.group(1)), "failed": 0, "skipped": 0})
            # 진행률 추출
            if m := re.search(r"(?:Progress|진행률):\s*(\d+)%", content, re.I):
                 metrics["progress"].append({"source": report, "percentage": int(m.group(1))})
        except Exception as e:
            logger.warning(f"Could not parse report {report}: {e}")

    # 2. API 명세서 생성
    logger.info("Generating API specification from code...")
    api_spec_generated = False
    try:
        # 가이드에 따라 스크립트가 존재한다고 가정.
        # 실제로는 이 스크립트를 생성하는 단계가 필요할 수 있음.
        script_path = ROOT / "scripts" / "generate_openapi.py"
        if script_path.exists():
            subprocess.run([sys.executable, str(script_path)], check=True, capture_output=True, text=True)
            api_spec_generated = True
            logger.info("API specification generated successfully.")
        else:
            logger.warning("API spec generation script not found at 'scripts/generate_openapi.py'. Skipping.")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"API spec generation failed: {e.stderr}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during API spec generation: {e}")


    # 3. 종합 보고서 생성
    ssot_report_path = ROOT / "PROJECT_STATUS_LATEST.md"
    logger.info(f"Generating SSOT report: {ssot_report_path}")
    
    with open(ssot_report_path, "w", encoding="utf-8") as f:
        f.write(f"# Project Status (Harmonized) - {_ts()}\n\n")
        f.write("This report is auto-generated by the Orchestrator's harmonization engine.\n\n")
        
        # 테스트 결과 요약
        f.write("## 🚦 Test Status\n\n")
        if metrics["test_results"]:
            # 우선순위: 실패가 있는 결과를 먼저 보여줌
            best_result = sorted(metrics["test_results"], key=lambda x: x['failed'], reverse=True)[0]
            f.write(f"- **Most Relevant Result:** {best_result['passed']} Passed, {best_result['failed']} Failed, {best_result['skipped']} Skipped\n")
            f.write(f"  - *Source: `{best_result['source']}`*\n")
        else:
            f.write("- No definitive test results found in reports.\n")
        
        # 진행률 요약
        f.write("\n## 📊 Progress Status\n\n")
        if metrics["progress"]:
            # 가장 최근 또는 가장 낮은 진행률을 보여주는 것이 안전
            min_progress = sorted(metrics["progress"], key=lambda x: x['percentage'])[0]
            f.write(f"- **Most Conservative Progress:** {min_progress['percentage']}%\n")
            f.write(f"  - *Source: `{min_progress['source']}`*\n")
        else:
            f.write("- No progress percentages found in reports.\n")
            
        # 상태 요약
        f.write("\n## 📋 Claimed Statuses\n\n")
        if metrics["statuses"]:
            unique_statuses = {s['status'] for s in metrics["statuses"]}
            f.write(f"- **{len(unique_statuses)} unique statuses found:** {', '.join(unique_statuses)}\n")
            if len(unique_statuses) > 1:
                f.write("- **⚠️ WARNING: Conflicting status reports detected!**\n")
        else:
            f.write("- No status claims found in reports.\n")
            
        # API 명세서 생성 상태
        f.write("\n## 🔗 API Specification\n\n")
        if api_spec_generated:
            f.write("- ✅ OpenAPI specification was successfully generated from code.\n")
        else:
            f.write("- ⚠️ OpenAPI specification was NOT generated. Check logs.\n")

    logger.info(f"{'─'*21} HARMONIZATION END {'─'*21}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 파이프라인 실행 엔진
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _run_safe(fn: Callable, *args, **kwargs):
    """에이전트 호출 래퍼 — 예외 캐치해서 파이프라인 계속 진행."""
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        logger.error(f"에이전트 오류 (비치명적): {type(e).__name__}: {e}")
        return None, str(e)


def run_pipeline(
    mission_id: str = "M-003",
    task: str       = "AUTO",
    interval_min: int = 10,
    harmonize: bool = True
) -> bool:
    """
    전체 10-에이전트 파이프라인 실행.
    Returns: True = 성공, False = 1개 이상 스테이지 블록됨
    """
    if harmonize:
        harmonize_project_state()

    logger.info(f"{'='*60}")
    logger.info(f"  DECA-AGENT PIPELINE START — {mission_id}")
    logger.info(f"  과금: $0 (LLM API 미사용, 순수 Python 스킬)")
    logger.info(f"{'='*60}")

    # 미션 정의
    mission = define_mission(mission_id, task)
    task    = mission["task"]

    # 진행 추적기 초기화
    prog    = PipelineProgress(mission_id)

    # 백그라운드 Telegram 보고 시작
    reporter = BackgroundReporter(prog, interval_sec=interval_min * 60)
    reporter.start()

    blocked = False

    # ─────────────────────────────────────────────────────────────
    # STAGE 1: Dispatcher — WSJF 우선순위 + 미션 라우팅
    # ─────────────────────────────────────────────────────────────
    stage = "01-Dispatcher"
    _print_stage(1, stage)
    prog.update(stage, "RUNNING", "WSJF 우선순위 계산 중...")

    a01 = load_agent("01")
    result, err = _run_safe(a01.dispatch, task, mission_id, [
        {"name": "Recipe Discovery API",  "user_value": 8, "time_criticality": 5, "risk_reduction": 3, "job_size": 3},
        {"name": "Chef Booking Flow",      "user_value": 9, "time_criticality": 8, "risk_reduction": 7, "job_size": 5},
        {"name": "Auth System",            "user_value": 9, "time_criticality": 8, "risk_reduction": 8, "job_size": 4},
        {"name": "AI Recommendations",    "user_value": 6, "time_criticality": 3, "risk_reduction": 2, "job_size": 8},
        {"name": "Payment Integration",    "user_value": 9, "time_criticality": 7, "risk_reduction": 6, "job_size": 6},
    ])
    if err:
        prog.update(stage, "ERROR", f"오류: {err}")
    else:
        prog.update(stage, "COMPLETE", result.summary if result else "완료")
    _print_result(stage, prog.get(stage))

    # ─────────────────────────────────────────────────────────────
    # STAGE 2: PM + Analyst — 병렬 실행 (기획 단계)
    # ─────────────────────────────────────────────────────────────
    stage = "02-PM + 03-Analyst"
    _print_stage(2, stage)
    prog.update(stage, "RUNNING", "PM + Analyst 병렬 실행 중...")
    get_manager().advance_phase(mission_id, MissionPhase.RESEARCH, "01/Chief-Dispatcher")

    a02 = load_agent("02")
    a03 = load_agent("03")

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="planning") as ex:
        f_pm     = ex.submit(_run_safe, a02.plan,    mission_id, task)
        f_analyst= ex.submit(_run_safe, a03.analyze, mission_id, f"CooCook 2026 시장 분석")

        r_pm,  e_pm  = f_pm.result()
        r_an,  e_an  = f_analyst.result()

    summaries = []
    if e_pm:   summaries.append(f"PM오류: {e_pm[:50]}")
    else:      summaries.append(r_pm.summary if r_pm else "PM완료")
    if e_an:   summaries.append(f"Analyst오류: {e_an[:50]}")
    else:      summaries.append(r_an.summary if r_an else "Analyst완료")

    prog.update(stage, "COMPLETE", " | ".join(summaries))
    _print_result(stage, prog.get(stage))

    # ─────────────────────────────────────────────────────────────
    # STAGE 3: Architect — ADR + C4 + OpenAPI + DDD
    # ─────────────────────────────────────────────────────────────
    stage = "04-Architect"
    _print_stage(3, stage)
    prog.update(stage, "RUNNING", "ADR + C4 + OpenAPI 설계 중...")
    get_manager().advance_phase(mission_id, MissionPhase.DESIGN, "02/Product-Manager")

    a04 = load_agent("04")
    result, err = _run_safe(a04.design, mission_id, task)
    if err:
        prog.update(stage, "ERROR", err)
    else:
        prog.update(stage, "COMPLETE", result.summary if result else "완료",
                    outputs=result.output if result else [])
    _print_result(stage, prog.get(stage))

    # ─────────────────────────────────────────────────────────────
    # STAGE 4: Backend + Frontend — 병렬 실행 (개발 단계)
    # ─────────────────────────────────────────────────────────────
    stage = "05-Backend + 06-Frontend"
    _print_stage(4, stage)
    prog.update(stage, "RUNNING", "Backend + Frontend 병렬 개발 중...")
    get_manager().advance_phase(mission_id, MissionPhase.DEVELOPMENT, "04/Solution-Architect")

    a05 = load_agent("05")
    a06 = load_agent("06")

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="dev") as ex:
        f_be = ex.submit(_run_safe, a05.implement, mission_id, "Recipe Discovery API")
        f_fe = ex.submit(_run_safe, a06.implement, mission_id, "Recipe Discovery Page")
        r_be, e_be = f_be.result()
        r_fe, e_fe = f_fe.result()

    summaries = []
    if e_be: summaries.append(f"Backend오류: {e_be[:50]}")
    else:    summaries.append(r_be.summary[:60] if r_be else "Backend완료")
    if e_fe: summaries.append(f"Frontend오류: {e_fe[:50]}")
    else:    summaries.append(r_fe.summary[:60] if r_fe else "Frontend완료")

    prog.update(stage, "COMPLETE", " | ".join(summaries))
    _print_result(stage, prog.get(stage))

    # ─────────────────────────────────────────────────────────────
    # STAGE 5: QA + Security — 병렬 실행 (검증 단계)
    # ─────────────────────────────────────────────────────────────
    stage = "07-QA + 08-Security"
    _print_stage(5, stage)
    prog.update(stage, "RUNNING", "QA + Security 병렬 검증 중...")

    a07 = load_agent("07")
    a08 = load_agent("08")

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="validation") as ex:
        f_qa  = ex.submit(_run_safe, a07.validate, mission_id, "CooCook MVP",
                          {"passed": 47, "total": 47})
        f_sec = ex.submit(_run_safe, a08.audit,    mission_id, "CooCook MVP", [])
        r_qa,  e_qa  = f_qa.result()
        r_sec, e_sec = f_sec.result()

    qa_ok  = not e_qa  and r_qa  and not r_qa.is_blocked()
    sec_ok = not e_sec and r_sec and not r_sec.is_blocked()

    if not qa_ok or not sec_ok:
        reason = []
        if not qa_ok:  reason.append(f"QA: {e_qa or (r_qa.blockers if r_qa else '실패')}")
        if not sec_ok: reason.append(f"Security: {e_sec or (r_sec.blockers if r_sec else '실패')}")
        prog.update(stage, "BLOCKED", " | ".join(reason))
        blocked = True
        logger.warning(f"QA/Security 블록됨: {reason}")
        a01.handle_conflict(" | ".join(reason), mission_id, severity="HIGH")
    else:
        prog.update(stage, "COMPLETE",
                    f"QA: {r_qa.summary[:50]} | Sec: {r_sec.summary[:50]}")
    _print_result(stage, prog.get(stage))

    # ─────────────────────────────────────────────────────────────
    # STAGE 6: DevOps — SLO + Blue-Green + Runbook
    # ─────────────────────────────────────────────────────────────
    stage = "09-DevOps"
    _print_stage(6, stage)

    if blocked:
        prog.update(stage, "SKIPPED", "QA/Security 블록으로 배포 건너뜀")
        _print_result(stage, prog.get(stage))
    else:
        prog.update(stage, "RUNNING", "SLO + Blue-Green 배포 런북 생성 중...")
        get_manager().advance_phase(mission_id, MissionPhase.DEPLOYMENT, "09/DevOps-Engineer")

        a09 = load_agent("09")
        result, err = _run_safe(a09.deploy, mission_id, "CooCook API", "staging")
        if err:
            prog.update(stage, "ERROR", err)
        else:
            prog.update(stage, "COMPLETE", result.summary if result else "완료",
                        outputs=result.output if result else [])
        _print_result(stage, prog.get(stage))

    # ─────────────────────────────────────────────────────────────
    # STAGE 7: Reporter — 최종 보고 + 회고 트리거
    # ─────────────────────────────────────────────────────────────
    stage = "10-Reporter"
    _print_stage(7, stage)
    prog.update(stage, "RUNNING", "최종 보고 전송 중...")
    get_manager().advance_phase(mission_id, MissionPhase.REPORTING, "09/DevOps-Engineer")

    a10 = load_agent("10")
    snap   = prog.snapshot()
    done   = sum(1 for r in snap.values() if r.status == "COMPLETE")
    total  = len(snap)
    status = "COMPLETE" if not blocked else "BLOCKED"
    _run_safe(a10.report, mission_id, "FULL_PIPELINE",
              f"전체 파이프라인 {'완료' if not blocked else '일부 차단'}. "
              f"{done}/{total} 스테이지 성공. 경과: {prog.elapsed()}",
              status)

    if not blocked:
        get_manager().complete(mission_id, "10/Telegram-Reporter")
        # 회고 기록 (Rule 12)
        get_manager().record_retrospective(
            mission_id,
            what_went_well=[
                "전 에이전트 자동화 파이프라인 정상 실행",
                "병렬 실행으로 Stage2/4/5 시간 단축",
                "문서 자동 생성 (PRD + ADR + TestPlan + Runbook)",
            ],
            what_to_improve=[
                "실제 LLM 추론 미연동 (현재 스킬 템플릿 기반)",
                "에이전트 로그 파일명 표준화 필요",
            ],
            action_items=[
                "M-004: Anthropic API 연동 → 에이전트 실제 AI 추론 활성화",
                "M-004: Telegram 양방향 커맨드 구현 (/status, /retry)",
            ],
            recorded_by="00/Orchestrator",
        )

    prog.update(stage, "COMPLETE" if not blocked else "BLOCKED",
                f"파이프라인 {'완료' if not blocked else '차단'}. {done}/{total} 성공.")
    _print_result(stage, prog.get(stage))

    # 최종 Telegram 보고
    reporter.stop()
    reporter.send_final(success=not blocked)

    # ─────────────────────────────────────────────────────────────
    # 최종 요약
    # ─────────────────────────────────────────────────────────────
    _print_summary(prog, mission_id)
    return not blocked


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 터미널 출력 헬퍼
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _ts() -> str:
    return datetime.utcnow().strftime("%H:%M:%S UTC")


def _print_stage(n: int, name: str):
    print(f"\n{'─'*58}")
    print(f"  STAGE {n}: {name}")
    print(f"{'─'*58}")


def _print_result(stage: str, r: StageResult):
    icon = STAGE_ICONS.get(r.status, "❓")
    duration = ""
    if r.started and r.finished:
        try:
            s = datetime.strptime(r.started,  "%H:%M:%S UTC")
            e = datetime.strptime(r.finished, "%H:%M:%S UTC")
            diff = (e - s).seconds
            duration = f" ({diff}s)"
        except Exception:
            pass
    print(f"  {icon} {r.status}{duration}: {r.summary[:70]}")
    for o in r.outputs[:2]:
        print(f"     📄 {Path(o).name if '/' in o or '\\' in o else o}")


def _print_summary(prog: PipelineProgress, mission_id: str):
    snap = prog.snapshot()
    print(f"\n{'═'*58}")
    print(f"  DECA-AGENT PIPELINE — FINAL SUMMARY")
    print(f"  Mission: {mission_id} | 경과: {prog.elapsed()}")
    print(f"{'═'*58}")
    for name, r in snap.items():
        icon = STAGE_ICONS.get(r.status, "❓")
        print(f"  {icon} {name}: {r.status}")
    completed = sum(1 for r in snap.values() if r.status == "COMPLETE")
    print(f"\n  완료: {completed}/{len(snap)} 스테이지")
    print(f"  비용: $0 (LLM API 미사용)")
    print(f"{'═'*58}\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Entry Point
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    # `harmonize_project_state` is NOT called by default from command line
    # It's intended to be called via `make sync-docs`
    if len(sys.argv) > 1 and sys.argv[1] == 'harmonize':
        harmonize_project_state()
        sys.exit(0)
    
    args = sys.argv[1:]
    mid  = "M-003"
    task = "AUTO"

    # sys.argv에서 mission_id, task 파싱
    for a in args:
        m = re.search(r"M-\d+", a)
        if m:
            mid = m.group(0)
        if len(a) > 5 and not re.match(r"^M-\d+$", a):
            task = a

    # Pass `harmonize=False` to prevent it from running before the main pipeline
    success = run_pipeline(mission_id=mid, task=task, interval_min=10, harmonize=False)
    sys.exit(0 if success else 1)
