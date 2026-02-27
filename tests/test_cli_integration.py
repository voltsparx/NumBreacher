import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class TestCLIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.root = root

        candidates = [root / "numbreacher.py", root / "numBreacher.py"]
        for candidate in candidates:
            if candidate.exists():
                cls.entrypoint = candidate
                break
        else:
            raise RuntimeError("Could not locate NumBreacher entrypoint.")

    def setUp(self):
        self.generated_paths = [
            self.root / "output" / "test_report_summary.json",
            self.root / "config" / "test_framework_settings.json",
            self.root / "output" / "test_report.md",
            self.root / "output" / "test_runbook.txt",
        ]

    def tearDown(self):
        for path in self.generated_paths:
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                pass

    def run_cli(self, commands):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable, str(self.entrypoint)],
            input="\n".join(commands) + "\n",
            text=True,
            capture_output=True,
            cwd=self.root,
            env=env,
            timeout=180,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        return proc.stdout

    def run_cli_args(self, args):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable, str(self.entrypoint), *args],
            text=True,
            capture_output=True,
            cwd=self.root,
            env=env,
            timeout=180,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        return proc.stdout

    def test_unknown_command_suggestion(self):
        output = self.run_cli(["helo", "q"])
        self.assertIn("Did you mean 'help'?", output)

    def test_scanfast_summary_and_reportjson(self):
        output = self.run_cli(
            [
                "scanfast +14155552671",
                "summary",
                "reportjson output/test_report_summary.json",
                "q",
            ]
        )
        self.assertIn("[Reporter]", output)
        self.assertIn("JSON summary report generated", output)

        summary_path = self.root / "output" / "test_report_summary.json"
        self.assertTrue(summary_path.exists())
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertIn("risk_distribution", payload)
        self.assertIn("metadata", payload)

    def test_profile_save_load_status(self):
        output = self.run_cli(
            [
                "profile speed",
                "saveconfig config/test_framework_settings.json",
                "loadconfig config/test_framework_settings.json",
                "status",
                "q",
            ]
        )
        self.assertIn("Profile applied: speed", output)
        self.assertIn("Config saved to config/test_framework_settings.json", output)
        self.assertIn("Config loaded from config/test_framework_settings.json", output)
        self.assertIn("Profile        : speed", output)

    def test_flag_mode_scanfast_summary(self):
        output = self.run_cli_args(
            [
                "--scanfast",
                "+14155552671",
                "--summary",
                "--no-shell",
            ]
        )
        self.assertIn("[Reporter]", output)
        self.assertIn("Dataset Summary", output)

    def test_learning_and_analytics_commands(self):
        output = self.run_cli(
            [
                "scanfast +14155552671",
                "scanfast +14155552671",
                "searchresults 1415",
                "toprisks 1",
                "diff +14155552671",
                "glossary osint",
                "playbook quickstart",
                "lessons",
                "about",
                "q",
            ]
        )
        self.assertIn("Search Results for", output)
        self.assertIn("Top Risks", output)
        self.assertIn("Diff for +14155552671", output)
        self.assertIn("osint:", output)
        self.assertIn("Playbook: quickstart", output)
        self.assertIn("Learning Modules", output)
        self.assertIn("Version       :", output)

    def test_runbook_command(self):
        runbook_path = self.root / "output" / "test_runbook.txt"
        runbook_path.parent.mkdir(parents=True, exist_ok=True)
        runbook_path.write_text(
            "\n".join(
                [
                    "# test runbook",
                    "scanfast +14155552671",
                    "summary",
                ]
            ),
            encoding="utf-8",
        )

        output = self.run_cli([f'runbook "{runbook_path.as_posix()}"', "q"])
        self.assertIn("Runbook complete.", output)
        self.assertIn("Dataset Summary", output)

    def test_flag_mode_learning_commands(self):
        output = self.run_cli_args(
            [
                "--scanfast",
                "+14155552671",
                "--glossary",
                "osint",
                "--playbook",
                "quickstart",
                "--about",
                "--no-shell",
            ]
        )
        self.assertIn("osint:", output)
        self.assertIn("Playbook: quickstart", output)
        self.assertIn("Version       :", output)


if __name__ == "__main__":
    unittest.main()
