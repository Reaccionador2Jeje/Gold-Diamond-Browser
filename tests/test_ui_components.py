"""Tests for the modular browser presentation layer."""
import unittest

from browser.ui.dashboard import build_dashboard
from browser.ui.theme import build_stylesheet, PALETTES


class BrowserUiTests(unittest.TestCase):
    def test_all_themes_have_a_stylesheet(self):
        self.assertEqual(set(PALETTES), {"graphite", "midnight", "pearl", "forest"})
        for name in PALETTES:
            with self.subTest(theme=name):
                stylesheet = build_stylesheet(name)
                self.assertIn("QMainWindow", stylesheet)
                self.assertIn("QTabBar::tab:selected", stylesheet)

    def test_every_palette_uses_black_surfaces(self):
        for name, palette in PALETTES.items():
            with self.subTest(theme=name):
                self.assertEqual(palette["bg"], "#000000")
                expected_fields = {
                    "graphite": "#080808",
                    "midnight": "#07090d",
                    "pearl": "#080808",
                    "forest": "#060a08",
                }
                self.assertEqual(palette["field"], expected_fields[name])
                stylesheet = build_stylesheet(name)
                self.assertIn("QDialog", stylesheet)
                self.assertIn("QTextBrowser", stylesheet)
                self.assertIn("QComboBox QAbstractItemView", stylesheet)

    def test_unknown_theme_falls_back_to_graphite(self):
        self.assertEqual(build_stylesheet("unknown"), build_stylesheet("graphite"))

    def test_dashboard_contains_clock_search_and_quick_launch(self):
        page = build_dashboard()
        self.assertIn('id="time"', page)
        self.assertIn('id="search"', page)
        self.assertIn("QUICK LAUNCH", page)
        self.assertIn("Internet Archive", page)
        self.assertIn("gold-diamond.local", page)
        self.assertIn("MADE BY ATDEV DEV", page)

    def test_dashboard_uses_selected_search_engine(self):
        page = build_dashboard(search_engine="https://duckduckgo.com/?q=")
        self.assertIn('data-search-url="https://duckduckgo.com/?q="', page)

    def test_dashboard_displays_saved_bookmarks_safely(self):
        page = build_dashboard(
            bookmarks=[{"url": "https://example.com", "title": "<Example>"}]
        )
        self.assertIn("&lt;Example&gt;", page)
        self.assertIn('href="https://example.com"', page)

    def test_dashboard_ignores_unsafe_bookmark_schemes(self):
        page = build_dashboard(
            bookmarks=[{"url": "javascript:alert(1)", "title": "Unsafe"}]
        )
        self.assertNotIn("javascript:alert", page)
        self.assertIn("Your saved pages will appear here.", page)

    def test_dashboard_ignores_malformed_bookmark_records(self):
        page = build_dashboard(bookmarks=[
            None,
            {"url": None, "title": "Broken"},
            {"url": "https://safe.example", "title": None},
        ])
        self.assertIn('href="https://safe.example"', page)
        self.assertNotIn("Broken", page)


if __name__ == "__main__":
    unittest.main()
