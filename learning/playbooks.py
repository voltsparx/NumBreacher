PLAYBOOKS = {
    "quickstart": [
        "profile beginner",
        "scan +14155552671",
        "summary",
        "report output/report.md",
    ],
    "incident_triage": [
        "profile professional",
        "engine async",
        "workers 16",
        "bulk numbers.txt",
        "toprisks 10",
        "reportjson output/report_summary.json",
    ],
    "owner_investigation": [
        "ownerlookup on",
        "whois +14155552671",
        "whoisbulk numbers.txt",
        "searchresults unknown",
    ],
    "performance_scan": [
        "profile speed",
        "bulkview compact",
        "bulkfast numbers.txt",
        "summary",
    ],
}
