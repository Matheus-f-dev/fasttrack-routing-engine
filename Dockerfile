# =============================================================================
# Stage 1 — builder
# Installs dependencies into an isolated venv.
# The build toolchain (pip, wheel, gcc) stays in this stage only.
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Upgrade pip once, in the builder stage only
RUN pip install --upgrade pip --quiet

# Copy only the dependency manifest first to maximise layer cache reuse.
# The venv layer is rebuilt only when requirements.txt changes.
COPY requirements.txt .

RUN python -m venv /venv && \
    /venv/bin/pip install --quiet --no-cache-dir -r requirements.txt


# =============================================================================
# Stage 2 — runtime
# Copies the pre-built venv and application source only.
# No pip, no build tools, no test files.
# =============================================================================
FROM python:3.12-slim AS runtime

# ── Security: run as non-root ──────────────────────────────────────────────
RUN addgroup --system appgroup && \
    adduser  --system --ingroup appgroup --no-create-home appuser

WORKDIR /app

# Copy the venv from the builder stage
COPY --from=builder /venv /venv

# Copy application source (tests and dev files are excluded via .dockerignore)
COPY main.py .
COPY app/ ./app/

# Ensure the non-root user owns the workdir
RUN chown -R appuser:appgroup /app

USER appuser

# ── Runtime environment ────────────────────────────────────────────────────
# APP_HOST / APP_PORT   : bind address for Uvicorn
# WORKERS               : number of Uvicorn worker processes (default 1)
# LOG_LEVEL             : Uvicorn log level (default "info")
ENV APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    WORKERS=1 \
    LOG_LEVEL=info \
    PATH="/venv/bin:$PATH"

EXPOSE 8000

# ── Healthcheck ────────────────────────────────────────────────────────────
# Docker will mark the container as (un)healthy based on /health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${APP_PORT}/health')"

# ── Entrypoint ─────────────────────────────────────────────────────────────
CMD uvicorn main:app \
    --host $APP_HOST \
    --port $APP_PORT \
    --workers $WORKERS \
    --log-level $LOG_LEVEL \
    --no-access-log
