# Sales Dashboard — Design Spec

**Date:** 2026-06-21
**Status:** Approved (design), pending spec review
**Goal:** Give a non-technical user (Lucas) a web page where he can run the
`/sales` commands and see their output — without using GitHub, without running
Claude himself, and without a password.

---

## 1. Problem & Context

The `SalesAgent_Claude` repo ships 14 `/sales` commands as **Claude Code
skills**. A skill is not a normal program: it is a set of instructions that
*Claude (the LLM)* carries out — launching research subagents, browsing the web,
running helper Python scripts, and writing a markdown report. They only execute
because there is a Claude runtime + an Anthropic API key + web access behind
them.

Therefore a static website cannot run them on its own. For Lucas to type a
command and get a real report, a backend we host must run Claude on his behalf
when he clicks **Run**. The website is the front door; the engine lives on the
backend.

### Central trade-off (accepted)
"No password" + public URL + our API key behind it means anyone with the link
can spend our Anthropic budget. We accept this and mitigate it with a **daily
run cap** and an **unguessable URL token** (not a password — just un-findable).

---

## 2. Decisions (locked)

| Decision | Choice |
|---|---|
| What happens on Run | **Live runs** via a real backend (fresh report each time) |
| Hosting | **Cloud host, always on** (Railway/Render/Fly), so the link works 24/7 |
| Cost guardrail | **Daily run cap** + **unguessable URL token** |
| Claude auth | **Anthropic API key** (`ANTHROPIC_API_KEY` server env var) |
| Command scope | **All 14** commands from the table |
| Engine | **Claude Agent SDK (Python)** running the real installed sales skills |

---

## 3. Architecture

Two pieces, one deployment (single container).

```
┌─────────────────────────────┐         ┌──────────────────────────────────┐
│  Frontend (static page)     │  HTTPS  │  Backend (FastAPI, Python)       │
│  - command table (14)       │ ──────► │  POST /run     {command, arg}    │
│  - adaptive input box       │         │  GET  /status/{run_id} (SSE)     │
│  - Run button               │ ◄────── │  GET  /usage                     │
│  - live status + output     │   SSE   │                                  │
│  - download (.md / .pdf)    │         │   ├─ allowlist + cap check       │
└─────────────────────────────┘         │   ├─ Claude Agent SDK runner     │
                                         │   │    (14 sales skills loaded,  │
                                         │   │     ANTHROPIC_API_KEY)       │
                                         │   ├─ helper scripts (lead_scorer,│
                                         │   │     generate_pdf_report …)   │
                                         │   └─ workspace store (files)     │
                                         └──────────────────────────────────┘
```

### 3.1 Frontend (one page, built for a non-technical user)
- Renders the **command table** (all 14 commands, description, output type).
- Picking a command reveals **one input box** whose label/placeholder adapts:
  - `url` → prospect, quick, research, qualify, contacts, prep, competitors
  - `prospect name` → outreach, followup
  - `client` → proposal
  - `topic` → objections
  - `description` → icp
  - *(no input)* → report, report-pdf
- **Run** button → calls `POST /run`, then subscribes to `GET /status/{run_id}`.
- **Live status area** shows human-readable progress ("Researching company…",
  "Scoring lead…", "Writing report…") so a 1–3 min `prospect` run never looks
  frozen.
- **Output panel** renders the returned markdown; **Download** button saves
  `.md` (or `.pdf` for `report-pdf`).
- **Usage line**: "X of N runs left today."
- No jargon, no GitHub references, no login screen.

### 3.2 Backend (FastAPI, Python)
Endpoints:
- `POST /run {command, arg}`
  1. Validate `command` against a hard **allowlist** of the 14 commands.
  2. Validate/trim `arg` (length cap; URL-shape check for url commands).
  3. Check **daily run cap**; if exceeded → `429` with friendly message.
  4. Create `run_id`, start the Agent SDK run async, return `{run_id}`.
- `GET /status/{run_id}` (Server-Sent Events) → streams progress events, then a
  final event carrying the markdown output (and a PDF download URL if relevant).
- `GET /usage` → `{used, limit, resets_at}`.
- Auth to Claude: `ANTHROPIC_API_KEY` read from server env only; never sent to
  the browser.

### 3.3 Engine (Claude Agent SDK)
- A runner module loads the 14 sales skills (the repo's `skills/` + `sales/`)
  and the agent definitions (`agents/`), and exposes them to an Agent SDK
  session.
- On a run, it issues the equivalent of `/sales <command> <arg>` and captures:
  - streamed progress (mapped to friendly status strings), and
  - the produced output file(s) from the run workspace.
- Helper Python scripts (`lead_scorer.py`, `contact_finder.py`,
  `analyze_prospect.py`, `generate_pdf_report.py`) are available on the
  container so skills that call them work unchanged.

### 3.4 Workspace / state
- Each run writes its output files into a per-deployment workspace directory.
- `/sales report` and `/sales report-pdf` aggregate a **pipeline** of prior
  reports — so we persist run outputs to that workspace, letting those two
  commands summarize what has been run. Plain files; **no database**.

---

## 4. Cost & abuse controls
- **Daily run cap** (configurable, default e.g. 20 runs/day). Persisted counter,
  resets at local midnight. On exceed → friendly "come back tomorrow."
- **Unguessable URL token** in the path (e.g. `/d/8f3k9x2q`). Requests without a
  valid token are rejected. Shared only with Lucas. Not a password.
- **Per-run input caps** (arg length, single in-flight run per token) to stop
  accidental spam-clicking.
- API key lives only in the server environment.

---

## 5. Data flow (happy path)
1. Lucas opens `https://<host>/d/<token>`.
2. Picks `prospect`, types a company URL, clicks **Run**.
3. Frontend → `POST /run` → backend checks token + cap → returns `run_id`.
4. Frontend subscribes to `GET /status/{run_id}`; status area updates live.
5. Agent SDK runs the real `sales-prospect` skill (5 subagents).
6. Final SSE event delivers the rendered markdown; **Download** offers the file.
7. Usage counter decrements; `GET /usage` reflects remaining runs.

## 6. Error handling
- Invalid/blocked command → `400`, UI shows "That command isn't available."
- Cap exceeded → `429`, UI shows the friendly limit message + reset time.
- Missing token → `403`, generic not-found page (don't reveal the app).
- Agent run failure / timeout → SSE error event; UI shows "Something went wrong,
  try again" + a short reference id; full error logged server-side only.
- API key missing/invalid at boot → backend refuses to start with a clear log.

## 7. Testing
- **Unit:** command allowlist validation; arg validation; cap counter
  increment/reset; token check.
- **Integration:** `POST /run` → SSE stream → final output for a cheap command
  (e.g. `quick` or `icp`) against the real Agent SDK in a test workspace.
- **Manual acceptance:** from a phone browser with only the URL, run `research`
  and `prospect`, confirm live status, rendered output, and PDF download for
  `report-pdf`.

## 8. Deliverables
- `dashboard/frontend/` — single static page (HTML/CSS/JS).
- `dashboard/backend/` — FastAPI app + Agent SDK runner + helpers wiring.
- `dashboard/Dockerfile` + deploy config for the chosen cloud host.
- README: how to set `ANTHROPIC_API_KEY`, the daily cap, and the URL token; how
  to deploy; how to share the link with Lucas.

## 9. Out of scope (YAGNI)
- User accounts / multi-user separation.
- Editing or saving prospects beyond the report files.
- Rich history UI beyond "what's been run" for the report command.
- Rate limiting beyond single-in-flight + daily cap (revisit if abused).

## 10. Open questions for implementation phase
- Exact cloud host (Railway vs Render vs Fly) — pick during writing-plans.
- Default daily cap number.
- Whether to swap the 5-agent `prospect` to a cheaper model to cut per-run cost
  (deferred; not blocking).
