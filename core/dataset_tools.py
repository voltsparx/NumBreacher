from collections import Counter

RISK_ORDER = {"High": 3, "Medium": 2, "Low": 1}


def search_results(results, query, limit=25):
    needle = str(query or "").strip().lower()
    if not needle:
        return []

    matched = []
    for item in results:
        number = str(item.get("number", ""))
        carrier = str(item.get("carrier", ""))
        risk = str(item.get("risk", ""))
        country = str((item.get("geo") or {}).get("Country", ""))
        region = str((item.get("geo") or {}).get("Region", ""))
        owner_name = str((item.get("owner") or {}).get("name", ""))

        blob = " ".join([number, carrier, risk, country, region, owner_name]).lower()
        if needle in blob:
            matched.append(item)
            if len(matched) >= limit:
                break

    return matched


def top_risks(results, limit=10):
    scored = []
    for item in results:
        risk = str(item.get("risk", "Low"))
        base_score = RISK_ORDER.get(risk, 0) * 100

        owner = item.get("owner") or {}
        owner_name = str(owner.get("name", "Unknown")).strip().lower()
        if owner_name in {"unknown", "lookup disabled", ""}:
            base_score += 20

        carrier = str(item.get("carrier", ""))
        if carrier.lower() == "unknown":
            base_score += 15

        if item.get("voip"):
            base_score += 20

        scored.append((base_score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[: max(1, int(limit))]]


def diff_number_history(results, number):
    target = str(number or "").strip()
    if not target:
        return None

    history = [item for item in results if str(item.get("number", "")).strip() == target]
    if len(history) < 2:
        return None

    previous = history[-2]
    current = history[-1]

    changes = {}
    keys = ["carrier", "line_type", "risk", "voip"]
    for key in keys:
        old = previous.get(key)
        new = current.get(key)
        if old != new:
            changes[key] = {"old": old, "new": new}

    old_owner = (previous.get("owner") or {}).get("name")
    new_owner = (current.get("owner") or {}).get("name")
    if old_owner != new_owner:
        changes["owner.name"] = {"old": old_owner, "new": new_owner}

    old_country = (previous.get("geo") or {}).get("Country")
    new_country = (current.get("geo") or {}).get("Country")
    if old_country != new_country:
        changes["geo.Country"] = {"old": old_country, "new": new_country}

    return {
        "number": target,
        "changed": bool(changes),
        "changes": changes,
    }


def quick_distribution(results):
    risks = Counter(str(item.get("risk", "Unknown")) for item in results)
    countries = Counter(str((item.get("geo") or {}).get("Country", "Unknown")) for item in results)
    return {
        "risks": dict(risks),
        "countries": dict(countries),
    }
