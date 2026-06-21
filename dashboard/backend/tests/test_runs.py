import asyncio
import pytest
from app.runs import RunRegistry

async def test_replays_events_published_before_subscribe():
    reg = RunRegistry()
    rid = reg.create()
    await reg.publish(rid, {"kind": "status", "text": "a"})
    await reg.publish(rid, {"kind": "result", "output": "done", "files": []})
    await reg.close(rid)
    got = [ev async for ev in reg.subscribe(rid)]
    assert [e["kind"] for e in got] == ["status", "result"]

async def test_second_subscriber_gets_full_history_replay():
    # Reconnect after a dropped stream must replay everything, not error.
    reg = RunRegistry()
    rid = reg.create()
    await reg.publish(rid, {"kind": "status", "text": "a"})
    await reg.close(rid)
    first = [ev async for ev in reg.subscribe(rid)]
    second = [ev async for ev in reg.subscribe(rid)]
    assert first == second == [{"kind": "status", "text": "a"}]

async def test_live_events_stream_until_close():
    reg = RunRegistry()
    rid = reg.create()
    async def produce():
        await reg.publish(rid, {"kind": "status", "text": "go"})
        await reg.publish(rid, {"kind": "result", "output": "x", "files": []})
        await reg.close(rid)
    asyncio.create_task(produce())
    got = [ev async for ev in reg.subscribe(rid)]
    assert got[-1]["kind"] == "result"

async def test_unknown_run_raises():
    reg = RunRegistry()
    with pytest.raises(KeyError):
        async for _ in reg.subscribe("nope"):
            pass

async def test_closed_runs_swept_after_retain():
    clock = {"t": 1000.0}
    reg = RunRegistry(now=lambda: clock["t"], retain=100.0)
    rid = reg.create()
    await reg.close(rid)
    clock["t"] = 2000.0          # past retain window
    reg.create()                 # triggers sweep of the closed run
    with pytest.raises(KeyError):
        async for _ in reg.subscribe(rid):
            pass
