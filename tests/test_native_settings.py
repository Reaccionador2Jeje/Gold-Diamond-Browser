"""Offscreen tests for native settings and the optional AI assistant."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from browser.ai_assistant import AIAssistantDialog
from browser.ui.settings_dialog import SettingsDialog


class NativeSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_settings_dialog_collects_general_appearance_and_ai_preferences(self):
        dialog = SettingsDialog({
            "startup_page": "https://gold-diamond.local/",
            "search_engine": "https://www.google.com/search?q=",
            "restore_session": True,
            "theme": "graphite",
            "ai_base_url": "https://api.openai.com/v1",
            "ai_model": "gpt-4o-mini",
        })
        dialog.home_page.setText("gold-diamond.local")
        dialog.ai_model.setText("sample-model")
        dialog._save()
        self.assertEqual(dialog.values["startup_page"], "https://gold-diamond.local")
        self.assertEqual(dialog.values["ai_model"], "sample-model")
        self.assertEqual(dialog.values["theme"], "graphite")

    def test_ai_dialog_explains_missing_key_without_sending_request(self):
        previous = os.environ.pop("GDB_AI_API_KEY", None)
        try:
            dialog = AIAssistantDialog({"ai_model": "test-model"})
            dialog.prompt.setText("What can you do?")
            dialog.send_message()
            self.assertIn("Missing API key", dialog.status.text())
        finally:
            if previous is not None:
                os.environ["GDB_AI_API_KEY"] = previous


if __name__ == "__main__":
    unittest.main()
