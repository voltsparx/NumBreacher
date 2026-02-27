import unittest

from core.validator import validate_number


class TestValidator(unittest.TestCase):
    def test_validate_valid_number(self):
        valid, parsed = validate_number("+14155552671")
        self.assertTrue(valid)
        self.assertIsNotNone(parsed)

    def test_validate_invalid_number(self):
        valid, parsed = validate_number("not-a-number")
        self.assertFalse(valid)
        self.assertIsNone(parsed)

    def test_validate_empty_number(self):
        valid, parsed = validate_number("   ")
        self.assertFalse(valid)
        self.assertIsNone(parsed)


if __name__ == "__main__":
    unittest.main()
