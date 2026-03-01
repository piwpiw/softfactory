# Load Testing Execution Guide

**Date:** 2026-02-26
**Purpose:** Step-by-step instructions to run complete load testing suite

---

## Quick Start (5 minutes)

### Prerequisites Check
```bash
# 1. Verify Flask is running
curl http://localhost:9000/api/review/campaigns \
  -H "Authorization: Bearer demo_token"
# Expected: 200 OK with campaigns array

# 2. Check Node.js is available
node --version  # Should be v16+

# 3. Check Python
python --version  # Should be 3.8+
```

### Run Load Tests

**Terminal 1: Start Flask Application**
```bash
cd D:/Project
python start_platform.py

# Expected output:
# * Running on http://localhost:9000
# * WARNING: This is a development server.
```

**Terminal 2: Install k6 and Run Load Test**
```bash
# Install k6 (one-time)
npm install -g k6

# Verify installation
k6 --version

# Run the load test (5 minutes)
cd D:/Project
k6 run tests/load/load-test.js

# Expected output:
# init - 00:00:00 Starting load test
# data_received..................: 2.3 MB 15 kB/s
# data_sent........................: 1.2 MB 8.0 kB/s
# http_req_duration................: avg=245ms min=45ms med=180ms max=2.1s p(95)=520ms p(99)=890ms
```

**Terminal 3: Run Performance Profiler**
```bash
cd D:/Project
python scripts/profile_app.py

# Expected output:
# Progress: 50.0% (150s/300s)
#
# Performance report saved to performance_report.json
```

---

## Detailed Execution Steps

### Step 1: Prepare Environment

```bash
# Clone test dependencies
pip install requests psutil

# Verify database is accessible
sqlite3 D:/Project/platform.db ".tables"
# Should show tables: user, campaign, sns_account, etc.

# Verify API endpoints
curl -s http://localhost:9000/api/review/campaigns \
  -H "Authorization: Bearer demo_token" | python -m json.tool | head -20
```

### Step 2: Run Full Load Test Suite

#### Configuration Options

**Light Load (for quick testing)**
```javascript
// Modify tests/load/load-test.js
export let options = {
  stages: [
    { duration: '10s', target: 5 },
    { duration: '30s', target: 10 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
  },
};
```

**Standard Load (recommended)**
```javascript
// Uses default in load-test.js (50-100 VUs)
```

**Heavy Load (stress test)**
```javascript
export let options = {
  stages: [
    { duration: '1m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '2m', target: 200 },  // Peak stress
    { duration: '1m', target: 0 },
  ],
};
```

#### Run Command with Options
```bash
# Standard test with JSON output
k6 run tests/load/load-test.js \
  --out json=test-results-$(date +%Y%m%d-%H%M%S).json \
  --summary-export=test-summary.json

# With verbose logging
k6 run tests/load/load-test.js -v

# With custom API URL
k6 run tests/load/load-test.js --vus 50 --duration 3m \
  -e API_BASE="http://production.example.com"

# Run only specific endpoints
k6 run tests/load/load-test.js -e ENDPOINT_FILTER="review"
```

### Step 3: Monitor System Performance

```bash
# Option 1: Windows Task Manager
taskmgr.exe
# Watch: CPU %, Memory (MB), Disk I/O

# Option 2: PowerShell monitoring
Get-Process python | Select-Object ProcessName, CPU, WorkingSet

# Option 3: Run Python profiler
python scripts/profile_app.py

# Option 4: Database performance
# In another terminal, run:
sqlite3 D:/Project/platform.db ".eqp on"
SELECT COUNT(*) FROM campaigns;  # Should complete in <100ms
```

### Step 4: Analyze Results

#### k6 Results Interpretation

```
✓ http_req_duration: avg=245ms, med=180ms, min=45ms, max=2.1s, p(95)=520ms
  - avg: Average response time across all requests
  - med: Median (50th percentile)
  - p(95): 95% of requests completed in <520ms (ideal target)
  - max: Worst-case response time

✓ http_reqs_failed: 5 (out of 12,450 = 0.04%)
  - Error rate: 0.04% is acceptable
  - Investigate if >1%

✓ http_reqs: 12,450 total requests
  - At 100 VUs for 5 minutes: ≈ 2,490 req/min = 41.5 req/sec
```

#### Performance Report JSON Analysis

```bash
# Pretty-print report
python -c "import json; print(json.dumps(json.load(open('performance_report.json')), indent=2))"

# Extract slow endpoints
python << 'EOF'
import json
with open('performance_report.json') as f:
    data = json.load(f)
    print("SLOW ENDPOINTS:")
    for ep in data.get('slow_endpoints', []):
        print(f"  {ep['endpoint']}: {ep['avg_ms']:.0f}ms")
    print(f"\nTotal requests: {data['summary']['total_requests']}")
    print(f"Total errors: {data['summary']['total_errors']}")
    print(f"Peak CPU: {data['summary']['peak_cpu_percent']:.1f}%")
    print(f"Peak Memory: {data['summary']['peak_memory_percent']:.1f}%")
EOF
```

### Step 5: Troubleshooting Common Issues

#### Issue: "Connection Refused" on API
```bash
# Check if Flask is running
netstat -an | find "9000"

# Or restart Flask
cd D:/Project
python start_platform.py
```

#### Issue: k6 Install Fails
```bash
# Try direct download
choco install k6  # If using Chocolatey
# Or download from https://github.com/grafana/k6/releases

# Verify
k6 --version
```

#### Issue: "Authentication Failed" (401 errors)
```bash
# Verify demo token is correct
curl http://localhost:9000/api/review/campaigns \
  -H "Authorization: Bearer demo_token"

# Check if token format correct in load-test.js
# Should be: 'Bearer demo_token'
```

#### Issue: Database Locked Error
```bash
# SQLite gets locked during concurrent writes
# Solution 1: Use PostgreSQL (recommended for load testing)
# Solution 2: Increase timeout in backend/config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'connect_args': {'timeout': 30},
}

# Solution 3: Reduce concurrent VUs
# In load-test.js, reduce target VUs to 20-30
```

#### Issue: "Out of Memory" Error
```bash
# Flask using too much memory
# Solutions:
# 1. Reduce VU count in load-test.js
# 2. Enable query result streaming
# 3. Clear cache between tests

# Check memory usage
python -c "import psutil; print(f'Available: {psutil.virtual_memory().available / (1024**3):.1f}GB')"
```

---

## Interpreting Results

### Healthy Performance Indicators ✅

- [ ] p95 response time: <500ms
- [ ] p99 response time: <1000ms
- [ ] Error rate: <1%
- [ ] CPU usage: <70% at peak load
- [ ] Memory growth: Stable (not increasing continuously)
- [ ] Zero database connection timeouts
- [ ] No "slow query" warnings in logs

### Warning Signs ⚠️

- [ ] p95 > 1000ms
- [ ] Error rate > 1%
- [ ] CPU spiking to >85%
- [ ] Memory increasing >100MB over test duration
- [ ] Database connection errors
- [ ] "Max retries exceeded" errors

### Performance Issues 🔴

- [ ] p95 > 2000ms (unacceptable)
- [ ] Error rate > 5%
- [ ] CPU stuck at 99%
- [ ] Memory consuming >1GB
- [ ] API timeouts or crashes

---

## Post-Test Analysis

### Generate Comparison Report

```python
# compare_test_results.py
import json
from datetime import datetime

def compare_results(baseline_file, current_file):
    with open(baseline_file) as f:
        baseline = json.load(f)
    with open(current_file) as f:
        current = json.load(f)

    print("PERFORMANCE COMPARISON")
    print("=" * 60)

    baseline_p95 = baseline['summary'].get('p95_ms', 0)
    current_p95 = current['summary'].get('p95_ms', 0)
    improvement = ((baseline_p95 - current_p95) / baseline_p95) * 100

    print(f"p95 Latency:")
    print(f"  Baseline: {baseline_p95:.0f}ms")
    print(f"  Current:  {current_p95:.0f}ms")
    print(f"  Change:   {improvement:+.1f}%")

    print(f"\nError Rate:")
    baseline_errors = baseline['summary']['total_errors']
    current_errors = current['summary']['total_errors']
    print(f"  Baseline: {baseline_errors} errors")
    print(f"  Current:  {current_errors} errors")

# Run comparison
compare_results('baseline.json', 'performance_report.json')
```

### Optimization Recommendations Based on Results

**If p95 > 500ms:**
1. Check `PERFORMANCE_ANALYSIS.md` Section 4 (Bottleneck Analysis)
2. Run database query profiler
3. Enable Redis caching
4. Add database indexes

**If error rate > 1%:**
1. Check Flask error logs: `backend/logs/`
2. Verify database connectivity
3. Check rate limiting headers
4. Increase connection pool size

**If CPU > 80%:**
1. Reduce VU load
2. Enable connection pooling
3. Implement load balancing
4. Move heavy operations to background workers

---

## Scheduling Load Tests

### Weekly Testing Schedule

```bash
#!/bin/bash
# load-test-weekly.sh

# Run every Friday at 2 PM
# Add to crontab: 0 14 * * 5 /path/to/load-test-weekly.sh

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RESULTS_DIR="/path/to/results"

echo "Starting weekly load test..."

# Run test
k6 run tests/load/load-test.js \
  --out json="${RESULTS_DIR}/load-test-${TIMESTAMP}.json"

# Run profiler
python scripts/profile_app.py

# Generate report
python << EOF
import json, sys
with open('performance_report.json') as f:
    data = json.load(f)
    if data['summary']['slow_endpoint_count'] > 3:
        print("WARNING: Too many slow endpoints")
        sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo "Load test PASSED"
else
    echo "Load test FAILED - investigating..."
fi
```

### Continuous Performance Monitoring

```python
# continuous_monitor.py
# Run daily to detect regressions

import json
import subprocess
from pathlib import Path

def run_daily_test():
    # Quick 1-minute test
    subprocess.run([
        'k6', 'run', 'tests/load/load-test.js',
        '--out', f'json=results/daily-{Path.today()}.json'
    ])

def check_regression(current, baseline):
    threshold_ms = 500  # Alert if p95 > 500ms
    return current['p95_ms'] > threshold_ms

if __name__ == '__main__':
    run_daily_test()
```

---

## Cleanup and Next Steps

### After Testing

1. **Archive results**
   ```bash
   mkdir -p results/archive
   mv test-results*.json results/archive/
   mv performance_report.json results/archive/
   ```

2. **Review performance_report.json**
   ```bash
   cat performance_report.json | python -m json.tool | less
   ```

3. **Document findings**
   - Create ticket with bottlenecks identified
   - Assign optimizations to sprints
   - Update PERFORMANCE_ANALYSIS.md with actual results

4. **Implement fixes** (if needed)
   ```bash
   # Example: Add database indexes
   sqlite3 D:/Project/platform.db < docs/sql/indexes.sql

   # Re-run test to verify improvement
   k6 run tests/load/load-test.js
   ```

---

## Success Criteria

**Load testing is complete when:**

- [ ] k6 test runs for full duration without errors
- [ ] performance_report.json generated successfully
- [ ] p95 latency documented
- [ ] All endpoints tested return <2000ms response time
- [ ] Error rate <1%
- [ ] System CPU <80% at peak load
- [ ] Bottleneck analysis completed
- [ ] Optimization recommendations documented

---

## Additional Resources

- [k6 Documentation](https://k6.io/docs/)
- [Performance Analysis Report](./PERFORMANCE_ANALYSIS.md)
- [Flask Performance Tuning](https://flask.palletsprojects.com/en/2.0.x/patterns/deployment/)
- [SQLAlchemy Query Optimization](https://docs.sqlalchemy.org/en/14/faq/performance.html)

