import pytest
from app.config import load_settings, ConfigError

def _base_env(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-x")
    monkeypatch.setenv("DASHBOARD_TOKEN", "tok123")
    monkeypatch.setenv("SALES_REPO_DIR", str(tmp_path))
    monkeypatch.setenv("WORKSPACE_DIR", str(tmp_path / "ws"))

def test_loads_from_env(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("DAILY_CAP", "7")
    monkeypatch.setenv("MAX_TURNS", "55")
    monkeypatch.setenv("MAX_CONCURRENT", "3")
    monkeypatch.setenv("MODEL", "claude-sonnet-4-6")
    s = load_settings()
    assert s.token == "tok123"
    assert s.daily_cap == 7
    assert s.max_turns == 55
    assert s.max_concurrent == 3
    assert s.model == "claude-sonnet-4-6"
    assert s.api_key == "sk-ant-x"
    assert s.pipeline_dir == (tmp_path / "ws" / "pipeline")
    assert s.runs_dir == (tmp_path / "ws" / "runs")

def test_defaults(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.delenv("DAILY_CAP", raising=False)
    monkeypatch.delenv("MAX_TURNS", raising=False)
    monkeypatch.delenv("MAX_CONCURRENT", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    s = load_settings()
    assert s.daily_cap == 20
    assert s.max_turns == 80
    assert s.max_concurrent == 1
    assert s.model == "claude-haiku-4-5"   # cheapest by default

def test_missing_key_raises(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ConfigError):
        load_settings()

def test_missing_token_raises(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.delenv("DASHBOARD_TOKEN", raising=False)
    with pytest.raises(ConfigError):
        load_settings()
