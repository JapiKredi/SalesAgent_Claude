import asyncio
import json
import os
import secrets
from pathlib import Path

# Subscription-only by design: never use API-key billing. Drop any ambient
# ANTHROPIC_API_KEY so the SDK/CLI authenticates via the logged-in `claude`
# session (Claude Max) instead. Runs then cost nothing per token.
os.environ.pop("ANTHROPIC_API_KEY", None)

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
app.state.runner = run_command          # overridable in tests
app.state.tasks = set()                 # hold task refs so they aren't GC'd
app.state.inflight = 0                  # concurrency guard

_FRONTEND = Path(__file__).resolve().parents[2] / "frontend"

def _check_token(request: Request):
    supplied = request.headers.get("X-Dashboard-Token") or request.query_params.get("token")
    if not supplied or not secrets.compare_digest(supplied, settings.token):
        raise HTTPException(status_code=403, detail="not found")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/d/{token}/")
async def dashboard_page(token: str):
    if not secrets.compare_digest(token, settings.token):
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(_FRONTEND / "index.html")

@app.post("/api/run")
async def start_run(request: Request):
    _check_token(request)
    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError("body must be an object")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request.")
    try:
        command = validate_command(body.get("command", ""))
        arg = validate_arg(command, body.get("arg", ""))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if app.state.inflight >= settings.max_concurrent:
        raise HTTPException(status_code=429, detail="A run is already in progress — please wait for it to finish.")

    allowed, _ = app.state.cap.try_consume()
    if not allowed:
        raise HTTPException(status_code=429, detail="Daily limit reached — please try again tomorrow.")

    registry: RunRegistry = app.state.registry
    run_id = registry.create()
    run_dir = settings.runs_dir / run_id
    app.state.inflight += 1

    async def drive():
        errored = False
        try:
            async for ev in app.state.runner(
                command, arg,
                sales_repo_dir=settings.sales_repo_dir,
                run_dir=run_dir,
                pipeline_dir=settings.pipeline_dir,
                max_turns=settings.max_turns,
                model=settings.model,
            ):
                if ev.get("kind") == "error":
                    errored = True
                await registry.publish(run_id, ev)
        except Exception as exc:
            errored = True
            await registry.publish(run_id, {"kind": "error", "message": str(exc)})
        finally:
            if errored:
                app.state.cap.refund()      # don't burn a slot on failure
            app.state.inflight -= 1
            await registry.close(run_id)

    task = asyncio.create_task(drive())
    app.state.tasks.add(task)
    task.add_done_callback(app.state.tasks.discard)
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
            yield {"data": json.dumps({"kind": "error", "message": "Unknown or expired run."})}

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
    target = settings.pipeline_dir / safe
    if not target.exists():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(target, filename=safe)

# Static assets (css/js) — no secrets here, served unauthenticated at /static.
if _FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=_FRONTEND), name="static")
