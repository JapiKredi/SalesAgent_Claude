import os, pytest
from pathlib import Path

pytestmark = pytest.mark.integration

@pytest.mark.skipif(os.environ.get("RUN_INTEGRATION") != "1",
                    reason="set RUN_INTEGRATION=1 + ANTHROPIC_API_KEY + SALES_REPO_DIR")
async def test_sales_skill_is_discoverable(tmp_path):
    # Install skills into the home Claude config the SDK reads (setting_sources=["user"]).
    repo = Path(os.environ["SALES_REPO_DIR"])
    os.system(f"bash {repo}/install.sh >/dev/null 2>&1")
    from claude_agent_sdk import query, ClaudeAgentOptions
    opts = ClaudeAgentOptions(cwd=str(tmp_path), permission_mode="bypassPermissions",
                              setting_sources=["user"], max_turns=2)
    saw_text = False
    async for msg in query(prompt="List the subcommands of the `sales` skill, then stop.",
                           options=opts):
        if getattr(msg, "content", None):
            saw_text = True
    assert saw_text
