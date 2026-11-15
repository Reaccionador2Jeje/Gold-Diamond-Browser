"""Smoke tests for the Memingo-owned browser behavior."""
import unittest

from browser.memingo_bridge import load_config, resolve_url


class MemingoBrowserTests(unittest.TestCase):
    def test_configuration_is_loaded_from_memingo(self):
        config = load_config()
        self.assertEqual(config["name"], "Gold & Diamond Browser")
        self.assertEqual(config["version"], "0.1.0")
        self.assertIn("gold", config["theme"])

    def test_explicit_url_is_preserved(self):
        self.assertEqual(resolve_url("https://example.com"), "https://example.com")

    def test_domain_gets_https(self):
        self.assertEqual(resolve_url("example.com"), "https://example.com")

    def test_search_text_becomes_search_url(self):
        self.assertEqual(
            resolve_url("hello world"),
            "https://www.google.com/search?q=hello+world",
        )


if __name__ == "__main__":
    unittest.main()
