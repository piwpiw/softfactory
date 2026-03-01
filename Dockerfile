# SoftFactory — Multi-Stage Production Dockerfile
# Final image size: ~350MB
# Port: 9000 (gunicorn, 4 sync workers)
#
# Build:  docker build -t softfactory:latest .
# Run:    docker run -p 9000:9000 --env-file .env softfactory:latest

# ============================================================
# STAGE 1: Builder — install Python deps in isolated userspace
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build-only system deps (removed in runtime image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Separate requirements copy to maximise layer cache hits
COPY requirements.txt .

# Install into /root/.local so we can COPY them cleanly
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================
# STAGE 2: Runtime — lean image with only what's needed
# ============================================================
FROM python:3.11-slim

LABEL org.opencontainers.image.title="SoftFactory Platform"
LABEL org.opencontainers.image.description="SoftFactory SaaS platform (Flask + gunicorn)"
LABEL org.opencontainers.image.url="https://github.com/softfactory-io/softfactory"

WORKDIR /app

# Runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built packages from builder stage
COPY --from=builder /root/.local /root/.local

# Add user packages to PATH and set sensible Python env vars
ENV PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    PORT=9000

# Create non-root user for defence-in-depth
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Copy application source (exclude dev artefacts via .dockerignore)
COPY --chown=appuser:appuser . .

# Ensure log and upload dirs exist and are writable by appuser
RUN mkdir -p /app/logs /app/uploads /app/instance && \
    chown -R appuser:appuser /app/logs /app/uploads /app/instance

# Switch to non-root user
USER appuser

EXPOSE 9000

# Container-level health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# Gunicorn: 4 sync workers, 120s timeout, structured logs to stdout
CMD ["gunicorn", \
     "--bind", "0.0.0.0:9000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--worker-tmp-dir", "/dev/shm", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "--forwarded-allow-ips", "*", \
     "start_platform:app"]
