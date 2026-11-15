"""Smoke tests for Memingo-owned browser behavior."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from browser.memingo_bridge import (
    add_bookmark, clear_history, list_bookmarks, load_config, load_settings,
    load_session, record_history, remove_bookmark, resolve_url, save_setting, save_session,
    list_workspaces, save_workspace,
)


class MemingoBrowserTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        patcher = patch("browser.memingo_bridge.DATA_DIR", Path(self.temp_dir.name))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.temp_dir.cleanup)

    def test_configuration_is_loaded_from_memingo(self):
        config = load_config()
        self.assertEqual(config["name"], "Gold & Diamond Browser")
        self.assertEqual(config["version"], "0.5.0")
        self.assertIn("gold", config["theme"])

    def test_settings_have_memingo_defaults(self):
        settings = load_settings()
        self.assertEqual(settings["startup_page"], "https://gold-diamond.local/")
        self.assertIn("restore_session", settings)

    def test_setting_can_be_persisted(self):
        settings = save_setting("startup_page", "https://example.com")
        self.assertEqual(settings["startup_page"], "https://example.com")

    def test_session_is_saved_and_restored_by_memingo(self):
        save_session(["https://example.com", "not-a-url"])
        self.assertEqual(load_session(), ["https://example.com"])

    def test_theme_preference_is_persisted(self):
        settings = save_setting("theme", "midnight")
        self.assertEqual(settings["theme"], "midnight")

    def test_bookmarks_are_managed_by_memingo(self):
        add_bookmark("https://example.com", "Example")
        self.assertTrue(any(item["url"] == "https://example.com" for item in list_bookmarks()))
        remove_bookmark("https://example.com")
        self.assertFalse(any(item["url"] == "https://example.com" for item in list_bookmarks()))

    def test_history_records_visits(self):
        history = record_history("https://example.org", "Example Org")
        self.assertTrue(any(item["url"] == "https://example.org" for item in history))
        clear_history()

    def test_workspaces_are_saved_and_restored_by_memingo(self):
        save_workspace("Research", ["https://example.com", "not-a-url"])
        workspaces = list_workspaces()
        self.assertEqual(workspaces[-1]["name"], "Research")
        self.assertEqual(workspaces[-1]["tabs"], ["https://example.com"])

    def test_explicit_url_is_preserved(self):
        self.assertEqual(resolve_url("https://example.com"), "https://example.com")

    def test_domain_gets_https(self):
        self.assertEqual(resolve_url("example.com"), "https://example.com")

    def test_search_text_becomes_search_url(self):
        self.assertEqual(
            resolve_url("hello world"),
            "https://www.google.com/search?q=hello+world",
        )

    def test_custom_search_engine_is_used(self):
        self.assertEqual(
            resolve_url("hello world", "https://duckduckgo.com/?q="),
            "https://duckduckgo.com/?q=hello+world",
        )


if __name__ == "__main__":
    unittest.main()
