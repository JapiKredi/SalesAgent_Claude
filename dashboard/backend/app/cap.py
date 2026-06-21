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

    def refund(self):
        with self._lock:
            data = self._load()
            if data["count"] > 0:
                data["count"] -= 1
            self._save(data)

    def usage(self):
        with self._lock:
            data = self._load()
            self._save(data)
            used = data["count"]
            return used, self._limit, max(0, self._limit - used)
