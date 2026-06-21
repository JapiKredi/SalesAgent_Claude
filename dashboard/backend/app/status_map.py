"""Translate raw Agent SDK activity into short, non-technical progress lines."""

_TOOL_STATUS = {
    "WebSearch": "Researching the web…",
    "WebFetch": "Researching the web…",
    "Task": "Running research agents…",
    "Bash": "Crunching numbers…",
    "Write": "Writing the report…",
    "Edit": "Writing the report…",
}

def friendly_status(event: dict):
    etype = event.get("type")
    if etype == "text":
        return "Thinking…"
    if etype == "tool_use":
        return _TOOL_STATUS.get(event.get("name"))
    return None
