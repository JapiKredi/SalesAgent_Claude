import pytest
from app.validation import validate_command, validate_arg, ValidationError

def test_validate_command_accepts_known():
    assert validate_command("research") == "research"

def test_validate_command_rejects_unknown():
    with pytest.raises(ValidationError):
        validate_command("rm-rf")

def test_url_command_requires_url_shape():
    assert validate_arg("research", "https://acme.com") == "https://acme.com"
    with pytest.raises(ValidationError):
        validate_arg("research", "not a url")

def test_url_command_requires_nonempty():
    with pytest.raises(ValidationError):
        validate_arg("research", "")

def test_text_command_accepts_plain_text():
    assert validate_arg("icp", "B2B SaaS founders") == "B2B SaaS founders"

def test_none_command_ignores_arg():
    assert validate_arg("report", "anything") == ""

def test_arg_length_capped():
    with pytest.raises(ValidationError):
        validate_arg("icp", "x" * 2001)

def test_arg_is_trimmed():
    assert validate_arg("icp", "  hello  ") == "hello"

def test_control_chars_rejected():
    with pytest.raises(ValidationError):
        validate_arg("icp", "line1\nline2")
