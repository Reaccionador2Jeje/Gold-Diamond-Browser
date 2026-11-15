import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from browser import profile_store


class ProfileStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Path(self.temp.name) / "ecosystem.json"
        self.patch = patch.object(profile_store, "STORE", self.store)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_create_profile_and_activate(self):
        profile = profile_store.create_profile("Work Space")
        self.assertEqual(profile["id"], "work-space")
        self.assertEqual(profile_store.active_profile_id(), "work-space")
        profile_store.set_active_profile("default")
        self.assertEqual(profile_store.active_profile_id(), "default")

    def test_profile_names_are_unique(self):
        first = profile_store.create_profile("Work")
        second = profile_store.create_profile("Work")
        self.assertNotEqual(first["id"], second["id"])

    def test_extension_preferences_are_validated(self):
        profile_store.set_extension_enabled("reader", False)
        self.assertNotIn("reader", profile_store.enabled_extensions())
        with self.assertRaises(ValueError):
            profile_store.set_extension_enabled("unknown", True)


if __name__ == "__main__":
    unittest.main()
