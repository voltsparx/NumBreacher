from collections import Counter
from datetime import datetime, timezone


class Reporter:
    UNKNOWN_OWNER_NAMES = {"unknown", "lookup disabled", ""}

    def single_scan_terminal(self, result):
        number = result.get("number", "Unknown")
        risk = result.get("risk", "Unknown")
        owner = result.get("owner", {})
        owner_name = str(owner.get("name", "Unknown"))
        owner_confidence = str(owner.get("confidence", "Low"))

        signals = []
        if result.get("voip"):
            signals.append("VoIP")
        if str(result.get("carrier", "")).strip().lower() == "unknown":
            signals.append("unknown-carrier")

        line_type = str(result.get("line_type", "UNKNOWN")).upper()
        if line_type in {"PREMIUM_RATE", "PAGER", "VOIP"}:
            signals.append(f"line={line_type}")

        if owner_name.strip().lower() in self.UNKNOWN_OWNER_NAMES:
            signals.append("owner-unresolved")

        if not signals:
            signals_text = "no major anomalies"
        else:
            signals_text = ", ".join(signals)

        return (
            f"[Reporter] {number} -> {risk} risk | "
            f"Owner: {owner_name} ({owner_confidence}) | Signals: {signals_text}"
        )

    def bulk_terminal_summary(
        self,
        results,
        scanned,
        skipped,
        engine_name,
        elapsed_seconds,
        workers,
        title="Bulk Summary",
    ):
        risk_counts = Counter(str(item.get("risk", "Unknown")) for item in results)
        owner_resolved = sum(1 for item in results if self._owner_resolved(item))

        carrier_counts = Counter(str(item.get("carrier", "Unknown")) for item in results)
        top_carriers = ", ".join(
            f"{name}({count})" for name, count in carrier_counts.most_common(3)
        )
        if not top_carriers:
            top_carriers = "None"

        top_regions = Counter(
            str((item.get("geo") or {}).get("Country", "Unknown")) for item in results
        )
        region_summary = ", ".join(
            f"{name}({count})" for name, count in top_regions.most_common(3)
        )
        if not region_summary:
            region_summary = "None"

        high_risk_numbers = [
            item.get("number", "Unknown") for item in results if item.get("risk") == "High"
        ][:5]
        if not high_risk_numbers:
            high_risk_text = "None"
        else:
            high_risk_text = ", ".join(high_risk_numbers)

        return "\n".join(
            [
                f"[Reporter] {title}",
                f" Engine: {engine_name} (workers={workers})",
                f" Runtime: {elapsed_seconds:.2f}s",
                f" Totals: scanned={scanned}, skipped={skipped}",
                (
                    " Risk: "
                    f"High={risk_counts.get('High', 0)}, "
                    f"Medium={risk_counts.get('Medium', 0)}, "
                    f"Low={risk_counts.get('Low', 0)}"
                ),
                f" Owner resolved: {owner_resolved}/{scanned if scanned else 0}",
                f" Top carriers: {top_carriers}",
                f" Top countries: {region_summary}",
                f" Priority numbers: {high_risk_text}",
            ]
        )

    def generate_markdown_report(self, results, metadata=None):
        metadata = metadata or {}
        scanned = len(results)
        skipped = int(metadata.get("skipped", 0))
        engine_name = metadata.get("engine", "threading")
        workers = int(metadata.get("workers", 1))
        elapsed_seconds = float(metadata.get("elapsed_seconds", 0.0))

        risk_counts = Counter(str(item.get("risk", "Unknown")) for item in results)
        owner_resolved = sum(1 for item in results if self._owner_resolved(item))
        top_carriers = Counter(str(item.get("carrier", "Unknown")) for item in results)
        top_countries = Counter(
            str((item.get("geo") or {}).get("Country", "Unknown")) for item in results
        )

        lines = [
            "# Telecom Recon Report",
            "",
            f"- Generated: {datetime.now(timezone.utc).isoformat()}",
            f"- Engine: {engine_name}",
            f"- Workers: {workers}",
            f"- Runtime: {elapsed_seconds:.2f}s",
            f"- Scanned: {scanned}",
            f"- Skipped: {skipped}",
            "",
            "## Risk Distribution",
            f"- High: {risk_counts.get('High', 0)}",
            f"- Medium: {risk_counts.get('Medium', 0)}",
            f"- Low: {risk_counts.get('Low', 0)}",
            "",
            "## Owner Resolution",
            f"- Resolved owner names: {owner_resolved}/{scanned if scanned else 0}",
            "",
            "## Top Carriers",
        ]

        if top_carriers:
            for name, count in top_carriers.most_common(10):
                lines.append(f"- {name}: {count}")
        else:
            lines.append("- None")

        lines.extend(["", "## Top Countries"])
        if top_countries:
            for name, count in top_countries.most_common(10):
                lines.append(f"- {name}: {count}")
        else:
            lines.append("- None")

        lines.extend(["", "## High-Risk Numbers"])
        high_risk_results = [item for item in results if item.get("risk") == "High"]
        if high_risk_results:
            for item in high_risk_results[:25]:
                owner_name = (item.get("owner") or {}).get("name", "Unknown")
                carrier = item.get("carrier", "Unknown")
                lines.append(f"- {item.get('number', 'Unknown')} | carrier={carrier} | owner={owner_name}")
        else:
            lines.append("- None")

        lines.extend(
            [
                "",
                "## Reporter Notes",
                "- Owner matches are heuristic and require manual verification.",
                "- Treat this report as triage intelligence, not identity proof.",
            ]
        )

        return "\n".join(lines) + "\n"

    def generate_json_summary(self, results, metadata=None):
        metadata = metadata or {}
        scanned = len(results)
        skipped = int(metadata.get("skipped", 0))
        engine_name = metadata.get("engine", "threading")
        workers = int(metadata.get("workers", 1))
        elapsed_seconds = float(metadata.get("elapsed_seconds", 0.0))

        risk_counts = Counter(str(item.get("risk", "Unknown")) for item in results)
        owner_resolved = sum(1 for item in results if self._owner_resolved(item))

        carrier_counts = Counter(str(item.get("carrier", "Unknown")) for item in results)
        country_counts = Counter(
            str((item.get("geo") or {}).get("Country", "Unknown")) for item in results
        )

        top_carriers = [
            {"carrier": name, "count": count} for name, count in carrier_counts.most_common(10)
        ]
        top_countries = [
            {"country": name, "count": count} for name, count in country_counts.most_common(10)
        ]
        high_risk_numbers = [
            item.get("number", "Unknown") for item in results if item.get("risk") == "High"
        ][:25]

        return {
            "metadata": {
                "engine": engine_name,
                "workers": workers,
                "elapsed_seconds": round(elapsed_seconds, 4),
                "scanned": scanned,
                "skipped": skipped,
            },
            "risk_distribution": {
                "high": risk_counts.get("High", 0),
                "medium": risk_counts.get("Medium", 0),
                "low": risk_counts.get("Low", 0),
                "unknown": risk_counts.get("Unknown", 0),
            },
            "owner_resolution": {
                "resolved": owner_resolved,
                "unresolved": scanned - owner_resolved,
            },
            "top_carriers": top_carriers,
            "top_countries": top_countries,
            "priority_numbers": high_risk_numbers,
        }

    def _owner_resolved(self, result):
        owner = result.get("owner", {})
        owner_name = str(owner.get("name", "Unknown")).strip().lower()
        return owner_name not in self.UNKNOWN_OWNER_NAMES
