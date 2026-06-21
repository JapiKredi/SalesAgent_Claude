# Python base (Debian bookworm; pip installs freely). Add Node 20 for the Claude CLI.
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

# Dashboard backend deps.
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Sales repo + ITS OWN deps (reportlab/bs4/requests) — needed by report-pdf & scripts.
COPY salesagent /app/salesagent
RUN pip install --no-cache-dir -r /app/salesagent/requirements.txt

# Install the /sales skills into /root/.claude (what setting_sources=["user"] reads).
# No "|| true": this is load-bearing — if it fails, the build must fail.
RUN bash /app/salesagent/install.sh

COPY backend /app/backend
COPY frontend /app/frontend
RUN mkdir -p /app/workspace

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000"]
