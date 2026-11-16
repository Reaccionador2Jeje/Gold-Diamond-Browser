"""Tests for GitHub release version comparison."""
import unittest

from browser.ui.update_dialog import _version_tuple


class UpdateVersionTests(unittest.TestCase):
    def test_version_comparison_uses_numeric_parts(self):
        self.assertGreater(_version_tuple("0.10.0"), _version_tuple("0.9.9"))
        self.assertGreater(_version_tuple("1.0.0"), _version_tuple("0.99.99"))
        self.assertEqual(_version_tuple("v0.5.0"), (0, 5, 0))


if __name__ == "__main__":
    unittest.main()
