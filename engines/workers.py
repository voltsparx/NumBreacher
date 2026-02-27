from core.scanner import scan_number
from core.validator import validate_number
from modules.owner_osint import lookup_owner_name
from ui.formatter import format_output


def scan_number_worker(task):
    number = str(task.get("number", "")).strip()
    enable_owner_lookup = bool(task.get("enable_owner_lookup", True))
    render_output = bool(task.get("render_output", True))

    if not number:
        return {"ok": False, "number": "", "error": "Invalid number: empty input"}

    valid, parsed = validate_number(number)
    if not valid:
        return {"ok": False, "number": number, "error": f"Invalid number: {number}"}

    try:
        result = scan_number(
            parsed,
            original_number=number,
            enable_owner_lookup=enable_owner_lookup,
        )
    except Exception as exc:
        return {"ok": False, "number": number, "error": f"Scan error for {number}: {exc}"}

    output = ""
    if render_output:
        output = format_output(result)

    return {
        "ok": True,
        "number": number,
        "result": result.to_dict(),
        "output": output,
    }


def owner_lookup_worker(task):
    number = str(task.get("number", "")).strip()
    if not number:
        return {"ok": False, "number": "", "error": "Invalid number: empty input"}

    valid, parsed = validate_number(number)
    if not valid:
        return {"ok": False, "number": number, "error": f"Invalid number: {number}"}

    try:
        owner = lookup_owner_name(parsed)
    except Exception as exc:
        return {"ok": False, "number": number, "error": f"Owner lookup error for {number}: {exc}"}

    return {"ok": True, "number": number, "owner": owner}
