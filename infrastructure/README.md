# Infrastructure Directory

> **Purpose:** Infrastructure-as-Code, monitoring, deployment, and security configurations
> **Version:** 1.0
> **Updated:** 2026-02-25
> **Owner:** DevOps Team (Team E)

---

## Structure

```
infrastructure/
├── monitoring/              ← Prometheus, alerting, observability
│   ├── prometheus_config.yml
│   ├── alerts.yml          (to be created)
│   ├── rules.yml           (to be created)
│   └── dashboards/         (to be created)
│
├── deployment/             ← Kubernetes, Docker, deployment specs
│   ├── Dockerfile          (in project root)
│   ├── docker-compose.yml  (in project root)
│   └── k8s/               (to be created for production)
│
└── security/               ← Security policies, compliance
    ├── policies.md        (to be created)
    └── compliance/        (to be created)
```

---

## Monitoring (monitoring/)

### Prometheus Configuration
- **File:** `prometheus_config.yml`
- **Purpose:** Define metrics scrape targets and intervals
- **Usage:** Reference in Prometheus deployment
- **Services Monitored:**
  - SoftFactory API (port 8000)
  - PostgreSQL database
  - Redis cache
  - System metrics (CPU, memory)
  - Docker containers

### How to Use

1. **Configure Prometheus**
   ```bash
   docker run -d --name prometheus \
     -v $(pwd)/infrastructure/monitoring/prometheus_config.yml:/etc/prometheus/prometheus.yml \
     -p 9090:9090 \
     prom/prometheus
   ```

2. **Access Prometheus UI**
   - Navigate to http://localhost:9090
   - Verify all targets are UP
   - Query metrics (e.g., `http_requests_total`)

3. **Export Metrics from SoftFactory**
   ```bash
   # API endpoint: GET /api/metrics/prometheus
   curl http://localhost:8000/api/metrics/prometheus
   ```

---

## Deployment (deployment/)

### Docker Build & Run

```bash
# Build image
docker build -t softfactory:latest .

# Run locally
docker run -p 8000:8000 softfactory:latest

# Run with compose
docker-compose up -d
```

### Kubernetes Deployment (Production)

*To be created when migrating to Kubernetes*

---

## Security (security/)

### Security Policies

*To be created based on OWASP and compliance requirements*

---

## CI/CD Integration

This directory is integrated with GitHub Actions:

- **.github/workflows/build.yml** - Builds Docker images using Dockerfile in root
- **.github/workflows/deploy.yml** - Deploys using Docker and runs health checks
- **.github/workflows/security.yml** - Scans images and code for vulnerabilities

---

## Adding New Infrastructure

### Add a New Monitoring Target

1. Edit `infrastructure/monitoring/prometheus_config.yml`
2. Add new `scrape_configs` entry:
   ```yaml
   - job_name: 'new-service'
     static_configs:
       - targets: ['localhost:9999']
   ```
3. Reload Prometheus
4. Verify target appears in Prometheus UI

### Add Alerting Rules

1. Create `infrastructure/monitoring/alerts.yml`:
   ```yaml
   groups:
     - name: softfactory
       interval: 30s
       rules:
         - alert: HighErrorRate
           expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
           for: 5m
           annotations:
             summary: "High error rate detected"
   ```

2. Reference in `prometheus_config.yml`:
   ```yaml
   rule_files:
     - "alerts.yml"
   ```

---

## Troubleshooting

### Prometheus Not Scraping

1. Check config syntax:
   ```bash
   promtool check config infrastructure/monitoring/prometheus_config.yml
   ```

2. View Prometheus targets:
   - UI: http://localhost:9090/targets
   - Check for "DOWN" status

3. Verify service is running:
   ```bash
   curl http://localhost:8000/api/metrics/prometheus
   ```

### High Memory Usage

1. Check container stats:
   ```bash
   docker stats softfactory
   ```

2. Review error logs:
   ```bash
   docker logs softfactory | tail -20
   ```

3. Check database connections:
   ```bash
   curl http://localhost:8000/api/infrastructure/health
   ```

---

## Related Documentation

- **Deployment Checklist:** `/docs/standards/DEPLOYMENT_CHECKLIST.md`
- **Project Structure Validation:** `/scripts/validate_project_structure.sh`
- **CI/CD Workflows:** `/.github/workflows/`
- **Governance:** `/CLAUDE.md`

---

**Last Updated:** 2026-02-25
**Next Review:** 2026-03-10
