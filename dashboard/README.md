# Sales Dashboard

A no-password web page so a non-technical user can run the `/sales` commands.

## How it works
A FastAPI backend runs the real sales skills via the Claude Agent SDK (which drives
the `@anthropic-ai/claude-code` CLI) and streams progress + the final report to a
single web page. Output is read from the file each skill writes. Access is gated by
an unguessable URL token; spend is bounded by a daily run cap, a single-in-flight
concurrency guard, and a `max_turns` ceiling.

## Deploy (Railway)
1. Create a Railway project from this repo; set the Dockerfile path to
   `dashboard/Dockerfile`. The build copies the repo into `dashboard/salesagent/`
   (see acceptance Step 2), installs Node 20 + the `claude` CLI, the sales repo's
   Python deps, and the `/sales` skills.
2. Set environment variables:
   - `ANTHROPIC_API_KEY` — your key (billing enabled).
   - `DASHBOARD_TOKEN` — a long random string (`openssl rand -hex 16`).
   - `DAILY_CAP` — e.g. `20`. `MAX_TURNS` — e.g. `80`. `MAX_CONCURRENT` — `1`.
3. **Attach a persistent volume mounted at `/app/workspace` (= `WORKSPACE_DIR`).**
   This is REQUIRED, not optional: Railway's container filesystem is ephemeral, so
   without a volume `cap.json` (your daily cost cap), per-run dirs, and the shared
   `pipeline/` are **wiped on every redeploy/crash/restart** — the cap silently
   resets to 0 and `report` finds an empty pipeline. The volume makes both durable.
4. **Keep replicas at 1** (`numReplicas: 1` in `railway.json`). The cap and the
   concurrency guard are per-container; multiple replicas multiply your spend ceiling.
5. (Strongly recommended) Restrict outbound network egress to Anthropic's API +
   the domains the skills need (search/company sites). If a prompt injection ever
   succeeds, egress restriction is what stops it from exfiltrating `ANTHROPIC_API_KEY`.
6. Deploy. Health probe is `/health` (unauthenticated).
7. The public link for Lucas is:
   `https://<your-app>.up.railway.app/d/<DASHBOARD_TOKEN>/`
   Send him that single link. No login, no GitHub.

## Cost controls (and their real limits — read this)
- **Daily cap is the true dollar ceiling.** It stops spend after N runs/day; a failed
  run is refunded (not charged a slot). It only holds if the persistent volume +
  single replica are in place (see Deploy 3–4) — otherwise it silently resets.
- **`max_turns` is NOT a reliable cost cap.** It bounds the *orchestrator* loop, but
  `prospect` fans out ~5 subagents via the Task tool, each with its own token budget —
  which is where most spend happens. Treat `max_turns` as a runaway-loop guard, not a
  cost ceiling. Per-run cost is logged (`[run] command=… cost_usd=…`) for visibility;
  watch those logs and tune `DAILY_CAP` to your tolerance.
- **Single-in-flight** (`MAX_CONCURRENT=1`) stops spam-click pile-ups.

## Residual risk (read before sharing)
- **Worst case is API-key theft, not just "a few extra runs."** Bash is enabled (the
  bundled Python scripts need it) and the agent runs with `bypassPermissions` (headless
  can't answer prompts). Framing the arg as `<user_input>…DATA` is a *soft mitigation,
  not a boundary* — a successful prompt injection through the input field can run
  arbitrary shell in a container that holds `ANTHROPIC_API_KEY` in its environment, and
  could exfiltrate that key and run up your bill. **Rotating `DASHBOARD_TOKEN` does NOT
  undo a leaked key** — if you suspect a malicious input ran, rotate the Anthropic key.
- **Mitigations in place / required:** scoped `allowed_tools`, untrusted-arg framing,
  and (required) restricted outbound egress (Deploy 5) so exfiltration is hard even if
  injection succeeds. Treat this as a **single-trusted-user** tool, not a public service.
  Rotate `DASHBOARD_TOKEN` to revoke a forwarded link (invalidates the old link).

## Pipeline commands
`report` and `report-pdf` aggregate previously-generated reports from the shared
`pipeline/` directory. Run some research/prospect commands first, then `report`,
then `report-pdf` (which needs `SALES-REPORT.md` to exist).

## Local development
```bash
cd dashboard/backend
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
DASHBOARD_TOKEN=devtok ANTHROPIC_API_KEY=sk-ant-... \
  SALES_REPO_DIR=$HOME/Documents/Projects/SalesAgent_Claude WORKSPACE_DIR=/tmp/ws \
  python -m uvicorn app.main:app --port 8000
# open http://localhost:8000/d/devtok/
python -m pytest          # unit tests; integration smokes skipped unless RUN_INTEGRATION=1
```
