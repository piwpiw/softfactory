import pytest
from pathlib import Path

pytestmark = pytest.mark.e2e


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_root_console_has_key_entry_points():
    html = read("d:/Project/web/index.html")
    assert "SoftFactory 운영 콘솔" in html
    assert "사용자 대시보드" in html
    assert "관리자 대시보드" in html
    assert "Bohemian Marketing AI" in html
    assert "카드뉴스 자동화" in html
    assert "자동화 고도화 대시보드" in html
    assert "Growth Automation Hub" in html
    assert "데이터 분석" in html
    assert "CI/CD 운영" in html
    assert "팀 관리" in html
    assert "운영 제어" in html
    assert "리포트 센터" in html


def test_operational_pages_have_clean_titles_and_sections():
    analytics = read("d:/Project/web/analytics.html")
    cicd = read("d:/Project/web/ci-cd.html")
    teams = read("d:/Project/web/teams.html")
    operations = read("d:/Project/web/operations.html")
    reports = read("d:/Project/web/reports.html")
    automation = read("d:/Project/web/automation-dashboard.html")

    assert "데이터 분석" in analytics
    assert "부서별 생산성 추세" in analytics
    assert "CI/CD 운영" in cicd
    assert "최근 실행 히스토리" in cicd
    assert "팀 관리" in teams
    assert "팀 상태 테이블" in teams
    assert "운영 제어" in operations
    assert "운영 미션" in operations
    assert "리포트 센터" in reports
    assert "보고서 목록" in reports
    assert "자동화 고도화 대시보드" in automation
    assert "자동화 사이클" in automation
