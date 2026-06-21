"""Single source of truth for the 14 /sales commands exposed by the dashboard.

pipeline=True commands (report, report-pdf) read/write the shared pipeline dir so
they can aggregate previously-generated reports; all others run in isolation.

output_file is the *documented* filename each skill writes (from the repo's
SKILL.md / README). The runner reads exactly that file (glob-matched, so the
timestamped report-pdf works), which is far more robust than guessing by mtime
when a skill also drops intermediate scratch files. None = terminal-only (quick).
"""

COMMANDS = [
    {"name": "prospect",   "arg_kind": "url",         "label": "Full prospect audit",        "output": "markdown", "pipeline": False, "output_file": "PROSPECT-ANALYSIS.md"},
    {"name": "quick",      "arg_kind": "url",         "label": "60-second snapshot",         "output": "markdown", "pipeline": False, "output_file": None},
    {"name": "research",   "arg_kind": "url",         "label": "Company research",           "output": "markdown", "pipeline": False, "output_file": "COMPANY-RESEARCH.md"},
    {"name": "qualify",    "arg_kind": "url",         "label": "BANT/MEDDIC qualification",  "output": "markdown", "pipeline": False, "output_file": "LEAD-QUALIFICATION.md"},
    {"name": "contacts",   "arg_kind": "url",         "label": "Decision makers",            "output": "markdown", "pipeline": False, "output_file": "DECISION-MAKERS.md"},
    {"name": "outreach",   "arg_kind": "prospect",    "label": "Cold outreach sequence",     "output": "markdown", "pipeline": False, "output_file": "OUTREACH-SEQUENCE.md"},
    {"name": "followup",   "arg_kind": "prospect",    "label": "Follow-up sequence",         "output": "markdown", "pipeline": False, "output_file": "FOLLOWUP-SEQUENCE.md"},
    {"name": "prep",       "arg_kind": "url",         "label": "Meeting prep brief",         "output": "markdown", "pipeline": False, "output_file": "MEETING-PREP.md"},
    {"name": "proposal",   "arg_kind": "client",      "label": "Client proposal",            "output": "markdown", "pipeline": False, "output_file": "CLIENT-PROPOSAL.md"},
    {"name": "objections", "arg_kind": "topic",       "label": "Objection playbook",         "output": "markdown", "pipeline": False, "output_file": "OBJECTION-PLAYBOOK.md"},
    {"name": "icp",        "arg_kind": "description",  "label": "Ideal Customer Profile",     "output": "markdown", "pipeline": False, "output_file": "IDEAL-CUSTOMER-PROFILE.md"},
    {"name": "competitors","arg_kind": "url",         "label": "Competitive intel",          "output": "markdown", "pipeline": False, "output_file": "COMPETITIVE-INTEL.md"},
    {"name": "report",     "arg_kind": "none",        "label": "Pipeline report",            "output": "markdown", "pipeline": True,  "output_file": "SALES-REPORT.md"},
    {"name": "report-pdf", "arg_kind": "none",        "label": "Pipeline report (PDF)",      "output": "pdf",      "pipeline": True,  "output_file": "SALES-REPORT-*.pdf"},
]

_BY_NAME = {c["name"]: c for c in COMMANDS}

def get_command(name: str):
    return _BY_NAME.get(name)
