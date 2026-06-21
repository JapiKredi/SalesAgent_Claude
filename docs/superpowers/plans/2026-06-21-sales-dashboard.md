# Sales Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a no-password web dashboard where a non-technical user runs the 14 `/sales` commands live and sees rendered output.

**Architecture:** A FastAPI backend serves a single static page and exposes `/run` (start a job), `/status/{id}` (SSE progress + final output), and `/usage`. A runner module executes the real installed sales skills through the Claude Agent SDK (Python) using `ANTHROPIC_API_KEY`. Access is gated by an unguessable URL token; spend is bounded by a file-backed daily run cap. One Docker container, deployed to Railway.

**Tech Stack:** Python 3.11, FastAPI, uvicorn, sse-starlette, claude-agent-sdk, pytest, vanilla HTML/CSS/JS (marked.js via CDN for markdown), Docker.

---

## File Structure

```
dashboard/
  backend/
    app/
      __init__.py        # package marker
      config.py          # env-driven settings (token, cap, key, paths)
      commands.py        # the 14-command allowlist + per-command arg metadata
      validation.py      # validate_command(), validate_arg()
      cap.py             # file-backed daily run counter with date reset
      runs.py            # in-memory run registry + event queues for SSE
      runner.py          # Claude Agent SDK runner -> async events
      status_map.py      # map raw SDK message -> friendly status string
      main.py            # FastAPI app: routes, static mount, SSE
    tests/
      test_commands.py
      test_validation.py
      test_cap.py
      test_status_map.py
      test_api.py            # route tests with a fake runner
      test_runner_integration.py  # real SDK, opt-in
    requirements.txt
    pytest.ini
  frontend/
    index.html
    styles.css
    app.js
  Dockerfile
  railway.json
  .env.example
  README.md
```

Each backend module has one responsibility and is unit-tested in isolation. `runner.py` is the only module that touches the network/SDK; everything else is pure and fast to test.

---

## Task 0: Project skeleton + dependency spike

**Files:**
- Create: `dashboard/backend/requirements.txt`
- Create: `dashboard/backend/pytest.ini`
- Create: `dashboard/backend/app/__init__.py`
- Create: `dashboard/.env.example`

- [ ] **Step 1: Create requirements.txt**

```
fastapi>=0.110
uvicorn[standard]>=0.29
sse-starlette>=2.1
claude-agent-sdk>=0.1.0
pydantic>=2.6
pytest>=8.0
pytest-asyncio>=0.23
httpx>=0.27
```

- [ ] **Step 2: Create pytest.ini**

```ini
[pytest]
asyncio_mode = auto
markers =
    integration: hits the real Claude Agent SDK (costs API money); opt-in via RUN_INTEGRATION=1
addopts = -q
testpaths = tests
```

- [ ] **Step 3: Create empty package marker**

`dashboard/backend/app/__init__.py`:
```python
```

- [ ] **Step 4: Create .env.example**

`dashboard/.env.example`:
```
# Required: Anthropic API key with billing enabled (console.anthropic.com)
ANTHROPIC_API_KEY=sk-ant-...
# Unguessable path token Lucas uses: https://<host>/d/<DASHBOARD_TOKEN>
DASHBOARD_TOKEN=change-me-to-a-long-random-string
# Max runs allowed per calendar day (resets local midnight)
DAILY_CAP=20
# Absolute path to the installed SalesAgent_Claude repo (skills live here)
SALES_REPO_DIR=/app/salesagent
# Where run outputs are written (pipeline state for report/report-pdf)
WORKSPACE_DIR=/app/workspace
```

- [ ] **Step 5: Create venv, install, confirm SDK import (spike)**

Run:
```bash
cd dashboard/backend && python3.11 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python -c "import claude_agent_sdk as s; print('sdk-ok', [n for n in dir(s) if 'query' in n.lower() or 'Options' in n or 'Client' in n])"
```
Expected: prints `sdk-ok` and a list containing `query`, `ClaudeAgentOptions`, `ClaudeSDKClient` (or close equivalents).

> **If the installed SDK exposes different names** (the package evolves), note the actual symbols here and use them in Task 6. This is the one place the plan touches an external API surface — verify before coding the runner.

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/requirements.txt dashboard/backend/pytest.ini dashboard/backend/app/__init__.py dashboard/.env.example
git commit -m "chore: dashboard backend skeleton + deps"
```

---

## Task 1: Command catalog (the 14 commands)

**Files:**
- Create: `dashboard/backend/app/commands.py`
- Test: `dashboard/backend/tests/test_commands.py`

- [ ] **Step 1: Write the failing test**

`tests/test_commands.py`:
```python
from app.commands import COMMANDS, get_command

def test_all_fourteen_present():
    assert len(COMMANDS) == 14
    names = {c["name"] for c in COMMANDS}
    assert names == {
        "prospect", "quick", "research", "qualify", "contacts",
        "outreach", "followup", "prep", "proposal", "objections",
        "icp", "competitors", "report", "report-pdf",
    }

def test_arg_kinds_are_known():
    allowed = {"url", "prospect", "client", "topic", "description", "none"}
    assert all(c["arg_kind"] in allowed for c in COMMANDS)

def test_report_commands_take_no_arg():
    assert get_command("report")["arg_kind"] == "none"
    assert get_command("report-pdf")["arg_kind"] == "none"

def test_report_pdf_outputs_pdf():
    assert get_command("report-pdf")["output"] == "pdf"
    assert get_command("research")["output"] == "markdown"

def test_get_unknown_returns_none():
    assert get_command("definitely-not-a-command") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_commands.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.commands'`)

- [ ] **Step 3: Write minimal implementation**

`app/commands.py`:
```python
"""Single source of truth for the 14 /sales commands exposed by the dashboard."""

COMMANDS = [
    {"name": "prospect",   "arg_kind": "url",         "label": "Full prospect audit",        "output": "markdown"},
    {"name": "quick",      "arg_kind": "url",         "label": "60-second snapshot",         "output": "markdown"},
    {"name": "research",   "arg_kind": "url",         "label": "Company research",           "output": "markdown"},
    {"name": "qualify",    "arg_kind": "url",         "label": "BANT/MEDDIC qualification",  "output": "markdown"},
    {"name": "contacts",   "arg_kind": "url",         "label": "Decision makers",            "output": "markdown"},
    {"name": "outreach",   "arg_kind": "prospect",    "label": "Cold outreach sequence",     "output": "markdown"},
    {"name": "followup",   "arg_kind": "prospect",    "label": "Follow-up sequence",         "output": "markdown"},
    {"name": "prep",       "arg_kind": "url",         "label": "Meeting prep brief",         "output": "markdown"},
    {"name": "proposal",   "arg_kind": "client",      "label": "Client proposal",            "output": "markdown"},
    {"name": "objections", "arg_kind": "topic",       "label": "Objection playbook",         "output": "markdown"},
    {"name": "icp",        "arg_kind": "description",  "label": "Ideal Customer Profile",     "output": "markdown"},
    {"name": "competitors","arg_kind": "url",         "label": "Competitive intel",          "output": "markdown"},
    {"name": "report",     "arg_kind": "none",        "label": "Pipeline report",            "output": "markdown"},
    {"name": "report-pdf", "arg_kind": "none",        "label": "Pipeline report (PDF)",      "output": "pdf"},
]

_BY_NAME = {c["name"]: c for c in COMMANDS}

def get_command(name: str):
    return _BY_NAME.get(name)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_commands.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/app/commands.py dashboard/backend/tests/test_commands.py
git commit -m "feat: command catalog for dashboard (14 sales commands)"
```

---

## Task 2: Input validation

**Files:**
- Create: `dashboard/backend/app/validation.py`
- Test: `dashboard/backend/tests/test_validation.py`

- [ ] **Step 1: Write the failing test**

`tests/test_validation.py`:
```python
import pytest
from app.validation import validate_command, validate_arg, ValidationError

def test_validate_command_accepts_known():
    assert validate_command("research") == "research"

def test_validate_command_rejects_unknown():
    with pytest.raises(ValidationError):
        validate_command("rm-rf")

def test_url_command_requires_url_shape():
    assert validate_arg("research", "https://acme.com") == "https://acme.com"
    with pytest.raises(ValidationError):
        validate_arg("research", "not a url")

def test_url_command_requires_nonempty():
    with pytest.raises(ValidationError):
        validate_arg("research", "")

def test_text_command_accepts_plain_text():
    assert validate_arg("icp", "B2B SaaS founders") == "B2B SaaS founders"

def test_none_command_ignores_arg():
    assert validate_arg("report", "anything") == ""

def test_arg_length_capped():
    with pytest.raises(ValidationError):
        validate_arg("icp", "x" * 2001)

def test_arg_is_trimmed():
    assert validate_arg("icp", "  hello  ") == "hello"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validation.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.validation'`)

- [ ] **Step 3: Write minimal implementation**

`app/validation.py`:
```python
from app.commands import get_command

MAX_ARG_LEN = 2000

class ValidationError(Exception):
    pass

def validate_command(name: str) -> str:
    if get_command(name) is None:
        raise ValidationError(f"Unknown command: {name!r}")
    return name

def validate_arg(command: str, arg: str) -> str:
    cmd = get_command(command)
    if cmd is None:
        raise ValidationError(f"Unknown command: {command!r}")
    if cmd["arg_kind"] == "none":
        return ""
    arg = (arg or "").strip()
    if not arg:
        raise ValidationError("This command needs an input.")
    if len(arg) > MAX_ARG_LEN:
        raise ValidationError("Input is too long.")
    if cmd["arg_kind"] == "url" and not (arg.startswith("http://") or arg.startswith("https://")):
        raise ValidationError("Please enter a full URL starting with https://")
    return arg
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_validation.py -v`
Expected: PASS (8 passed)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/app/validation.py dashboard/backend/tests/test_validation.py
git commit -m "feat: command + arg validation"
```

---

## Task 3: Daily run cap (file-backed, midnight reset)

**Files:**
- Create: `dashboard/backend/app/cap.py`
- Test: `dashboard/backend/tests/test_cap.py`

- [ ] **Step 1: Write the failing test**

`tests/test_cap.py`:
```python
from datetime import date
from app.cap import RunCap

def test_first_run_allowed(tmp_path):
    cap = RunCap(tmp_path / "cap.json", limit=2, today=lambda: date(2026, 6, 21))
    allowed, remaining = cap.try_consume()
    assert allowed is True
    assert remaining == 1

def test_cap_blocks_after_limit(tmp_path):
    cap = RunCap(tmp_path / "cap.json", limit=2, today=lambda: date(2026, 6, 21))
    cap.try_consume()
    cap.try_consume()
    allowed, remaining = cap.try_consume()
    assert allowed is False
    assert remaining == 0

def test_cap_resets_on_new_day(tmp_path):
    day = {"d": date(2026, 6, 21)}
    cap = RunCap(tmp_path / "cap.json", limit=1, today=lambda: day["d"])
    assert cap.try_consume()[0] is True
    assert cap.try_consume()[0] is False
    day["d"] = date(2026, 6, 22)
    assert cap.try_consume()[0] is True

def test_usage_reports_state_without_consuming(tmp_path):
    cap = RunCap(tmp_path / "cap.json", limit=5, today=lambda: date(2026, 6, 21))
    cap.try_consume()
    used, limit, remaining = cap.usage()
    assert (used, limit, remaining) == (1, 5, 4)
    # calling usage() again must not change the count
    assert cap.usage() == (1, 5, 4)

def test_state_persists_across_instances(tmp_path):
    path = tmp_path / "cap.json"
    RunCap(path, limit=3, today=lambda: date(2026, 6, 21)).try_consume()
    again = RunCap(path, limit=3, today=lambda: date(2026, 6, 21))
    assert again.usage() == (1, 3, 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cap.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.cap'`)

- [ ] **Step 3: Write minimal implementation**

`app/cap.py`:
```python
import json
from datetime import date
from pathlib import Path
from threading import Lock

class RunCap:
    """File-backed per-calendar-day run counter. Resets when the date changes."""

    def __init__(self, path, limit: int, today=date.today):
        self._path = Path(path)
        self._limit = limit
        self._today = today
        self._lock = Lock()

    def _load(self):
        try:
            data = json.loads(self._path.read_text())
        except (FileNotFoundError, ValueError):
            data = {}
        if data.get("date") != self._today().isoformat():
            data = {"date": self._today().isoformat(), "count": 0}
        return data

    def _save(self, data):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data))

    def try_consume(self):
        with self._lock:
            data = self._load()
            if data["count"] >= self._limit:
                self._save(data)
                return False, 0
            data["count"] += 1
            self._save(data)
            return True, self._limit - data["count"]

    def usage(self):
        with self._lock:
            data = self._load()
            self._save(data)
            used = data["count"]
            return used, self._limit, max(0, self._limit - used)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cap.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/app/cap.py dashboard/backend/tests/test_cap.py
git commit -m "feat: file-backed daily run cap"
```

---

## Task 4: Config (env-driven settings)

**Files:**
- Create: `dashboard/backend/app/config.py`
- Test: `dashboard/backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

`tests/test_config.py`:
```python
import pytest
from app.config import load_settings, ConfigError

def test_loads_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-x")
    monkeypatch.setenv("DASHBOARD_TOKEN", "tok123")
    monkeypatch.setenv("DAILY_CAP", "7")
    monkeypatch.setenv("SALES_REPO_DIR", str(tmp_path))
    monkeypatch.setenv("WORKSPACE_DIR", str(tmp_path / "ws"))
    s = load_settings()
    assert s.token == "tok123"
    assert s.daily_cap == 7
    assert s.api_key == "sk-ant-x"

def test_missing_key_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("DASHBOARD_TOKEN", "tok123")
    monkeypatch.setenv("SALES_REPO_DIR", str(tmp_path))
    with pytest.raises(ConfigError):
        load_settings()

def test_missing_token_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-x")
    monkeypatch.delenv("DASHBOARD_TOKEN", raising=False)
    monkeypatch.setenv("SALES_REPO_DIR", str(tmp_path))
    with pytest.raises(ConfigError):
        load_settings()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.config'`)

- [ ] **Step 3: Write minimal implementation**

`app/config.py`:
```python
import os
from dataclasses import dataclass
from pathlib import Path

class ConfigError(Exception):
    pass

@dataclass(frozen=True)
class Settings:
    api_key: str
    token: str
    daily_cap: int
    sales_repo_dir: Path
    workspace_dir: Path
    cap_file: Path

def load_settings() -> Settings:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    token = os.environ.get("DASHBOARD_TOKEN")
    if not api_key:
        raise ConfigError("ANTHROPIC_API_KEY is required")
    if not token:
        raise ConfigError("DASHBOARD_TOKEN is required")
    daily_cap = int(os.environ.get("DAILY_CAP", "20"))
    sales_repo_dir = Path(os.environ.get("SALES_REPO_DIR", "/app/salesagent"))
    workspace_dir = Path(os.environ.get("WORKSPACE_DIR", "/app/workspace"))
    return Settings(
        api_key=api_key,
        token=token,
        daily_cap=daily_cap,
        sales_repo_dir=sales_repo_dir,
        workspace_dir=workspace_dir,
        cap_file=workspace_dir / "cap.json",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/app/config.py dashboard/backend/tests/test_config.py
git commit -m "feat: env-driven settings"
```

---

## Task 5: Status mapping (SDK message -> friendly progress text)

**Files:**
- Create: `dashboard/backend/app/status_map.py`
- Test: `dashboard/backend/tests/test_status_map.py`

- [ ] **Step 1: Write the failing test**

`tests/test_status_map.py`:
```python
from app.status_map import friendly_status

def test_tool_use_web_maps_to_research():
    assert friendly_status({"type": "tool_use", "name": "WebSearch"}) == "Researching the web…"
    assert friendly_status({"type": "tool_use", "name": "WebFetch"}) == "Researching the web…"

def test_subagent_maps_to_analyzing():
    assert friendly_status({"type": "tool_use", "name": "Task"}) == "Running research agents…"

def test_script_maps_to_scoring():
    assert friendly_status({"type": "tool_use", "name": "Bash"}) == "Crunching numbers…"

def test_write_maps_to_writing():
    assert friendly_status({"type": "tool_use", "name": "Write"}) == "Writing the report…"

def test_text_message_maps_to_thinking():
    assert friendly_status({"type": "text"}) == "Thinking…"

def test_unknown_returns_none():
    assert friendly_status({"type": "tool_use", "name": "SomethingElse"}) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_status_map.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.status_map'`)

- [ ] **Step 3: Write minimal implementation**

`app/status_map.py`:
```python
"""Translate raw Agent SDK activity into short, non-technical progress lines."""

_TOOL_STATUS = {
    "WebSearch": "Researching the web…",
    "WebFetch": "Researching the web…",
    "Task": "Running research agents…",
    "Bash": "Crunching numbers…",
    "Write": "Writing the report…",
}

def friendly_status(event: dict):
    etype = event.get("type")
    if etype == "text":
        return "Thinking…"
    if etype == "tool_use":
        return _TOOL_STATUS.get(event.get("name"))
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_status_map.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/app/status_map.py dashboard/backend/tests/test_status_map.py
git commit -m "feat: friendly status mapping for SDK activity"
```

---

## Task 6: Runner (Claude Agent SDK execution)

**Files:**
- Create: `dashboard/backend/app/runner.py`
- Test: `dashboard/backend/tests/test_runner_integration.py`

> Uses the SDK symbols confirmed in Task 0 Step 5. If they differ, adjust the import + call here.

- [ ] **Step 1: Write the integration test (opt-in)**

`tests/test_runner_integration.py`:
```python
import os
import pytest
from pathlib import Path
from app.runner import run_command

pytestmark = pytest.mark.integration

@pytest.mark.skipif(os.environ.get("RUN_INTEGRATION") != "1",
                    reason="set RUN_INTEGRATION=1 and ANTHROPIC_API_KEY to run")
async def test_icp_produces_markdown(tmp_path):
    sales_repo = Path(os.environ["SALES_REPO_DIR"])
    events = []
    final = None
    async for ev in run_command("icp", "B2B SaaS founders selling to SMBs",
                                sales_repo_dir=sales_repo, workspace_dir=tmp_path):
        events.append(ev)
        if ev["kind"] == "result":
            final = ev
    assert final is not None
    assert final["output"]            # non-empty markdown
    assert any(e["kind"] == "status" for e in events)
```

- [ ] **Step 2: Run test to verify it is collected and skipped**

Run: `pytest tests/test_runner_integration.py -v`
Expected: SKIPPED (1 skipped) when `RUN_INTEGRATION` is unset — confirms it imports cleanly.

- [ ] **Step 3: Write the implementation**

`app/runner.py`:
```python
"""Execute a /sales command via the Claude Agent SDK, yielding progress + result.

Yields dict events:
  {"kind": "status", "text": "Researching the web…"}
  {"kind": "result", "output": "<markdown>", "files": ["PROSPECT-ANALYSIS.md"]}
  {"kind": "error",  "message": "..."}
"""
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions  # confirmed in Task 0
from app.status_map import friendly_status

_PROMPT = (
    "Run the `/sales {command}` command"
    "{arg_clause}. "
    "Use the sales skill. Produce the documented output file in the current "
    "working directory and end your final message with the full markdown content "
    "of that output between <OUTPUT> and </OUTPUT> tags."
)

def _build_prompt(command: str, arg: str) -> str:
    arg_clause = f" with input: {arg}" if arg else ""
    return _PROMPT.format(command=command, arg_clause=arg_clause)

def _extract_output(text: str) -> str:
    start, end = text.find("<OUTPUT>"), text.rfind("</OUTPUT>")
    if start != -1 and end != -1 and end > start:
        return text[start + len("<OUTPUT>"):end].strip()
    return text.strip()

async def run_command(command, arg, *, sales_repo_dir: Path, workspace_dir: Path):
    workspace_dir.mkdir(parents=True, exist_ok=True)
    options = ClaudeAgentOptions(
        cwd=str(workspace_dir),
        permission_mode="bypassPermissions",
        setting_sources=["user", "project"],
        add_dirs=[str(sales_repo_dir)],
    )
    last_text = ""
    try:
        async for message in query(prompt=_build_prompt(command, arg), options=options):
            for ev in _iter_blocks(message):
                status = friendly_status(ev)
                if status:
                    yield {"kind": "status", "text": status}
                if ev.get("type") == "text":
                    last_text = ev.get("text", last_text) or last_text
    except Exception as exc:  # surface as a structured error event
        yield {"kind": "error", "message": str(exc)}
        return
    files = sorted(p.name for p in workspace_dir.glob("*.md")) + \
            sorted(p.name for p in workspace_dir.glob("*.pdf"))
    yield {"kind": "result", "output": _extract_output(last_text), "files": files}

def _iter_blocks(message):
    """Normalize an SDK message into {'type','name'/'text'} dicts.

    Tolerant of SDK shape: messages may carry a `.content` list of blocks with
    `.type`, `.name` (tool_use) or `.text` (text). Adjust to the confirmed shape
    from Task 0 if attribute names differ.
    """
    content = getattr(message, "content", None)
    if content is None:
        return
    for block in content:
        btype = getattr(block, "type", None) or getattr(type(block), "__name__", "").lower()
        if "tooluse" in str(btype).lower() or btype == "tool_use":
            yield {"type": "tool_use", "name": getattr(block, "name", "")}
        elif "text" in str(btype).lower() or btype == "text":
            yield {"type": "text", "text": getattr(block, "text", "")}
```

- [ ] **Step 4: Run integration test for real (manual, optional, costs API money)**

Run:
```bash
RUN_INTEGRATION=1 SALES_REPO_DIR=$HOME/Documents/Projects/SalesAgent_Claude \
  ANTHROPIC_API_KEY=sk-ant-... pytest tests/test_runner_integration.py -v -m integration
```
Expected: PASS — confirms the SDK loads the sales skill and returns markdown. If block/message attribute names differ, fix `_iter_blocks` and re-run.

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/app/runner.py dashboard/backend/tests/test_runner_integration.py
git commit -m "feat: Claude Agent SDK runner for sales commands"
```

---

## Task 7: Run registry (in-memory jobs + SSE queues)

**Files:**
- Create: `dashboard/backend/app/runs.py`
- Test: `dashboard/backend/tests/test_runs.py`

- [ ] **Step 1: Write the failing test**

`tests/test_runs.py`:
```python
import asyncio
import pytest
from app.runs import RunRegistry

async def _producer(reg, run_id):
    await reg.publish(run_id, {"kind": "status", "text": "go"})
    await reg.publish(run_id, {"kind": "result", "output": "done", "files": []})
    await reg.close(run_id)

async def test_subscribe_receives_published_events():
    reg = RunRegistry()
    run_id = reg.create()
    asyncio.create_task(_producer(reg, run_id))
    got = [ev async for ev in reg.subscribe(run_id)]
    assert got[0] == {"kind": "status", "text": "go"}
    assert got[-1]["kind"] == "result"

async def test_unknown_run_subscribe_raises():
    reg = RunRegistry()
    with pytest.raises(KeyError):
        async for _ in reg.subscribe("nope"):
            pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_runs.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.runs'`)

- [ ] **Step 3: Write minimal implementation**

`app/runs.py`:
```python
import asyncio
import uuid

_SENTINEL = object()

class RunRegistry:
    """Tracks in-flight runs and fans out their events to one SSE subscriber."""

    def __init__(self):
        self._queues = {}

    def create(self) -> str:
        run_id = uuid.uuid4().hex
        self._queues[run_id] = asyncio.Queue()
        return run_id

    async def publish(self, run_id: str, event: dict):
        self._queues[run_id].put_nowait(event)

    async def close(self, run_id: str):
        self._queues[run_id].put_nowait(_SENTINEL)

    async def subscribe(self, run_id: str):
        if run_id not in self._queues:
            raise KeyError(run_id)
        queue = self._queues[run_id]
        try:
            while True:
                item = await queue.get()
                if item is _SENTINEL:
                    return
                yield item
        finally:
            self._queues.pop(run_id, None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_runs.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/app/runs.py dashboard/backend/tests/test_runs.py
git commit -m "feat: in-memory run registry with SSE fan-out"
```

---

## Task 8: FastAPI app (routes, token gate, SSE, static)

**Files:**
- Create: `dashboard/backend/app/main.py`
- Test: `dashboard/backend/tests/test_api.py`

- [ ] **Step 1: Write the failing test (fake runner injected)**

`tests/test_api.py`:
```python
import os
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-x")
    monkeypatch.setenv("DASHBOARD_TOKEN", "secret-tok")
    monkeypatch.setenv("DAILY_CAP", "2")
    monkeypatch.setenv("SALES_REPO_DIR", str(tmp_path))
    monkeypatch.setenv("WORKSPACE_DIR", str(tmp_path / "ws"))
    from importlib import reload
    import app.main as m
    reload(m)

    async def fake_runner(command, arg, *, sales_repo_dir, workspace_dir):
        yield {"kind": "status", "text": "Thinking…"}
        yield {"kind": "result", "output": f"# {command} {arg}", "files": []}

    m.app.state.runner = fake_runner
    return m.app

async def _client(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://t")

async def test_run_rejects_bad_token(app):
    async with await _client(app) as c:
        r = await c.post("/api/run", json={"command": "research", "arg": "https://a.com"},
                         headers={"X-Dashboard-Token": "wrong"})
    assert r.status_code == 403

async def test_run_rejects_unknown_command(app):
    async with await _client(app) as c:
        r = await c.post("/api/run", json={"command": "danger", "arg": "x"},
                         headers={"X-Dashboard-Token": "secret-tok"})
    assert r.status_code == 400

async def test_run_returns_run_id(app):
    async with await _client(app) as c:
        r = await c.post("/api/run", json={"command": "research", "arg": "https://a.com"},
                         headers={"X-Dashboard-Token": "secret-tok"})
    assert r.status_code == 200
    assert "run_id" in r.json()

async def test_cap_enforced(app):
    headers = {"X-Dashboard-Token": "secret-tok"}
    body = {"command": "research", "arg": "https://a.com"}
    async with await _client(app) as c:
        assert (await c.post("/api/run", json=body, headers=headers)).status_code == 200
        assert (await c.post("/api/run", json=body, headers=headers)).status_code == 200
        r = await c.post("/api/run", json=body, headers=headers)
    assert r.status_code == 429

async def test_usage_endpoint(app):
    async with await _client(app) as c:
        r = await c.get("/api/usage", headers={"X-Dashboard-Token": "secret-tok"})
    assert r.status_code == 200
    assert set(r.json()) == {"used", "limit", "remaining"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.main'`)

- [ ] **Step 3: Write minimal implementation**

`app/main.py`:
```python
import asyncio
import json
import secrets
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from app.config import load_settings
from app.validation import validate_command, validate_arg, ValidationError
from app.cap import RunCap
from app.runs import RunRegistry
from app.runner import run_command

settings = load_settings()
app = FastAPI()
app.state.settings = settings
app.state.cap = RunCap(settings.cap_file, settings.daily_cap)
app.state.registry = RunRegistry()
app.state.runner = run_command  # overridable in tests

def _check_token(request: Request):
    supplied = request.headers.get("X-Dashboard-Token") or request.query_params.get("token")
    if not supplied or not secrets.compare_digest(supplied, settings.token):
        raise HTTPException(status_code=403, detail="not found")

@app.post("/api/run")
async def start_run(request: Request):
    _check_token(request)
    body = await request.json()
    try:
        command = validate_command(body.get("command", ""))
        arg = validate_arg(command, body.get("arg", ""))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    allowed, _ = app.state.cap.try_consume()
    if not allowed:
        raise HTTPException(status_code=429, detail="Daily limit reached — please try again tomorrow.")

    registry: RunRegistry = app.state.registry
    run_id = registry.create()

    async def drive():
        try:
            async for ev in app.state.runner(
                command, arg,
                sales_repo_dir=settings.sales_repo_dir,
                workspace_dir=settings.workspace_dir,
            ):
                await registry.publish(run_id, ev)
        except Exception as exc:
            await registry.publish(run_id, {"kind": "error", "message": str(exc)})
        finally:
            await registry.close(run_id)

    asyncio.create_task(drive())
    return {"run_id": run_id}

@app.get("/api/status/{run_id}")
async def status(run_id: str, request: Request):
    _check_token(request)
    registry: RunRegistry = app.state.registry

    async def event_stream():
        try:
            async for ev in registry.subscribe(run_id):
                yield {"data": json.dumps(ev)}
        except KeyError:
            yield {"data": json.dumps({"kind": "error", "message": "Unknown run."})}

    return EventSourceResponse(event_stream())

@app.get("/api/usage")
async def usage(request: Request):
    _check_token(request)
    used, limit, remaining = app.state.cap.usage()
    return {"used": used, "limit": limit, "remaining": remaining}

@app.get("/api/download/{name}")
async def download(name: str, request: Request):
    _check_token(request)
    safe = Path(name).name  # strip any path components
    target = settings.workspace_dir / safe
    if not target.exists():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(target, filename=safe)

# Static frontend served at /d/{token}/... ; index handled by the page itself.
_frontend = Path(__file__).resolve().parents[2] / "frontend"
if _frontend.exists():
    app.mount("/d", StaticFiles(directory=_frontend, html=True), name="frontend")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Run the full suite**

Run: `pytest -v`
Expected: all unit tests PASS; integration test SKIPPED.

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/app/main.py dashboard/backend/tests/test_api.py
git commit -m "feat: FastAPI routes, token gate, SSE, cap enforcement"
```

---

## Task 9: Frontend (single page)

**Files:**
- Create: `dashboard/frontend/index.html`
- Create: `dashboard/frontend/styles.css`
- Create: `dashboard/frontend/app.js`

> The frontend reads the token from its own URL path (`/d/<token>/`) and sends it
> as `X-Dashboard-Token`. Manual acceptance is covered in Task 11.

- [ ] **Step 1: Create index.html**

`frontend/index.html`:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex, nofollow" />
  <title>Sales Assistant</title>
  <link rel="stylesheet" href="styles.css" />
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
  <header>
    <h1>Sales Assistant</h1>
    <p id="usage" class="usage"></p>
  </header>

  <main>
    <section class="picker">
      <label for="command">Pick what you want to do</label>
      <select id="command"></select>
      <div id="argRow" class="arg-row">
        <input id="arg" type="text" placeholder="" />
      </div>
      <button id="run">Run</button>
    </section>

    <section id="statusBox" class="status hidden">
      <span class="spinner"></span>
      <span id="statusText">Starting…</span>
    </section>

    <section id="errorBox" class="error hidden"></section>

    <section id="outputBox" class="output hidden">
      <div class="output-actions">
        <a id="download" href="#" download>Download</a>
      </div>
      <article id="output" class="markdown"></article>
    </section>
  </main>

  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create styles.css**

`frontend/styles.css`:
```css
:root { --bg:#0f172a; --card:#1e293b; --ink:#e2e8f0; --accent:#38bdf8; --muted:#94a3b8; }
* { box-sizing: border-box; }
body { margin:0; font-family: system-ui, sans-serif; background:var(--bg); color:var(--ink); }
header { padding:24px; display:flex; justify-content:space-between; align-items:baseline; }
h1 { margin:0; font-size:20px; }
.usage { color:var(--muted); font-size:13px; }
main { max-width:820px; margin:0 auto; padding:0 24px 48px; }
.picker { background:var(--card); padding:20px; border-radius:12px; display:flex; flex-direction:column; gap:12px; }
select, input, button { font-size:16px; padding:12px; border-radius:8px; border:1px solid #334155; background:#0b1220; color:var(--ink); }
button { background:var(--accent); color:#04243a; font-weight:600; border:none; cursor:pointer; }
button:disabled { opacity:.5; cursor:not-allowed; }
.arg-row.hidden { display:none; }
.status { margin-top:20px; display:flex; align-items:center; gap:10px; color:var(--muted); }
.spinner { width:16px; height:16px; border:2px solid #334155; border-top-color:var(--accent); border-radius:50%; animation:spin 1s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
.error { margin-top:20px; padding:14px; border-radius:8px; background:#7f1d1d; color:#fee2e2; }
.output { margin-top:24px; background:var(--card); border-radius:12px; padding:20px; }
.output-actions { text-align:right; margin-bottom:12px; }
.output-actions a { color:var(--accent); }
.markdown { line-height:1.6; }
.markdown h1,.markdown h2 { border-bottom:1px solid #334155; padding-bottom:6px; }
.markdown table { border-collapse:collapse; width:100%; }
.markdown td,.markdown th { border:1px solid #334155; padding:6px 10px; }
.hidden { display:none; }
```

- [ ] **Step 3: Create app.js**

`frontend/app.js`:
```javascript
// Token is the path segment after /d/ : /d/<token>/index.html
const TOKEN = location.pathname.split("/").filter(Boolean)[1] || "";
const API = "/api";
const headers = { "Content-Type": "application/json", "X-Dashboard-Token": TOKEN };

const COMMANDS = [
  ["prospect","Full prospect audit","url"],
  ["quick","60-second snapshot","url"],
  ["research","Company research","url"],
  ["qualify","Lead qualification (BANT/MEDDIC)","url"],
  ["contacts","Find decision makers","url"],
  ["outreach","Cold outreach emails","prospect"],
  ["followup","Follow-up emails","prospect"],
  ["prep","Meeting prep brief","url"],
  ["proposal","Client proposal","client"],
  ["objections","Objection playbook","topic"],
  ["icp","Ideal Customer Profile","description"],
  ["competitors","Competitive intel","url"],
  ["report","Pipeline report","none"],
  ["report-pdf","Pipeline report (PDF)","none"],
];
const PLACEHOLDER = {
  url:"Paste a company or LinkedIn URL (https://…)",
  prospect:"Prospect or company name",
  client:"Client name",
  topic:"Objection topic (e.g. pricing)",
  description:"Describe your ideal customer",
};

const $ = (id) => document.getElementById(id);
const select = $("command"), argRow = $("argRow"), argInput = $("arg"), runBtn = $("run");

COMMANDS.forEach(([name, label]) => {
  const o = document.createElement("option");
  o.value = name; o.textContent = label; select.appendChild(o);
});

function syncArgRow() {
  const kind = COMMANDS.find(c => c[0] === select.value)[2];
  if (kind === "none") { argRow.classList.add("hidden"); }
  else { argRow.classList.remove("hidden"); argInput.placeholder = PLACEHOLDER[kind]; argInput.value = ""; }
}
select.addEventListener("change", syncArgRow);
syncArgRow();

async function refreshUsage() {
  try {
    const r = await fetch(`${API}/usage`, { headers });
    if (!r.ok) return;
    const u = await r.json();
    $("usage").textContent = `${u.remaining} of ${u.limit} runs left today`;
  } catch (_) {}
}
refreshUsage();

function show(id) { $(id).classList.remove("hidden"); }
function hide(id) { $(id).classList.add("hidden"); }

runBtn.addEventListener("click", async () => {
  hide("errorBox"); hide("outputBox"); show("statusBox");
  $("statusText").textContent = "Starting…";
  runBtn.disabled = true;

  let res;
  try {
    res = await fetch(`${API}/run`, {
      method: "POST", headers,
      body: JSON.stringify({ command: select.value, arg: argInput.value }),
    });
  } catch (e) { return fail("Network error — please try again."); }

  if (res.status === 429) return fail("Daily limit reached — please try again tomorrow.");
  if (res.status === 400) return fail((await res.json()).detail || "Please check your input.");
  if (!res.ok) return fail("Something went wrong — please try again.");

  const { run_id } = await res.json();
  const ev = new EventSource(`${API}/status/${run_id}?token=${encodeURIComponent(TOKEN)}`);
  ev.onmessage = (m) => {
    const data = JSON.parse(m.data);
    if (data.kind === "status") { $("statusText").textContent = data.text; }
    else if (data.kind === "error") { ev.close(); fail(data.message || "Something went wrong."); }
    else if (data.kind === "result") {
      ev.close(); hide("statusBox"); show("outputBox");
      $("output").innerHTML = marked.parse(data.output || "_No output._");
      setupDownload(data);
      runBtn.disabled = false; refreshUsage();
    }
  };
  ev.onerror = () => { ev.close(); fail("Connection lost — please try again."); };
});

function setupDownload(data) {
  const dl = $("download");
  const pdf = (data.files || []).find(f => f.endsWith(".pdf"));
  if (pdf) { dl.href = `${API}/download/${encodeURIComponent(pdf)}?token=${encodeURIComponent(TOKEN)}`; dl.textContent = "Download PDF"; dl.classList.remove("hidden"); return; }
  const blob = new Blob([data.output || ""], { type: "text/markdown" });
  dl.href = URL.createObjectURL(blob); dl.download = `${select.value}.md`; dl.textContent = "Download .md"; dl.classList.remove("hidden");
}

function fail(msg) {
  hide("statusBox"); show("errorBox"); $("errorBox").textContent = msg; runBtn.disabled = false;
}
```

- [ ] **Step 4: Manual smoke (local, fake key not needed for static)**

Run: `cd dashboard/backend && . .venv/bin/activate && DASHBOARD_TOKEN=devtok ANTHROPIC_API_KEY=x SALES_REPO_DIR=$HOME/Documents/Projects/SalesAgent_Claude WORKSPACE_DIR=/tmp/ws uvicorn app.main:app --reload`
Open: `http://localhost:8000/d/devtok/` — confirm the page renders, dropdown lists 14 commands, the input box hides for `report`/`report-pdf`.

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/
git commit -m "feat: dashboard frontend (single page)"
```

---

## Task 10: Containerization + deploy config

**Files:**
- Create: `dashboard/Dockerfile`
- Create: `dashboard/railway.json`

- [ ] **Step 1: Create Dockerfile**

`dashboard/Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Node is needed by the Claude Agent SDK CLI runtime
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Bring in the sales skills repo and install the skills for the Agent SDK
COPY salesagent /app/salesagent
RUN bash /app/salesagent/install.sh || true

COPY backend /app/backend
COPY frontend /app/frontend

ENV SALES_REPO_DIR=/app/salesagent \
    WORKSPACE_DIR=/app/workspace \
    PYTHONPATH=/app/backend
RUN mkdir -p /app/workspace

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000"]
```

> **Build context note:** the Dockerfile expects `salesagent/` next to `backend/`
> and `frontend/`. The build step (Task 11) copies/symlinks the repo into the
> build context, or the deploy uses the repo root as context with adjusted paths.

- [ ] **Step 2: Create railway.json**

`dashboard/railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": { "builder": "DOCKERFILE", "dockerfilePath": "dashboard/Dockerfile" },
  "deploy": { "restartPolicyType": "ON_FAILURE", "healthcheckPath": "/api/usage" }
}
```

- [ ] **Step 3: Local container smoke**

Run:
```bash
cd dashboard && cp -R "$HOME/Documents/Projects/SalesAgent_Claude" ./salesagent 2>/dev/null; \
docker build -t sales-dash -f Dockerfile . && \
docker run --rm -p 8000:8000 -e ANTHROPIC_API_KEY=x -e DASHBOARD_TOKEN=devtok sales-dash &
sleep 5 && curl -s -H "X-Dashboard-Token: devtok" localhost:8000/api/usage
```
Expected: JSON `{"used":0,"limit":20,"remaining":20}`. Then stop the container.

- [ ] **Step 4: Commit**

```bash
git add dashboard/Dockerfile dashboard/railway.json
echo "dashboard/salesagent/" >> .gitignore && git add .gitignore
git commit -m "feat: Dockerfile + Railway deploy config"
```

---

## Task 11: Deploy + acceptance + README

**Files:**
- Create: `dashboard/README.md`

- [ ] **Step 1: Write README**

`dashboard/README.md`:
```markdown
# Sales Dashboard

A no-password web page so a non-technical user can run the `/sales` commands.

## How it works
A FastAPI backend runs the real sales skills via the Claude Agent SDK and streams
progress + the final report to a single web page. Access is gated by an
unguessable URL token; spend is bounded by a daily run cap.

## Deploy (Railway)
1. Create a Railway project from this repo; set the Dockerfile path to
   `dashboard/Dockerfile`.
2. Set environment variables:
   - `ANTHROPIC_API_KEY` — your key (billing enabled).
   - `DASHBOARD_TOKEN` — a long random string (e.g. `openssl rand -hex 16`).
   - `DAILY_CAP` — e.g. `20`.
3. Deploy. The public URL for Lucas is:
   `https://<your-app>.up.railway.app/d/<DASHBOARD_TOKEN>/`
4. Send Lucas that single link. No login, no GitHub.

## Cost controls
- Daily cap stops spend after N runs/day.
- The token keeps the URL un-findable (rotate it by changing `DASHBOARD_TOKEN`).
- `prospect` launches 5 research agents — the most expensive command.
```

- [ ] **Step 2: Generate a real token**

Run: `openssl rand -hex 16`
Use the output as `DASHBOARD_TOKEN` in Railway.

- [ ] **Step 3: Deploy to Railway**

Push the branch, connect Railway, set the three env vars, deploy. Confirm the
build runs `install.sh` and the service becomes healthy (`/api/usage` returns 200).

- [ ] **Step 4: Live acceptance from a phone/incognito browser**

- Open `https://<app>/d/<token>/` — page loads, dropdown shows 14 commands.
- Run `research` with a real company URL — live status updates, markdown renders.
- Run `report-pdf` — a **Download PDF** button appears and downloads a PDF.
- Open the URL **without** the token (`/d/`) — confirm it does not expose the app.
- Run until the daily cap trips — confirm the friendly "try again tomorrow" message.

- [ ] **Step 5: Commit**

```bash
git add dashboard/README.md
git commit -m "docs: dashboard deploy + acceptance guide"
```

---

## Self-Review Notes (completed)

- **Spec coverage:** live runs (Task 6), cloud host/Docker (Tasks 10–11), daily cap
  (Task 3 + enforced Task 8), URL token (Task 8 + 11), Anthropic key (Task 4),
  all 14 commands (Task 1 + frontend Task 9), SSE progress (Tasks 5/7/8/9),
  adaptive input (Task 9), markdown render + PDF download (Task 9), pipeline state
  for report commands (workspace dir, Tasks 4/6/8), error handling (Tasks 6/8/9).
- **Placeholders:** none — every code step shows full code.
- **Type consistency:** event shape `{"kind": "status|result|error", ...}` is
  identical across runner (Task 6), registry (Task 7), API (Task 8), and frontend
  (Task 9). `RunCap.try_consume()/usage()` signatures match across Tasks 3/8.
- **Known external-API risk:** the Agent SDK symbol/message shape is verified in
  Task 0 Step 5 and Task 6 Step 4 before the runner is finalized — the one place
  reality must be confirmed against the installed package.
```
