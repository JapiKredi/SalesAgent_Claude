from app.status_map import friendly_status

def test_tool_use_web_maps_to_research():
    assert friendly_status({"type": "tool_use", "name": "WebSearch"}) == "Researching the web…"
    assert friendly_status({"type": "tool_use", "name": "WebFetch"}) == "Researching the web…"

def test_subagent_maps_to_analyzing():
    assert friendly_status({"type": "tool_use", "name": "Task"}) == "Running research agents…"

def test_script_maps_to_scoring():
    assert friendly_status({"type": "tool_use", "name": "Bash"}) == "Crunching numbers…"

def test_write_maps_to_writing():
    assert friendly_status({"type": "tool_use", "name": "Write"}) == "Writing the report…"

def test_text_message_maps_to_thinking():
    assert friendly_status({"type": "text"}) == "Thinking…"

def test_unknown_returns_none():
    assert friendly_status({"type": "tool_use", "name": "SomethingElse"}) is None
