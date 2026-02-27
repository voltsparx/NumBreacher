import unittest

from learning.glossary import GLOSSARY
from learning.playbooks import PLAYBOOKS


class TestLearningModules(unittest.TestCase):
    def test_glossary_contains_core_terms(self):
        self.assertIn("osint", GLOSSARY)
        self.assertIn("bulkview", GLOSSARY)
        self.assertTrue(GLOSSARY["osint"])

    def test_playbooks_contain_commands(self):
        self.assertIn("quickstart", PLAYBOOKS)
        self.assertIn("incident_triage", PLAYBOOKS)
        self.assertGreater(len(PLAYBOOKS["quickstart"]), 0)


if __name__ == "__main__":
    unittest.main()
