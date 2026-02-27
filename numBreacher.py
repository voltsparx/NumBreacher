import argparse
import json
import time
from collections import Counter
from difflib import get_close_matches
from pathlib import Path

from core.dataset_tools import diff_number_history, search_results, top_risks
from core.scanner import scan_number
from core.settings import FrameworkSettings, PROFILE_PRESETS
from core.validator import validate_number
from engines.factory import available_engines, create_engine
from engines.workers import owner_lookup_worker, scan_number_worker
from learning.glossary import GLOSSARY
from learning.playbooks import PLAYBOOKS
from config.metadata import (
    APP_NAME,
    APP_TAGLINE,
    AUTHOR,
    CONTACT_EMAILS,
    ETHICAL_NOTICE,
    REPO_URL,
    VERSION,
)
from modules.intel import get_number_formats
from modules.owner_osint import lookup_owner_name
from reporter.reporter import Reporter
from ui.banner import show_banner
from ui.formatter import format_output
from utils.helpers import save_result
from utils.logger import log


class NumBreacherCLI:
    COMMAND_ALIASES = {
        "?": "help",
        "h": "help",
        "s": "scan",
        "sf": "scanfast",
        "b": "bulk",
        "bf": "bulkfast",
        "w": "whois",
        "wb": "whoisbulk",
        "bv": "bulkview",
        "rb": "runbook",
        "sr": "searchresults",
        "tr": "toprisks",
        "cfg": "status",
        "stats": "summary",
        "q": "exit",
    }

    def __init__(self):
        self.last_results = []
        self.last_bulk_metadata = {"skipped": 0, "elapsed_seconds": 0.0}
        self.settings = FrameworkSettings()
        self.reporter = Reporter()
        self._runbook_depth = 0
        self.command_handlers = {
            "help": self.handle_help,
            "scan": self.handle_scan,
            "scanfast": self.handle_scanfast,
            "bulk": self.handle_bulk,
            "bulkfast": self.handle_bulkfast,
            "whois": self.handle_whois,
            "whoisbulk": self.handle_whois_bulk,
            "ownerlookup": self.handle_owner_lookup,
            "engine": self.handle_engine,
            "workers": self.handle_workers,
            "autosummary": self.handle_auto_summary,
            "dedupe": self.handle_dedupe,
            "bulkview": self.handle_bulk_view,
            "profile": self.handle_profile,
            "status": self.handle_status,
            "tips": self.handle_tips,
            "about": self.handle_about,
            "glossary": self.handle_glossary,
            "playbook": self.handle_playbook,
            "lessons": self.handle_lessons,
            "runbookstop": self.handle_runbook_stop,
            "validate": self.handle_validate,
            "clearresults": self.handle_clear_results,
            "runbook": self.handle_runbook,
            "searchresults": self.handle_search_results,
            "toprisks": self.handle_top_risks,
            "diff": self.handle_diff,
            "summary": self.handle_summary,
            "report": self.handle_report,
            "reportjson": self.handle_report_json,
            "saveconfig": self.handle_save_config,
            "loadconfig": self.handle_load_config,
            "exportjson": self.handle_export_json,
        }

    @staticmethod
    def help_menu():
        print(
            """
Core Commands:
 scan <number>           Scan one phone number
 scanfast <number>       Scan without owner lookup
 bulk <file.txt>         Bulk scan from file
 bulkfast <file.txt>     Fast bulk scan (no owner lookup)
 runbook <file.txt>      Execute command script from file
 whois <number>          Owner OSINT lookup only
 whoisbulk <file.txt>    Bulk owner lookups
 validate <number>       Validate and normalize number formats
 searchresults <query>   Search in-memory results
 toprisks [n]            Show top n riskiest in-memory results
 diff <number>           Compare latest two scans of a number

Framework Commands:
 status                  Show framework status and session stats
 tips                    Beginner-friendly quick help
 about                   Show tool metadata and ethical notice
 lessons                 List learning modules
 glossary [term]         Telecom recon glossary
 playbook [name]         Show guided investigation playbooks
 profile <name>          Apply profile: beginner/professional/speed/deep
 engine [name]           Show/set engine: threading, parallel, async
 workers <number>        Set worker count (1-64)
 ownerlookup <on|off>    Toggle owner lookup in scan/bulk
 autosummary <on|off>    Auto print summary after bulk
 dedupe <on|off>         Remove duplicate numbers in bulk
 bulkview <mode>         Bulk output mode: full, compact, silent
 runbookstop <on|off>    Stop runbook when a command fails
 saveconfig <file.json>  Save framework settings
 loadconfig <file.json>  Load framework settings
 clearresults            Clear in-memory scan results

Reporting Commands:
 summary                 Terminal dataset summary
 report <file.md>        Write markdown report
 reportjson <file.json>  Write structured summary JSON
 exportjson <file.json>  Export full raw scan results

General:
 help                    Show this menu
 exit                    Exit tool
""".strip()
        )

    def run(self, show_startup=True):
        if show_startup:
            show_banner()
            self.help_menu()
            if self.settings.show_beginner_tips:
                self.handle_tips("")

        while True:
            try:
                raw = input("\nNumBreacher > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            if not raw:
                continue

            command, arg = self._parse_command(raw)
            if command == "exit":
                break

            handler = self.command_handlers.get(command)
            if handler is None:
                self._print_unknown_command(command)
                continue

            try:
                handler(arg)
            except Exception as exc:
                print(f"Command failed: {exc}")
                log(f"command_error command={command} error={exc}")

    def _parse_command(self, raw):
        parts = raw.split(maxsplit=1)
        command = parts[0].strip().lower()
        command = self.COMMAND_ALIASES.get(command, command)
        argument = parts[1].strip() if len(parts) > 1 else ""
        if len(argument) >= 2 and argument[0] == argument[-1] and argument[0] in {"'", '"'}:
            argument = argument[1:-1]
        return command, argument

    def _print_unknown_command(self, command):
        choices = list(self.command_handlers.keys()) + ["exit"]
        suggestion = get_close_matches(command, choices, n=1, cutoff=0.55)
        if suggestion:
            print(f"Unknown command '{command}'. Did you mean '{suggestion[0]}'?")
        else:
            print(f"Unknown command '{command}'. Type 'help'.")

    def _current_engine_name(self):
        return self.settings.engine_name

    def _current_workers(self):
        return self.settings.max_workers

    def _owner_lookup_enabled(self):
        return self.settings.owner_lookup_enabled

    def _record_scan_result(self, result):
        output = format_output(result)
        print(output)
        save_result(output)
        result_dict = result.to_dict()
        self.last_results.append(result_dict)
        print(self.reporter.single_scan_terminal(result_dict))

    def _scan_and_record(self, number, enable_owner_lookup=None):
        valid, parsed = validate_number(number)
        if not valid:
            print(f"Invalid number: {number}")
            log(f"scan_invalid number={number}")
            return False

        lookup_enabled = self._owner_lookup_enabled()
        if enable_owner_lookup is not None:
            lookup_enabled = enable_owner_lookup

        result = scan_number(
            parsed,
            original_number=number,
            enable_owner_lookup=lookup_enabled,
        )
        self._record_scan_result(result)
        log(
            "scan_success "
            f"number={number} risk={result.risk} "
            f"engine={self._current_engine_name()} owner_lookup={lookup_enabled}"
        )
        return True

    def _read_bulk_numbers(self, file_path):
        with open(file_path, encoding="utf-8") as handle:
            return [line.strip() for line in handle if line.strip()]

    def _prepare_bulk_numbers(self, numbers):
        if not self.settings.dedupe_bulk_numbers:
            return numbers, 0

        unique = []
        seen = set()
        for number in numbers:
            key = number.strip()
            if key in seen:
                continue
            seen.add(key)
            unique.append(number)
        removed = len(numbers) - len(unique)
        return unique, removed

    def _profile_names(self):
        return ", ".join(sorted(PROFILE_PRESETS.keys()))

    def _metadata(self):
        return {
            "engine": self._current_engine_name(),
            "workers": self._current_workers(),
            "elapsed_seconds": float(self.last_bulk_metadata.get("elapsed_seconds", 0.0)),
            "skipped": int(self.last_bulk_metadata.get("skipped", 0)),
        }

    def run_flag_actions(self, args):
        ran = False

        if args.loadconfig:
            self.handle_load_config(args.loadconfig)
            ran = True

        if args.profile:
            self.handle_profile(args.profile)
            ran = True
        if args.engine:
            self.handle_engine(args.engine)
            ran = True
        if args.workers is not None:
            self.handle_workers(str(args.workers))
            ran = True
        if args.bulkview:
            self.handle_bulk_view(args.bulkview)
            ran = True
        if args.runbookstop:
            self.handle_runbook_stop(args.runbookstop)
            ran = True
        if args.ownerlookup:
            self.handle_owner_lookup(args.ownerlookup)
            ran = True
        if args.autosummary:
            self.handle_auto_summary(args.autosummary)
            ran = True
        if args.dedupe:
            self.handle_dedupe(args.dedupe)
            ran = True

        if args.validate:
            self.handle_validate(args.validate)
            ran = True
        if args.runbook:
            self.handle_runbook(args.runbook)
            ran = True
        if args.scan:
            self.handle_scan(args.scan)
            ran = True
        if args.scanfast:
            self.handle_scanfast(args.scanfast)
            ran = True
        if args.bulk:
            self.handle_bulk(args.bulk)
            ran = True
        if args.bulkfast:
            self.handle_bulkfast(args.bulkfast)
            ran = True
        if args.whois:
            self.handle_whois(args.whois)
            ran = True
        if args.whoisbulk:
            self.handle_whois_bulk(args.whoisbulk)
            ran = True

        if args.searchresults:
            self.handle_search_results(args.searchresults)
            ran = True
        if args.toprisks is not None:
            self.handle_top_risks(args.toprisks)
            ran = True
        if args.diff:
            self.handle_diff(args.diff)
            ran = True

        if args.status:
            self.handle_status("")
            ran = True
        if args.summary:
            self.handle_summary("")
            ran = True
        if args.tips:
            self.handle_tips("")
            ran = True
        if args.about:
            self.handle_about("")
            ran = True
        if args.lessons:
            self.handle_lessons("")
            ran = True
        if args.glossary is not None:
            self.handle_glossary(args.glossary)
            ran = True
        if args.playbook is not None:
            self.handle_playbook(args.playbook)
            ran = True

        if args.report:
            self.handle_report(args.report)
            ran = True
        if args.reportjson:
            self.handle_report_json(args.reportjson)
            ran = True
        if args.exportjson:
            self.handle_export_json(args.exportjson)
            ran = True

        if args.saveconfig:
            self.handle_save_config(args.saveconfig)
            ran = True

        if args.clearresults:
            self.handle_clear_results("")
            ran = True

        return ran

    def handle_help(self, _):
        self.help_menu()

    def handle_scan(self, number):
        if not number:
            print("Usage: scan <number>")
            return
        self._scan_and_record(number, enable_owner_lookup=None)

    def handle_scanfast(self, number):
        if not number:
            print("Usage: scanfast <number>")
            return
        self._scan_and_record(number, enable_owner_lookup=False)

    def handle_bulk(self, file_path):
        self._handle_bulk_impl(file_path, enable_owner_lookup=None)

    def handle_bulkfast(self, file_path):
        self._handle_bulk_impl(file_path, enable_owner_lookup=False)

    def _handle_bulk_impl(self, file_path, enable_owner_lookup=None):
        if not file_path:
            print("Usage: bulk <file.txt>")
            return

        scanned = 0
        skipped = 0
        batch_results = []

        try:
            numbers = self._read_bulk_numbers(file_path)
        except OSError as exc:
            print(f"Bulk error: {exc}")
            log(f"bulk_error file={file_path} error={exc}")
            return

        if not numbers:
            print("Bulk error: input file contains no numbers.")
            return

        numbers, removed_duplicates = self._prepare_bulk_numbers(numbers)
        if removed_duplicates:
            print(f"Deduped bulk input: removed {removed_duplicates} duplicate entries.")

        lookup_enabled = self._owner_lookup_enabled()
        if enable_owner_lookup is not None:
            lookup_enabled = enable_owner_lookup

        output_mode = str(self.settings.bulk_output_mode or "full").strip().lower()
        if output_mode not in {"full", "compact", "silent"}:
            output_mode = "full"
            self.settings.bulk_output_mode = "full"

        tasks = [
            {
                "number": number,
                "enable_owner_lookup": lookup_enabled,
                "render_output": output_mode == "full",
            }
            for number in numbers
        ]

        try:
            engine = create_engine(self._current_engine_name())
        except ValueError as exc:
            print(exc)
            return

        start_time = time.perf_counter()
        worker_results = engine.run(
            scan_number_worker,
            tasks,
            max_workers=self._current_workers(),
        )
        elapsed = time.perf_counter() - start_time
        total = len(worker_results)

        for index, item in enumerate(worker_results, start=1):
            if item.get("ok"):
                output = item.get("output", "")
                result = item.get("result", {})
                if output_mode == "full":
                    print(output)
                    save_result(output)
                elif output_mode == "compact":
                    print(self.reporter.single_scan_terminal(result))
                self.last_results.append(result)
                batch_results.append(result)
                scanned += 1
            else:
                print(item.get("error", "Bulk scan worker failed."))
                skipped += 1

            if total >= 20 and (index % 10 == 0 or index == total):
                print(f"Bulk progress: {index}/{total}")

        self.last_bulk_metadata = {"skipped": skipped, "elapsed_seconds": elapsed}
        print(f"Bulk complete. Scanned: {scanned}, Skipped: {skipped}")

        log(
            "bulk_complete "
            f"file={file_path} scanned={scanned} skipped={skipped} "
            f"elapsed={elapsed:.3f}s engine={self._current_engine_name()} "
            f"workers={self._current_workers()} owner_lookup={lookup_enabled}"
        )

        if self.settings.auto_summary_after_bulk:
            print(
                self.reporter.bulk_terminal_summary(
                    batch_results,
                    scanned=scanned,
                    skipped=skipped,
                    engine_name=self._current_engine_name(),
                    elapsed_seconds=elapsed,
                    workers=self._current_workers(),
                )
            )
        else:
            print("Auto summary is off. Run `summary` for a dataset overview.")

    def handle_whois(self, number):
        if not number:
            print("Usage: whois <number>")
            return

        valid, parsed = validate_number(number)
        if not valid:
            print(f"Invalid number: {number}")
            return

        owner = lookup_owner_name(parsed)
        print("\nOwner OSINT Lookup")
        print("-" * 40)
        print(f"Name       : {owner.get('name', 'Unknown')}")
        print(f"Confidence : {owner.get('confidence', 'Low')}")
        print(f"Method     : {owner.get('method', 'Unknown')}")

        candidates = owner.get("candidates", [])
        if candidates:
            print(f"Candidates : {', '.join(candidates)}")

        notes = owner.get("notes")
        if notes:
            print(f"Notes      : {notes}")

        sources = owner.get("sources", [])
        if sources:
            print("Sources:")
            for source in sources:
                print(f" - {source}")

    def handle_whois_bulk(self, file_path):
        if not file_path:
            print("Usage: whoisbulk <file.txt>")
            return

        try:
            numbers = self._read_bulk_numbers(file_path)
        except OSError as exc:
            print(f"Whois bulk error: {exc}")
            return

        if not numbers:
            print("Whois bulk error: input file contains no numbers.")
            return

        numbers, removed_duplicates = self._prepare_bulk_numbers(numbers)
        if removed_duplicates:
            print(f"Deduped whois input: removed {removed_duplicates} duplicate entries.")

        try:
            engine = create_engine(self._current_engine_name())
        except ValueError as exc:
            print(exc)
            return

        tasks = [{"number": number} for number in numbers]
        start_time = time.perf_counter()
        worker_results = engine.run(owner_lookup_worker, tasks, max_workers=self._current_workers())
        elapsed = time.perf_counter() - start_time

        successful = 0
        failed = 0
        total = len(worker_results)
        for index, item in enumerate(worker_results, start=1):
            if item.get("ok"):
                successful += 1
                number = item.get("number", "Unknown")
                owner = item.get("owner", {})
                print(
                    f"[whois] {number} -> {owner.get('name', 'Unknown')} "
                    f"({owner.get('confidence', 'Low')})"
                )
            else:
                failed += 1
                print(item.get("error", "Owner lookup worker failed."))

            if total >= 20 and (index % 10 == 0 or index == total):
                print(f"Whois progress: {index}/{total}")

        print(
            f"Whois bulk complete. Success: {successful}, Failed: {failed}, "
            f"Runtime: {elapsed:.2f}s"
        )

    def handle_owner_lookup(self, state):
        if not state:
            current = "on" if self.settings.owner_lookup_enabled else "off"
            print(f"ownerlookup is currently {current}")
            print("Usage: ownerlookup <on|off>")
            return

        normalized = state.strip().lower()
        if normalized not in {"on", "off"}:
            print("Usage: ownerlookup <on|off>")
            return

        self.settings.owner_lookup_enabled = normalized == "on"
        status = "enabled" if self.settings.owner_lookup_enabled else "disabled"
        print(f"Owner lookup {status} for scan and bulk commands.")

    def handle_engine(self, value):
        if not value:
            available = ", ".join(available_engines())
            print(f"Current engine: {self._current_engine_name()}")
            print(f"Available engines: {available}")
            print("Usage: engine <threading|parallel|async>")
            return

        selected = value.strip().lower()
        if selected not in available_engines():
            print(f"Unknown engine '{selected}'. Available: {', '.join(available_engines())}")
            return

        self.settings.engine_name = selected
        print(f"Engine set to {self._current_engine_name()}.")

    def handle_workers(self, value):
        if not value:
            print(f"Current workers: {self._current_workers()}")
            print("Usage: workers <number>")
            return

        try:
            parsed = int(value.strip())
        except ValueError:
            print("Workers must be an integer.")
            return

        if parsed < 1 or parsed > 64:
            print("Workers must be between 1 and 64.")
            return

        self.settings.max_workers = parsed
        print(f"Worker count set to {self._current_workers()}.")

    def handle_auto_summary(self, value):
        if not value:
            current = "on" if self.settings.auto_summary_after_bulk else "off"
            print(f"autosummary is currently {current}")
            print("Usage: autosummary <on|off>")
            return

        normalized = value.strip().lower()
        if normalized not in {"on", "off"}:
            print("Usage: autosummary <on|off>")
            return

        self.settings.auto_summary_after_bulk = normalized == "on"
        status = "enabled" if self.settings.auto_summary_after_bulk else "disabled"
        print(f"Auto summary {status}.")

    def handle_dedupe(self, value):
        if not value:
            current = "on" if self.settings.dedupe_bulk_numbers else "off"
            print(f"dedupe is currently {current}")
            print("Usage: dedupe <on|off>")
            return

        normalized = value.strip().lower()
        if normalized not in {"on", "off"}:
            print("Usage: dedupe <on|off>")
            return

        self.settings.dedupe_bulk_numbers = normalized == "on"
        status = "enabled" if self.settings.dedupe_bulk_numbers else "disabled"
        print(f"Bulk dedupe {status}.")

    def handle_runbook_stop(self, value):
        if not value:
            current = "on" if self.settings.runbook_stop_on_error else "off"
            print(f"runbookstop is currently {current}")
            print("Usage: runbookstop <on|off>")
            return

        normalized = value.strip().lower()
        if normalized not in {"on", "off"}:
            print("Usage: runbookstop <on|off>")
            return

        self.settings.runbook_stop_on_error = normalized == "on"
        status = "enabled" if self.settings.runbook_stop_on_error else "disabled"
        print(f"Runbook stop-on-error {status}.")

    def handle_bulk_view(self, value):
        if not value:
            print(f"Current bulkview mode: {self.settings.bulk_output_mode}")
            print("Usage: bulkview <full|compact|silent>")
            return

        normalized = value.strip().lower()
        if normalized not in {"full", "compact", "silent"}:
            print("Usage: bulkview <full|compact|silent>")
            return

        self.settings.bulk_output_mode = normalized
        print(f"Bulk output mode set to {normalized}.")

    def handle_glossary(self, term):
        target = str(term or "").strip().lower()
        if not target:
            print("\nGlossary Terms")
            print("-" * 40)
            for key in sorted(GLOSSARY):
                print(f"- {key}")
            print("Usage: glossary <term>")
            return

        if target in GLOSSARY:
            print(f"{target}: {GLOSSARY[target]}")
            return

        suggestion = get_close_matches(target, list(GLOSSARY.keys()), n=1, cutoff=0.55)
        if suggestion:
            print(f"Unknown term '{target}'. Did you mean '{suggestion[0]}'?")
        else:
            print(f"Unknown term '{target}'. Use `glossary` to list available terms.")

    def handle_playbook(self, name):
        target = str(name or "").strip().lower()
        if not target:
            print("\nAvailable Playbooks")
            print("-" * 40)
            for key in sorted(PLAYBOOKS):
                print(f"- {key}")
            print("Usage: playbook <name>")
            return

        steps = PLAYBOOKS.get(target)
        if steps is None:
            suggestion = get_close_matches(target, list(PLAYBOOKS.keys()), n=1, cutoff=0.55)
            if suggestion:
                print(f"Unknown playbook '{target}'. Did you mean '{suggestion[0]}'?")
            else:
                print(f"Unknown playbook '{target}'. Use `playbook` to list available names.")
            return

        print(f"\nPlaybook: {target}")
        print("-" * 40)
        for index, step in enumerate(steps, start=1):
            print(f"{index}. {step}")
        print("\nTip: run commands directly or save them into a runbook file.")

    def handle_lessons(self, _):
        print("\nLearning Modules")
        print("-" * 40)
        print("1. `tips` for beginner workflow guidance")
        print("2. `glossary` for telecom and OSINT terminology")
        print("3. `playbook` for investigation sequences")
        print("4. `runbook <file>` to automate those sequences")

    def handle_runbook(self, file_path):
        if not file_path:
            print("Usage: runbook <file.txt>")
            return

        if self._runbook_depth >= 3:
            print("Runbook nesting limit reached (max depth: 3).")
            return

        path = Path(file_path.strip())
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            print(f"Runbook error: {exc}")
            return

        commands = []
        for line in lines:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            commands.append(text)

        if not commands:
            print("Runbook contains no executable commands.")
            return

        start = time.perf_counter()
        executed = 0
        failed = 0
        skipped = 0

        self._runbook_depth += 1
        try:
            for index, raw_command in enumerate(commands, start=1):
                command, arg = self._parse_command(raw_command)
                print(f"[runbook {index}/{len(commands)}] {raw_command}")

                if command in {"exit"}:
                    skipped += 1
                    print("Runbook skipped reserved command: exit")
                    continue

                if command == "runbook":
                    skipped += 1
                    print("Runbook skipped nested runbook command for safety.")
                    continue

                handler = self.command_handlers.get(command)
                if handler is None:
                    failed += 1
                    print(f"Runbook unknown command: {command}")
                    if self.settings.runbook_stop_on_error:
                        break
                    continue

                try:
                    handler(arg)
                    executed += 1
                except Exception as exc:
                    failed += 1
                    print(f"Runbook command failed: {command} ({exc})")
                    log(f"runbook_error command={command} error={exc}")
                    if self.settings.runbook_stop_on_error:
                        break
        finally:
            self._runbook_depth -= 1

        elapsed = time.perf_counter() - start
        print(
            "Runbook complete. "
            f"Executed: {executed}, Failed: {failed}, Skipped: {skipped}, Runtime: {elapsed:.2f}s"
        )

    def handle_search_results(self, query):
        if not query:
            print("Usage: searchresults <query>")
            return

        if not self.last_results:
            print("No in-memory results to search.")
            return

        matches = search_results(self.last_results, query, limit=25)
        if not matches:
            print(f"No results matched query: {query}")
            return

        print(f"\nSearch Results for '{query}' ({len(matches)} matches)")
        print("-" * 40)
        for item in matches:
            number = item.get("number", "Unknown")
            risk = item.get("risk", "Unknown")
            carrier = item.get("carrier", "Unknown")
            country = (item.get("geo") or {}).get("Country", "Unknown")
            owner_name = (item.get("owner") or {}).get("name", "Unknown")
            print(
                f"- {number} | risk={risk} | carrier={carrier} | country={country} | owner={owner_name}"
            )

    def handle_top_risks(self, value):
        if not self.last_results:
            print("No in-memory results available.")
            return

        target = str(value or "10").strip()
        try:
            limit = max(1, min(100, int(target)))
        except ValueError:
            print("Usage: toprisks [n]")
            return

        results = top_risks(self.last_results, limit=limit)
        print(f"\nTop Risks ({len(results)})")
        print("-" * 40)
        for index, item in enumerate(results, start=1):
            number = item.get("number", "Unknown")
            risk = item.get("risk", "Unknown")
            carrier = item.get("carrier", "Unknown")
            line_type = item.get("line_type", "Unknown")
            owner_name = (item.get("owner") or {}).get("name", "Unknown")
            print(
                f"{index}. {number} | risk={risk} | carrier={carrier} | "
                f"line_type={line_type} | owner={owner_name}"
            )

    def handle_diff(self, number):
        if not number:
            print("Usage: diff <number>")
            return

        result = diff_number_history(self.last_results, number)
        if result is None:
            print("No diff available. Need at least two scans for the same number.")
            return

        print(f"\nDiff for {result['number']}")
        print("-" * 40)
        if not result["changed"]:
            print("No changes detected between latest two scans.")
            return

        for key, change in result["changes"].items():
            print(f"- {key}: {change.get('old')} -> {change.get('new')}")

    def handle_profile(self, value):
        if not value:
            print(f"Current profile: {self.settings.profile}")
            print(f"Available profiles: {self._profile_names()}")
            print("Usage: profile <beginner|professional|speed|deep>")
            return

        try:
            self.settings.apply_profile(value)
        except ValueError as exc:
            print(exc)
            return

        if self._current_engine_name() not in available_engines():
            self.settings.engine_name = "threading"

        print(f"Profile applied: {self.settings.profile}")
        self.handle_status("")

    def handle_status(self, _):
        counts = Counter(str(item.get("risk", "Unknown")) for item in self.last_results)
        print("\nFramework Status")
        print("-" * 40)
        print(f"Profile        : {self.settings.profile}")
        print(f"Engine         : {self._current_engine_name()}")
        print(f"Workers        : {self._current_workers()}")
        print(f"Owner Lookup   : {'On' if self._owner_lookup_enabled() else 'Off'}")
        print(
            f"Auto Summary   : {'On' if self.settings.auto_summary_after_bulk else 'Off'}"
        )
        print(f"Bulk Dedupe    : {'On' if self.settings.dedupe_bulk_numbers else 'Off'}")
        print(f"Bulk View      : {self.settings.bulk_output_mode}")
        print(
            "Runbook Stop   : "
            f"{'On' if self.settings.runbook_stop_on_error else 'Off'}"
        )
        print(f"Results Loaded : {len(self.last_results)}")
        print(
            "Risk Snapshot  : "
            f"High={counts.get('High', 0)}, "
            f"Medium={counts.get('Medium', 0)}, "
            f"Low={counts.get('Low', 0)}"
        )

    def handle_tips(self, _):
        print("\nQuick Tips")
        print("-" * 40)
        print("1. Start with `scan <number>` for single investigations.")
        print("2. Use `bulk <file>` for datasets; it uses your selected engine.")
        print("3. Run `profile professional` for fast, analyst-style defaults.")
        print("4. Run `summary` then `report output/report.md` to document findings.")
        print("5. Use `status` anytime to review your active framework settings.")

    def handle_about(self, _):
        contacts = ", ".join(CONTACT_EMAILS)
        print("\nAbout")
        print("-" * 40)
        print(f"Name          : {APP_NAME}")
        print(f"Tagline       : {APP_TAGLINE}")
        print(f"Version       : {VERSION}")
        print(f"Author        : {AUTHOR}")
        print(f"Contact       : {contacts}")
        print(f"Repository    : {REPO_URL}")
        print(f"Ethical Notice: {ETHICAL_NOTICE}")

    def handle_validate(self, number):
        if not number:
            print("Usage: validate <number>")
            return

        valid, parsed = validate_number(number)
        if not valid:
            print(f"Invalid number: {number}")
            return

        formats = get_number_formats(parsed)
        print("\nNumber Validation")
        print("-" * 40)
        print(f"Input      : {number}")
        print("Valid      : Yes")
        if formats:
            for key, value in formats.items():
                print(f"{key:11}: {value}")

    def handle_clear_results(self, _):
        count = len(self.last_results)
        self.last_results.clear()
        self.last_bulk_metadata = {"skipped": 0, "elapsed_seconds": 0.0}
        print(f"Cleared {count} in-memory results.")

    def handle_summary(self, _):
        if not self.last_results:
            print("No scan results available for summary.")
            return

        print(
            self.reporter.bulk_terminal_summary(
                self.last_results,
                scanned=len(self.last_results),
                skipped=0,
                engine_name=self._current_engine_name(),
                elapsed_seconds=float(self.last_bulk_metadata.get("elapsed_seconds", 0.0)),
                workers=self._current_workers(),
                title="Dataset Summary",
            )
        )

    def handle_report(self, file_path):
        if not self.last_results:
            print("No scan results available for report.")
            return

        target = file_path.strip() or "output/report.md"
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)

        report = self.reporter.generate_markdown_report(
            self.last_results,
            metadata=self._metadata(),
        )

        try:
            with path.open("w", encoding="utf-8") as handle:
                handle.write(report)
            print(f"Report generated at {path}.")
        except OSError as exc:
            print(f"Report error: {exc}")

    def handle_report_json(self, file_path):
        if not self.last_results:
            print("No scan results available for reportjson.")
            return

        target = file_path.strip() or "output/report.json"
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)

        summary = self.reporter.generate_json_summary(
            self.last_results,
            metadata=self._metadata(),
        )

        try:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(summary, handle, indent=4)
            print(f"JSON summary report generated at {path}.")
        except OSError as exc:
            print(f"Reportjson error: {exc}")

    def handle_save_config(self, file_path):
        target = file_path.strip() or "config/framework_settings.json"
        try:
            self.settings.save(target)
        except OSError as exc:
            print(f"Save config error: {exc}")
            return
        print(f"Config saved to {target}.")

    def handle_load_config(self, file_path):
        if not file_path:
            print("Usage: loadconfig <file.json>")
            return

        try:
            loaded = FrameworkSettings.load(file_path.strip())
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"Load config error: {exc}")
            return

        if loaded.engine_name not in available_engines():
            loaded.engine_name = "threading"
        loaded.max_workers = max(1, min(64, int(loaded.max_workers)))
        if str(loaded.bulk_output_mode).strip().lower() not in {"full", "compact", "silent"}:
            loaded.bulk_output_mode = "full"
        loaded.runbook_stop_on_error = bool(loaded.runbook_stop_on_error)

        self.settings = loaded
        print(f"Config loaded from {file_path}.")
        self.handle_status("")

    def handle_export_json(self, file_path):
        if not file_path:
            print("Usage: exportjson <file.json>")
            return

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(self.last_results, handle, indent=4)
            print(f"Exported {len(self.last_results)} records to JSON.")
        except OSError as exc:
            print(f"Export error: {exc}")


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} ({APP_TAGLINE}) telecom recon framework",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {VERSION}")

    parser.add_argument("--no-shell", action="store_true", help="Run flags and exit without interactive shell")

    parser.add_argument("--profile", choices=sorted(PROFILE_PRESETS.keys()), help="Apply profile preset")
    parser.add_argument("--engine", choices=available_engines(), help="Set execution engine")
    parser.add_argument("--workers", type=int, help="Set worker count (1-64)")
    parser.add_argument(
        "--bulkview",
        choices=["full", "compact", "silent"],
        help="Set bulk output mode",
    )
    parser.add_argument(
        "--runbookstop",
        choices=["on", "off"],
        help="Toggle runbook stop-on-error behavior",
    )
    parser.add_argument("--ownerlookup", choices=["on", "off"], help="Toggle owner lookup")
    parser.add_argument("--autosummary", choices=["on", "off"], help="Toggle auto summary after bulk")
    parser.add_argument("--dedupe", choices=["on", "off"], help="Toggle bulk dedupe")

    parser.add_argument("--validate", help="Validate one phone number")
    parser.add_argument("--runbook", help="Execute command runbook file path")
    parser.add_argument("--scan", help="Scan one phone number")
    parser.add_argument("--scanfast", help="Scan one phone number without owner lookup")
    parser.add_argument("--bulk", help="Bulk scan file path")
    parser.add_argument("--bulkfast", help="Bulk scan file path without owner lookup")
    parser.add_argument("--whois", help="Owner OSINT lookup for one number")
    parser.add_argument("--whoisbulk", help="Bulk owner lookup file path")
    parser.add_argument("--searchresults", help="Search in-memory results")
    parser.add_argument(
        "--toprisks",
        nargs="?",
        const="10",
        help="Show top risk-ranked in-memory results",
    )
    parser.add_argument("--diff", help="Compare latest two scans for this number")

    parser.add_argument("--status", action="store_true", help="Show framework status")
    parser.add_argument("--summary", action="store_true", help="Show dataset summary")
    parser.add_argument("--tips", action="store_true", help="Show quick tips")
    parser.add_argument("--about", action="store_true", help="Show tool metadata")
    parser.add_argument("--lessons", action="store_true", help="Show learning modules")
    parser.add_argument(
        "--glossary",
        nargs="?",
        const="",
        help="Show glossary list or one term",
    )
    parser.add_argument(
        "--playbook",
        nargs="?",
        const="",
        help="Show playbook list or one playbook",
    )
    parser.add_argument("--clearresults", action="store_true", help="Clear in-memory results")

    parser.add_argument("--report", help="Write markdown report to path")
    parser.add_argument("--reportjson", help="Write JSON summary report to path")
    parser.add_argument("--exportjson", help="Write full results JSON to path")
    parser.add_argument("--saveconfig", help="Save settings to JSON path")
    parser.add_argument("--loadconfig", help="Load settings from JSON path")

    return parser


def has_flag_actions(args):
    return any(
        [
            args.profile,
            args.engine,
            args.workers is not None,
            args.bulkview,
            args.runbookstop,
            args.ownerlookup,
            args.autosummary,
            args.dedupe,
            args.validate,
            args.runbook,
            args.scan,
            args.scanfast,
            args.bulk,
            args.bulkfast,
            args.whois,
            args.whoisbulk,
            args.searchresults,
            args.toprisks is not None,
            args.diff,
            args.status,
            args.summary,
            args.tips,
            args.about,
            args.lessons,
            args.glossary is not None,
            args.playbook is not None,
            args.clearresults,
            args.report,
            args.reportjson,
            args.exportjson,
            args.saveconfig,
            args.loadconfig,
        ]
    )


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    cli = NumBreacherCLI()
    flagged = has_flag_actions(args)

    if flagged:
        show_banner()
        cli.run_flag_actions(args)
        if args.no_shell:
            return

    if args.no_shell and not flagged:
        print("No flag actions provided. Use --help.")
        return

    cli.run(show_startup=not flagged)


if __name__ == "__main__":
    main()
