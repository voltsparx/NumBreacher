import unittest

from engines.factory import available_engines, create_engine
from engines.workers import scan_number_worker


def simple_worker(task):
    return {"ok": True, "number": task.get("number", "")}


class TestEngines(unittest.TestCase):
    def test_available_engines(self):
        engines = available_engines()
        self.assertIn("threading", engines)
        self.assertIn("parallel", engines)
        self.assertIn("async", engines)

    def test_threading_engine_scan_worker(self):
        engine = create_engine("threading")
        results = engine.run(
            scan_number_worker,
            [
                {"number": "+14155552671", "enable_owner_lookup": False},
                {"number": "invalid", "enable_owner_lookup": False},
            ],
            max_workers=2,
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["ok"])
        self.assertFalse(results[1]["ok"])

    def test_async_engine_scan_worker(self):
        engine = create_engine("async")
        results = engine.run(
            scan_number_worker,
            [
                {
                    "number": "+447911123456",
                    "enable_owner_lookup": False,
                    "render_output": False,
                }
            ],
            max_workers=2,
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["ok"])
        self.assertEqual(results[0]["output"], "")

    def test_parallel_engine_simple_worker(self):
        engine = create_engine("parallel")
        try:
            results = engine.run(
                simple_worker,
                [{"number": "+14155552671"}, {"number": "+447911123456"}],
                max_workers=2,
            )
        except Exception as exc:
            self.skipTest(f"Parallel engine not supported in this environment: {exc}")
            return

        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["ok"])
        self.assertTrue(results[1]["ok"])


if __name__ == "__main__":
    unittest.main()
