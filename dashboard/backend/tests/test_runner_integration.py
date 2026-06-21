import os
import pytest
from pathlib import Path
from app.runner import run_command

pytestmark = pytest.mark.integration

@pytest.mark.skipif(os.environ.get("RUN_INTEGRATION") != "1",
                    reason="set RUN_INTEGRATION=1 and ANTHROPIC_API_KEY to run")
async def test_icp_produces_output(tmp_path):
    sales_repo = Path(os.environ["SALES_REPO_DIR"])
    events, final = [], None
    async for ev in run_command("icp", "B2B SaaS founders selling to SMBs",
                                sales_repo_dir=sales_repo,
                                run_dir=tmp_path / "runs" / "r1",
                                pipeline_dir=tmp_path / "pipeline",
                                max_turns=40):
        events.append(ev)
        if ev["kind"] == "result":
            final = ev
    assert final is not None
    assert final["output"]
    assert any(e["kind"] == "status" for e in events)
