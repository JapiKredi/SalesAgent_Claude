from app.commands import COMMANDS, get_command

def test_all_fourteen_present():
    assert len(COMMANDS) == 14
    names = {c["name"] for c in COMMANDS}
    assert names == {
        "prospect", "quick", "research", "qualify", "contacts",
        "outreach", "followup", "prep", "proposal", "objections",
        "icp", "competitors", "report", "report-pdf",
    }

def test_arg_kinds_are_known():
    allowed = {"url", "prospect", "client", "topic", "description", "none"}
    assert all(c["arg_kind"] in allowed for c in COMMANDS)

def test_report_commands_take_no_arg():
    assert get_command("report")["arg_kind"] == "none"
    assert get_command("report-pdf")["arg_kind"] == "none"

def test_report_pdf_outputs_pdf():
    assert get_command("report-pdf")["output"] == "pdf"
    assert get_command("research")["output"] == "markdown"

def test_pipeline_flag_set_only_for_report_commands():
    pipeline = {c["name"] for c in COMMANDS if c["pipeline"]}
    assert pipeline == {"report", "report-pdf"}

def test_output_file_set_for_all_but_quick():
    assert get_command("research")["output_file"] == "COMPANY-RESEARCH.md"
    assert get_command("report-pdf")["output_file"] == "SALES-REPORT-*.pdf"
    assert get_command("quick")["output_file"] is None

def test_get_unknown_returns_none():
    assert get_command("definitely-not-a-command") is None
