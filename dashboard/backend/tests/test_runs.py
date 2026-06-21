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

async def test_stale_runs_are_swept_on_create():
    clock = {"t": 1000.0}
    reg = RunRegistry(now=lambda: clock["t"], max_age=100.0)
    old = reg.create()
    clock["t"] = 2000.0           # advance well past max_age
    reg.create()                  # triggers sweep of `old`
    with pytest.raises(KeyError):
        async for _ in reg.subscribe(old):
            pass
