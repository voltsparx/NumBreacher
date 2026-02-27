import unittest

from core.dataset_tools import diff_number_history, quick_distribution, search_results, top_risks


class TestDatasetTools(unittest.TestCase):
    def setUp(self):
        self.results = [
            {
                "number": "+14155552671",
                "carrier": "Unknown",
                "risk": "Medium",
                "line_type": "VOIP",
                "voip": True,
                "owner": {"name": "Unknown"},
                "geo": {"Country": "United States", "Region": "CA"},
            },
            {
                "number": "+14155552671",
                "carrier": "AT&T",
                "risk": "High",
                "line_type": "MOBILE",
                "voip": False,
                "owner": {"name": "John Doe"},
                "geo": {"Country": "United States", "Region": "CA"},
            },
            {
                "number": "+447911123456",
                "carrier": "JT",
                "risk": "Low",
                "line_type": "MOBILE",
                "voip": False,
                "owner": {"name": "Alice"},
                "geo": {"Country": "Guernsey", "Region": "GG"},
            },
        ]

    def test_search_results(self):
        matches = search_results(self.results, "john")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["number"], "+14155552671")

    def test_top_risks(self):
        ranked = top_risks(self.results, limit=2)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["risk"], "High")

    def test_diff_number_history(self):
        diff = diff_number_history(self.results, "+14155552671")
        self.assertIsNotNone(diff)
        self.assertTrue(diff["changed"])
        self.assertIn("carrier", diff["changes"])
        self.assertIn("owner.name", diff["changes"])

    def test_quick_distribution(self):
        distribution = quick_distribution(self.results)
        self.assertEqual(distribution["risks"]["High"], 1)
        self.assertEqual(distribution["countries"]["United States"], 2)


if __name__ == "__main__":
    unittest.main()
