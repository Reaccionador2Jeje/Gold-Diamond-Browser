"""Smoke tests for Memingo-owned browser behavior."""
import unittest

from browser.memingo_bridge import (
    load_config, load_settings, resolve_url, save_setting,
)


class MemingoBrowserTests(unittest.TestCase):
    def test_configuration_is_loaded_from_memingo(self):
        config = load_config()
        self.assertEqual(config["name"], "Gold & Diamond Browser")
        self.assertEqual(config["version"], "0.1.0")
        self.assertIn("gold", config["theme"])

    def test_settings_have_memingo_defaults(self):
        settings = load_settings()
        self.assertEqual(settings["startup_page"], "https://www.google.com")
        self.assertIn("restore_session", settings)

    def test_setting_can_be_persisted(self):
        settings = save_setting("startup_page", "https://example.com")
        self.assertEqual(settings["startup_page"], "https://example.com")
        # Restore the default so this test is repeatable.
        save_setting("startup_page", "https://www.google.com")

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
