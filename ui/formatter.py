from core.models import ScanResult
from ui.colors import CYAN, RESET


def format_output(result_or_number, geo=None, carrier=None, voip=None, risk=None, osint=None):
    if isinstance(result_or_number, ScanResult):
        result = result_or_number
    else:
        if geo is None or carrier is None or voip is None or risk is None or osint is None:
            raise ValueError("Missing fields for scan result formatting.")
        result = ScanResult(
            number=str(result_or_number),
            geo=geo,
            carrier=carrier,
            line_type="UNKNOWN",
            formats={},
            voip=voip,
            risk=risk,
            owner={},
            reputation={},
            osint=osint,
        )

    out = []
    out.append(f"{CYAN}Scan Result for {result.number}{RESET}")
    out.append("-" * 40)

    for k, v in result.geo.items():
        out.append(f"{k:12}: {v}")

    out.append(f"Carrier     : {result.carrier}")
    out.append(f"Line Type   : {result.line_type}")
    out.append(f"VoIP        : {'Yes' if result.voip else 'No'}")
    out.append(f"Risk Level  : {result.risk}")

    if result.formats:
        out.append("\nNumber Formats:")
        for fmt, value in result.formats.items():
            out.append(f" {fmt:12}: {value}")

    owner = result.owner or {}
    out.append("\nOwner OSINT:")
    out.append(f" Name       : {owner.get('name', 'Unknown')}")
    out.append(f" Confidence : {owner.get('confidence', 'Low')}")

    method = owner.get("method")
    if method:
        out.append(f" Method     : {method}")

    candidates = owner.get("candidates", [])
    if candidates:
        out.append(f" Candidates : {', '.join(candidates)}")

    notes = owner.get("notes")
    if notes:
        out.append(f" Notes      : {notes}")

    owner_sources = owner.get("sources", [])
    if owner_sources:
        out.append(" Sources:")
        for source in owner_sources:
            out.append(f"  - {source}")

    if result.reputation:
        out.append("\nReputation Links:")
        for name, link in result.reputation.items():
            out.append(f" {name:10}: {link}")

    out.append("\nOSINT Links:")
    for name, link in result.osint.items():
        out.append(f" {name:10}: {link}")

    return "\n".join(out)
