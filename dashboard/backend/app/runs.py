import asyncio
import time
import uuid

class RunRegistry:
    """Tracks runs and their events, with replay so a dropped SSE stream can
    reconnect and resume. Each run keeps an append-only event log; subscribe()
    replays everything so far, then streams new events until the run closes.

    A run's log is retained for `retain` seconds after it closes (so a reconnect
    right after completion still gets the result), then reaped on the next create().
    This is what makes long runs survive flaky connections / tunnels.
    """

    def __init__(self, now=time.monotonic, retain: float = 600.0):
        self._runs = {}   # run_id -> {events, closed, cond, ts}
        self._now = now
        self._retain = retain

    def _sweep(self):
        cutoff = self._now() - self._retain
        for rid in [r for r, v in self._runs.items() if v["closed"] and v["ts"] < cutoff]:
            self._runs.pop(rid, None)

    def create(self) -> str:
        self._sweep()
        run_id = uuid.uuid4().hex
        self._runs[run_id] = {
            "events": [],
            "closed": False,
            "cond": asyncio.Condition(),
            "ts": self._now(),
        }
        return run_id

    async def publish(self, run_id: str, event: dict):
        run = self._runs.get(run_id)
        if run is None:
            return
        async with run["cond"]:
            run["events"].append(event)
            run["ts"] = self._now()
            run["cond"].notify_all()

    async def close(self, run_id: str):
        run = self._runs.get(run_id)
        if run is None:
            return
        async with run["cond"]:
            run["closed"] = True
            run["ts"] = self._now()
            run["cond"].notify_all()

    async def subscribe(self, run_id: str):
        run = self._runs.get(run_id)
        if run is None:
            raise KeyError(run_id)
        idx = 0
        while True:
            async with run["cond"]:
                while idx >= len(run["events"]) and not run["closed"]:
                    await run["cond"].wait()
                new = run["events"][idx:]
                idx += len(new)
                done = run["closed"] and idx >= len(run["events"])
            for ev in new:
                yield ev
            if done:
                return
