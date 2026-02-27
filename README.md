# NumBreacher

NumBreacher is a telecom recon and OSINT framework for phone-number triage, investigation workflows, and reporting.

Current version: `1.3.0`

## Core Capabilities

- Telecom intelligence: country/region, carrier, line type, VoIP signals
- Risk scoring and high-priority number surfacing
- Owner-name OSINT heuristic lookup with confidence and source hints
- Recon links for manual verification (search engines, social/messaging surfaces)
- Single, bulk, and owner-only workflows
- Reporter summaries for terminal, Markdown, and JSON

## Framework Features

- Engine abstraction: `threading`, `parallel`, `async`
- Worker controls (`workers <1-64>`) for throughput tuning
- Profiles: `beginner`, `professional`, `speed`, `deep`
- Bulk rendering modes: `full`, `compact`, `silent`
- Runbooks for scripted command execution
- Learning layer: `tips`, `lessons`, `glossary`, `playbook`
- In-memory analytics: `searchresults`, `toprisks`, `diff`
- Config persistence (`saveconfig`, `loadconfig`)

## Installation

```bash
git clone https://github.com/voltsparx/NumBreacher.git
cd NumBreacher
pip install -r requirements.txt
python numbreacher.py
```

## Interactive Quickstart

```text
scan +14155552671
bulk numbers.txt
summary
toprisks 10
report output/report.md
reportjson output/report_summary.json
```

## Useful Commands

- `about` - metadata, contact, and ethical notice
- `status` - active profile, engine, workers, toggles, and dataset snapshot
- `bulkview <full|compact|silent>` - control bulk output/detail level
- `runbook <file.txt>` - execute command script
- `runbookstop <on|off>` - stop runbook when command fails
- `searchresults <query>` - find results by number/risk/carrier/region/owner
- `toprisks [n]` - show highest-risk records
- `diff <number>` - compare latest two scans of same number
- `lessons`, `glossary [term]`, `playbook [name]` - learning modules

## Runbook Example

Create a file like `runbooks/triage.txt`:

```text
# incident triage
profile professional
engine async
workers 16
bulkview compact
bulk numbers.txt
toprisks 15
report output/incident_report.md
```

Then run:

```text
runbook runbooks/triage.txt
```

## Flag Mode (Non-Interactive)

```bash
python numbreacher.py --profile professional --bulkview compact --bulk numbers.txt --summary --no-shell
python numbreacher.py --runbook runbooks/triage.txt --reportjson output/triage.json --no-shell
python numbreacher.py --scanfast +14155552671 --toprisks 5 --report output/report.md --no-shell
python numbreacher.py --glossary osint --playbook incident_triage --no-shell
```

## Testing

```bash
python -m unittest discover -s tests -v
```

## Ethical Use

Use only for authorized security testing, research, and education.
Do not use for harassment, stalking, privacy invasion, or unlawful surveillance.
