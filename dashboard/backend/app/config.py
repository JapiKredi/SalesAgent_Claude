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
    max_turns: int
    max_concurrent: int
    model: str
    sales_repo_dir: Path
    workspace_dir: Path
    runs_dir: Path
    pipeline_dir: Path
    cap_file: Path

def load_settings() -> Settings:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    token = os.environ.get("DASHBOARD_TOKEN")
    if not api_key:
        raise ConfigError("ANTHROPIC_API_KEY is required")
    if not token:
        raise ConfigError("DASHBOARD_TOKEN is required")
    workspace_dir = Path(os.environ.get("WORKSPACE_DIR", "/app/workspace"))
    return Settings(
        api_key=api_key,
        token=token,
        daily_cap=int(os.environ.get("DAILY_CAP", "20")),
        max_turns=int(os.environ.get("MAX_TURNS", "80")),
        max_concurrent=int(os.environ.get("MAX_CONCURRENT", "1")),
        model=os.environ.get("MODEL", "claude-haiku-4-5"),  # cheapest tier by default

        sales_repo_dir=Path(os.environ.get("SALES_REPO_DIR", "/app/salesagent")),
        workspace_dir=workspace_dir,
        runs_dir=workspace_dir / "runs",
        pipeline_dir=workspace_dir / "pipeline",
        cap_file=workspace_dir / "cap.json",
    )
