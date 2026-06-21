# Sales Dashboard

A web page for running the `/sales` commands from a browser — for **your own use**,
powered by **your Claude Max subscription** (no API key, no per-token cost).

## How it works
The dashboard runs on **your Mac** and drives the `claude` CLI, which is logged into
your Claude Max subscription. So runs cost nothing per token — they count against your
Max plan's usage limits. A tunnel (ngrok) exposes the local server at an HTTPS URL so
you can reach it from another location (e.g. work). Output is read from the file each
skill writes; access is gated by an unguessable URL token.

> **This is single-user, for you only.** A personal Claude subscription is for your own
> use. Don't share the URL with anyone else — that would be using your subscription to
> serve other people, which the consumer terms don't allow. (If you ever want a version
> other people can use, that needs an API key — see "Alternative" below.)

## Run it (subscription mode)

1. **Stay logged into Claude on your Mac:**
   ```bash
   claude        # if not logged in: run /login inside it
   ```
2. **Start the dashboard** (no API key needed):
   ```bash
   cd dashboard/backend
   python3.11 -m venv .venv && . .venv/bin/activate   # first time only
   pip install -r requirements.txt                    # first time only
   uvicorn app.main:app --env-file ../.env --port 8000
   ```
   `.env` only needs `DASHBOARD_TOKEN`, `SALES_REPO_DIR`, `WORKSPACE_DIR`, and the
   optional knobs (`MODEL`, `DAILY_CAP`, …). It must **not** contain an API key — the
   server drops `ANTHROPIC_API_KEY` at startup so it always uses your subscription.
3. **Open a tunnel** so you can reach it remotely:
   ```bash
   ngrok http 8000
   ```
   ngrok prints a URL like `https://<random>.ngrok-free.dev`. Your dashboard is at:
   ```
   https://<random>.ngrok-free.dev/d/<DASHBOARD_TOKEN>/
   ```
4. From your work browser, open that URL. First visit shows an ngrok warning page —
   click **Visit Site** once; that sets a cookie so the app's live updates work.

### Caveats of this setup
- **Your Mac must be awake** with both the server and `ngrok` running for the URL to
  work remotely. (Sleep = link goes dead.)
- **The ngrok free URL changes** every time you restart ngrok. For a stable URL, add a
  free static domain in your ngrok dashboard and run `ngrok http 8000 --domain=<yours>`.
- Usage counts against your **Max plan limits**, so the daily cap (`DAILY_CAP`) and
  single-in-flight guard still apply as guardrails against burning through your quota.

## Model
`MODEL` defaults to `claude-haiku-4-5`. On a subscription there's no per-token charge,
so you can raise it to `claude-sonnet-4-6` or `claude-opus-4-8` for deeper reports —
just note heavier models consume your Max limits faster.

## Alternative: always-on, API-key version (for others)
If you ever want a version that's online 24/7 or usable by other people, that can't use
a personal subscription — it needs an Anthropic API key and a host. The repo still
contains `Dockerfile` + `railway.json` for that path: set `ANTHROPIC_API_KEY` (+ the
same token/cap/model vars) on the host and deploy. That bills per token (Haiku keeps it
cheap) and is the ToS-compliant way to let someone else use it.

## Pipeline commands
`report` and `report-pdf` aggregate previously-generated reports from the shared
`pipeline/` directory. Run some research/prospect commands first, then `report`, then
`report-pdf` (which needs `SALES-REPORT.md` to exist).
