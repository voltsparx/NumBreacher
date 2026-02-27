from modules.geo import get_geo_info
from modules.carrier import get_carrier_info
from modules.osint import get_osint_links
from modules.voip import is_voip
from modules.intel import get_line_type, get_number_formats
from modules.owner_osint import lookup_owner_name
from modules.reputation import get_reputation_links
from modules.risk import calculate_risk
from core.models import ScanResult


def scan_number(parsed, original_number=None, enable_owner_lookup=True):
    normalized_number = original_number or f"+{parsed.country_code}{parsed.national_number}"
    geo = get_geo_info(parsed)
    carrier = get_carrier_info(parsed)
    line_type = get_line_type(parsed)
    formats = get_number_formats(parsed)
    voip = is_voip(parsed)

    if enable_owner_lookup:
        owner = lookup_owner_name(parsed)
    else:
        owner = {
            "name": "Lookup disabled",
            "confidence": "Low",
            "method": "Disabled by user setting",
            "notes": "Enable owner lookup with `ownerlookup on`.",
            "sources": [],
            "candidates": [],
        }

    risk = calculate_risk(voip, carrier, line_type=line_type, owner_profile=owner)
    reputation = get_reputation_links(parsed)
    osint = get_osint_links(parsed)

    return ScanResult(
        number=normalized_number,
        geo=geo,
        carrier=carrier,
        line_type=line_type,
        formats=formats,
        voip=voip,
        risk=risk,
        owner=owner,
        reputation=reputation,
        osint=osint,
    )
