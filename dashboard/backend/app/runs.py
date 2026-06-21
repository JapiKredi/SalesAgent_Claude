import asyncio
import time
import uuid

_SENTINEL = object()

class RunRegistry:
    """Tracks in-flight runs and fans out their events to one SSE subscriber.

    Abandoned runs (client never subscribes) are reaped opportunistically on the
    next create() once older than max_age, so queues can't accumulate forever.
    """

    def __init__(self, now=time.monotonic, max_age: float = 3600.0):
        self._queues = {}
        self._created = {}
        self._now = now
        self._max_age = max_age

    def _sweep(self):
        cutoff = self._now() - self._max_age
        for rid in [r for r, t in self._created.items() if t < cutoff]:
            self._queues.pop(rid, None)
            self._created.pop(rid, None)

    def create(self) -> str:
        self._sweep()
        run_id = uuid.uuid4().hex
        self._queues[run_id] = asyncio.Queue()
        self._created[run_id] = self._now()
        return run_id

    async def publish(self, run_id: str, event: dict):
        q = self._queues.get(run_id)
        if q is not None:
            q.put_nowait(event)

    async def close(self, run_id: str):
        q = self._queues.get(run_id)
        if q is not None:
            q.put_nowait(_SENTINEL)

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
            self._created.pop(run_id, None)
