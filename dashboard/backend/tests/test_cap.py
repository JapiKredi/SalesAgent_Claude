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

def test_refund_returns_a_slot(tmp_path):
    cap = RunCap(tmp_path / "cap.json", limit=2, today=lambda: date(2026, 6, 21))
    cap.try_consume()
    cap.refund()
    assert cap.usage() == (0, 2, 2)

def test_refund_never_goes_negative(tmp_path):
    cap = RunCap(tmp_path / "cap.json", limit=2, today=lambda: date(2026, 6, 21))
    cap.refund()
    assert cap.usage() == (0, 2, 2)

def test_usage_reports_state_without_consuming(tmp_path):
    cap = RunCap(tmp_path / "cap.json", limit=5, today=lambda: date(2026, 6, 21))
    cap.try_consume()
    assert cap.usage() == (1, 5, 4)
    assert cap.usage() == (1, 5, 4)

def test_state_persists_across_instances(tmp_path):
    path = tmp_path / "cap.json"
    RunCap(path, limit=3, today=lambda: date(2026, 6, 21)).try_consume()
    again = RunCap(path, limit=3, today=lambda: date(2026, 6, 21))
    assert again.usage() == (1, 3, 2)
