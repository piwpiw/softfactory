@echo off
REM Open All SoftFactory Pages in Chrome
REM 모든 페이지를 Chrome에서 열기

echo Opening all SoftFactory pages in Chrome...
echo 모든 SoftFactory 페이지를 Chrome에서 열고 있습니다...

REM Main Pages
start "" "chrome" "http://localhost:8080/"
start "" "chrome" "http://localhost:8080/platform/dashboard.html"

REM CooCook Service
start "" "chrome" "http://localhost:8080/coocook/"
start "" "chrome" "http://localhost:8080/coocook/explore.html"
start "" "chrome" "http://localhost:8080/coocook/booking.html"
start "" "chrome" "http://localhost:8080/coocook/my-bookings.html"

REM SNS Auto Service
start "" "chrome" "http://localhost:8080/sns-auto/"
start "" "chrome" "http://localhost:8080/sns-auto/accounts.html"
start "" "chrome" "http://localhost:8080/sns-auto/schedule.html"

REM Review Service
start "" "chrome" "http://localhost:8080/review/"
start "" "chrome" "http://localhost:8080/review/create.html"

REM AI Automation Service
start "" "chrome" "http://localhost:8080/ai-automation/"
start "" "chrome" "http://localhost:8080/ai-automation/create.html"
start "" "chrome" "http://localhost:8080/ai-automation/scenarios.html"

REM WebApp Builder Service
start "" "chrome" "http://localhost:8080/webapp-builder/"
start "" "chrome" "http://localhost:8080/webapp-builder/create.html"

REM API Pages
start "" "chrome" "http://localhost:8000/health"
start "" "chrome" "http://localhost:8000/api/errors/recent"
start "" "chrome" "http://localhost:8000/api/metrics/prometheus"

echo.
echo All pages opened in Chrome!
echo 모든 페이지가 Chrome에서 열렸습니다!
pause
