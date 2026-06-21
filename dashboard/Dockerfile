# Build context is the REPO ROOT (Railway's default), with dockerfilePath set to
# dashboard/Dockerfile. The repo root itself IS the "sales repo" (skills/, scripts/,
# sales/, templates/, install.sh, requirements.txt) — so all COPY paths below are
# relative to the repo root, NOT to dashboard/.
FROM python:3.11-slim

ENV HOME=/root \
    SALES_REPO_DIR=/app/salesagent \
    WORKSPACE_DIR=/app/workspace \
    PYTHONPATH=/app/backend

# System deps + Node 20 (the Claude Code CLI requires Node 18+).
RUN apt-get update && apt-get install -y --no-install-recommends curl git ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# The Python SDK shells out to this CLI — without it, every /run fails at runtime.
RUN npm install -g @anthropic-ai/claude-code && claude --version

WORKDIR /app

# Dashboard backend deps (copied first for layer caching).
COPY dashboard/backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Sales repo's own deps (reportlab/bs4/requests) — requirements.txt is at repo root.
COPY requirements.txt /app/salesagent/requirements.txt
RUN pip install --no-cache-dir -r /app/salesagent/requirements.txt

# The repo root IS the sales repo: copy it in and install the /sales skills into
# /root/.claude (what setting_sources=["user"] reads). No "|| true": load-bearing.
COPY . /app/salesagent
RUN bash /app/salesagent/install.sh

# App code + static page (paths relative to repo root).
COPY dashboard/backend /app/backend
COPY dashboard/frontend /app/frontend
RUN mkdir -p /app/workspace

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000"]
