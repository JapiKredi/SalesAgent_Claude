from app.commands import get_command

MAX_ARG_LEN = 2000

class ValidationError(Exception):
    pass

def validate_command(name: str) -> str:
    if get_command(name) is None:
        raise ValidationError(f"Unknown command: {name!r}")
    return name

def validate_arg(command: str, arg: str) -> str:
    cmd = get_command(command)
    if cmd is None:
        raise ValidationError(f"Unknown command: {command!r}")
    if cmd["arg_kind"] == "none":
        return ""
    arg = (arg or "").strip()
    if not arg:
        raise ValidationError("This command needs an input.")
    if len(arg) > MAX_ARG_LEN:
        raise ValidationError("Input is too long.")
    # Reject control chars / newlines — keeps a single-line value out of the prompt body.
    if any(ord(ch) < 32 for ch in arg):
        raise ValidationError("Input contains invalid characters.")
    if cmd["arg_kind"] == "url" and not (arg.startswith("http://") or arg.startswith("https://")):
        raise ValidationError("Please enter a full URL starting with https://")
    return arg
