import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-x")
    monkeypatch.setenv("DASHBOARD_TOKEN", "secret-tok")
    monkeypatch.setenv("DAILY_CAP", "2")
    monkeypatch.setenv("MAX_CONCURRENT", "1")
    monkeypatch.setenv("SALES_REPO_DIR", str(tmp_path))
    monkeypatch.setenv("WORKSPACE_DIR", str(tmp_path / "ws"))
    from importlib import reload
    import app.main as m
    reload(m)

    async def fake_runner(command, arg, **kwargs):
        yield {"kind": "status", "text": "Thinking…"}
        yield {"kind": "result", "output": f"# {command} {arg}", "files": []}

    m.app.state.runner = fake_runner
    return m.app

async def _client(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://t")

async def _drain(app):
    # Deterministically wait for background drive() tasks to finish (decrement
    # inflight / refund cap) instead of sleeping on a timer.
    await asyncio.gather(*list(app.state.tasks))

async def test_health_is_unauthenticated(app):
    async with await _client(app) as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

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
        await _drain(app)   # run finishes -> concurrency guard frees, cap=1
        assert (await c.post("/api/run", json=body, headers=headers)).status_code == 200
        await _drain(app)   # cap=2 (== DAILY_CAP)
        r = await c.post("/api/run", json=body, headers=headers)
    assert r.status_code == 429   # blocked by daily cap

async def test_failed_run_refunds_cap(app):
    async def failing_runner(command, arg, **kwargs):
        yield {"kind": "error", "message": "boom"}
    app.state.runner = failing_runner
    headers = {"X-Dashboard-Token": "secret-tok"}
    async with await _client(app) as c:
        await c.post("/api/run", json={"command": "research", "arg": "https://a.com"}, headers=headers)
        await _drain(app)
        u = (await c.get("/api/usage", headers=headers)).json()
    assert u["used"] == 0   # refunded

async def test_malformed_body_returns_400(app):
    async with await _client(app) as c:
        r = await c.post("/api/run", content="not json at all",
                         headers={"X-Dashboard-Token": "secret-tok",
                                  "Content-Type": "application/json"})
    assert r.status_code == 400

async def test_usage_endpoint(app):
    async with await _client(app) as c:
        r = await c.get("/api/usage", headers={"X-Dashboard-Token": "secret-tok"})
    assert r.status_code == 200
    assert set(r.json()) == {"used", "limit", "remaining"}

async def test_dashboard_page_requires_token(app):
    async with await _client(app) as c:
        assert (await c.get("/d/wrong/")).status_code == 404
        ok = await c.get("/d/secret-tok/")
    assert ok.status_code == 200
    assert "Sales Assistant" in ok.text
