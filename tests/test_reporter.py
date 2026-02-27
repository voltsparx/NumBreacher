import unittest

from reporter.reporter import Reporter


class TestReporter(unittest.TestCase):
    def setUp(self):
        self.reporter = Reporter()
        self.sample_results = [
            {
                "number": "+14155552671",
                "risk": "Medium",
                "carrier": "Unknown",
                "voip": False,
                "line_type": "FIXED_LINE_OR_MOBILE",
                "owner": {"name": "Unknown", "confidence": "Low"},
                "geo": {"Country": "United States"},
            },
            {
                "number": "+447911123456",
                "risk": "Low",
                "carrier": "JT",
                "voip": False,
                "line_type": "MOBILE",
                "owner": {"name": "John Doe", "confidence": "Medium"},
                "geo": {"Country": "Guernsey"},
            },
        ]

    def test_single_scan_terminal(self):
        text = self.reporter.single_scan_terminal(self.sample_results[0])
        self.assertIn("[Reporter]", text)
        self.assertIn("Medium risk", text)

    def test_generate_markdown_report(self):
        report = self.reporter.generate_markdown_report(self.sample_results)
        self.assertIn("# Telecom Recon Report", report)
        self.assertIn("## Risk Distribution", report)

    def test_generate_json_summary(self):
        summary = self.reporter.generate_json_summary(
            self.sample_results,
            metadata={"engine": "async", "workers": 12, "elapsed_seconds": 1.23, "skipped": 1},
        )
        self.assertEqual(summary["metadata"]["engine"], "async")
        self.assertEqual(summary["metadata"]["workers"], 12)
        self.assertEqual(summary["metadata"]["scanned"], 2)
        self.assertEqual(summary["risk_distribution"]["medium"], 1)
        self.assertEqual(summary["risk_distribution"]["low"], 1)


if __name__ == "__main__":
    unittest.main()
