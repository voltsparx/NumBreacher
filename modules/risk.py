def calculate_risk(is_voip, carrier, line_type="UNKNOWN", owner_profile=None):
    score = 0

    if is_voip:
        score += 45
    if carrier == "Unknown":
        score += 25

    if line_type in {"PREMIUM_RATE", "PAGER"}:
        score += 25
    elif line_type == "UNKNOWN":
        score += 10

    if owner_profile:
        owner_name = str(owner_profile.get("name", "Unknown")).strip().lower()
        confidence = str(owner_profile.get("confidence", "Low")).strip().lower()

        if owner_name in {"unknown", "", "lookup disabled"}:
            score += 10
        elif confidence == "low":
            score += 5

    if score >= 70:
        return "High"
    elif score >= 35:
        return "Medium"
    else:
        return "Low"
