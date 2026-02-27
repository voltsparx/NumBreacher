import tempfile
import unittest
from pathlib import Path

from core.settings import FrameworkSettings


class TestFrameworkSettings(unittest.TestCase):
    def test_apply_profile_professional(self):
        settings = FrameworkSettings()
        settings.apply_profile("professional")
        self.assertEqual(settings.profile, "professional")
        self.assertEqual(settings.engine_name, "async")
        self.assertEqual(settings.max_workers, 16)
        self.assertTrue(settings.owner_lookup_enabled)
        self.assertEqual(settings.bulk_output_mode, "compact")
        self.assertTrue(settings.runbook_stop_on_error)

    def test_save_and_load_roundtrip(self):
        settings = FrameworkSettings()
        settings.apply_profile("speed")

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            settings.save(path)
            loaded = FrameworkSettings.load(path)

        self.assertEqual(loaded.profile, "speed")
        self.assertEqual(loaded.engine_name, "async")
        self.assertEqual(loaded.max_workers, 24)
        self.assertFalse(loaded.owner_lookup_enabled)
        self.assertEqual(loaded.bulk_output_mode, "silent")
        self.assertTrue(loaded.runbook_stop_on_error)


if __name__ == "__main__":
    unittest.main()
