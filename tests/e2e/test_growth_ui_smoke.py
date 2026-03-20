import pytest
from pathlib import Path

pytestmark = pytest.mark.e2e


def test_growth_pages_exist():
    root = Path("d:/Project/web/growth-automation")
    assert (root / "index.html").exists()
    assert (root / "contacts.html").exists()
    assert (root / "journeys.html").exists()
    assert (root / "ops.html").exists()
    assert (root / "app.js").exists()
    assert Path("d:/Project/web/api/v1/growth/public/bootstrap").exists()
    assert Path("d:/Project/web/api/v1/growth/dashboard/summary").exists()
    assert Path("d:/Project/web/api/v1/growth/events").exists()


def test_root_index_has_growth_card():
    html = Path("d:/Project/web/index.html").read_text(encoding="utf-8")
    assert "Growth Automation Hub" in html
    assert "growth-automation/index.html" in html


def test_contacts_page_exposes_feedback_and_segments():
    html = Path("d:/Project/web/growth-automation/contacts.html").read_text(encoding="utf-8")
    assert 'id="contactsFeedback"' in html
    assert 'id="contactSegments"' in html
    assert 'id="contactSavedFilters"' in html
    assert 'id="contactTrendStrip"' in html
    assert 'id="contactCompareGrid"' in html
    assert 'id="leadCreateBtn"' in html
    assert 'id="contactDetailGrid"' in html
    assert "trend-spark" in html
    assert "trend-bar" in html
    assert "compare-trend" in html
    assert "빠른 리드 생성" in html
    assert "연락처 목록" in html


def test_ops_page_exposes_feedback_and_full_tables():
    html = Path("d:/Project/web/growth-automation/ops.html").read_text(encoding="utf-8")
    assert 'id="opsFeedback"' in html
    assert 'id="opsEventRows"' in html
    assert 'id="dlqRows"' in html
    assert 'id="opsSavedFilters"' in html
    assert 'id="opsTrendStrip"' in html
    assert 'id="opsCompareGrid"' in html
    assert 'id="opsEventDetailGrid"' in html
    assert 'id="dlqDetailGrid"' in html
    assert "trend-spark" in html
    assert "trend-bar" in html
    assert "severity-badge" in html
    assert "compare-trend" in html
    assert "Error Code" in html
    assert "Error Summary" in html


def test_hub_and_journeys_copy_is_normalized():
    hub_html = Path("d:/Project/web/growth-automation/index.html").read_text(encoding="utf-8")
    journeys_html = Path("d:/Project/web/growth-automation/journeys.html").read_text(encoding="utf-8")
    app_js = Path("d:/Project/web/growth-automation/app.js").read_text(encoding="utf-8")

    assert "실제 여정 결과를 바로 확인하세요" in hub_html
    assert "오늘의 운영 포인트" in hub_html
    assert "사용자 여정을 바로 전진시키고 상태 변화를 즉시 확인하세요" in journeys_html
    assert "지금 바로 여정 진행" in journeys_html
    assert 'id="journeySavedFilters"' in journeys_html
    assert 'id="journeyTrendStrip"' in journeys_html
    assert 'id="journeyCompareGrid"' in journeys_html
    assert 'id="journeyDetailGrid"' in journeys_html
    assert "trend-spark" in journeys_html
    assert "trend-bar" in journeys_html
    assert "compare-trend" in journeys_html
    assert "화면 초기화 실패" in app_js
    assert "이벤트 실행 실패" in app_js
    assert "renderDetailGrid" in app_js
    assert "renderFilterChips" in app_js
    assert "renderCompareGrid" in app_js
    assert "renderTrendStrip" in app_js
    assert "getHistoricalBaseline" in app_js
    assert "getTrendSeries" in app_js
    assert "metricValue" in app_js
    assert "Last 7d vs prior 7d" in app_js


def test_clean_linked_docs_exist():
    responsive_doc = Path("d:/Project/web/RESPONSIVE_DESIGN_GUIDE_CLEAN.md").read_text(encoding="utf-8")
    dashboard_doc = Path("d:/Project/web/platform/DASHBOARD_IMPLEMENTATION_CLEAN.md").read_text(encoding="utf-8")
    ia_doc = Path("d:/Project/docs/IA.md").read_text(encoding="utf-8")

    assert "Responsive Design Guide" in responsive_doc
    assert "Dashboard Implementation Note" in dashboard_doc
    assert "RESPONSIVE_DESIGN_GUIDE_CLEAN.md" in ia_doc
    assert "DASHBOARD_IMPLEMENTATION_CLEAN.md" in ia_doc
