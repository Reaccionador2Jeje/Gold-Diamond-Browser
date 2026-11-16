"""Native settings window for Gold & Diamond Browser."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)


class SettingsDialog(QDialog):
    """Collect editable preferences; secrets are deliberately not stored here."""

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gold & Diamond · Settings")
        self.setMinimumSize(560, 430)
        self.values = dict(settings)

        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)

        general = QWidget()
        general_form = QFormLayout(general)
        self.home_page = QLineEdit(str(settings.get("startup_page", "https://gold-diamond.local/")))
        self.search_engine = QComboBox()
        engines = [
            ("Google", "https://www.google.com/search?q="),
            ("DuckDuckGo", "https://duckduckgo.com/?q="),
            ("Bing", "https://www.bing.com/search?q="),
        ]
        for label, url in engines:
            self.search_engine.addItem(label, url)
        current_engine = settings.get("search_engine", engines[0][1])
        selected = self.search_engine.findData(current_engine)
        self.search_engine.setCurrentIndex(max(0, selected))
        self.restore_session = QCheckBox("Restore regular tabs when the browser starts")
        self.restore_session.setChecked(bool(settings.get("restore_session", True)))
        general_form.addRow("Home page", self.home_page)
        general_form.addRow("Search engine", self.search_engine)
        general_form.addRow("", self.restore_session)
        tabs.addTab(general, "General")

        appearance = QWidget()
        appearance_form = QFormLayout(appearance)
        self.theme = QComboBox()
        for label, value in (
            ("Graphite Gold", "graphite"), ("Midnight Blue", "midnight"),
            ("Pearl Light", "pearl"), ("Emerald Forest", "forest"),
        ):
            self.theme.addItem(label, value)
        selected_theme = self.theme.findData(settings.get("theme", "graphite"))
        self.theme.setCurrentIndex(max(0, selected_theme))
        appearance_form.addRow("Color theme", self.theme)
        tabs.addTab(appearance, "Appearance")

        ai = QWidget()
        ai_form = QFormLayout(ai)
        self.ai_base_url = QLineEdit(str(settings.get("ai_base_url", "https://api.openai.com/v1")))
        self.ai_model = QLineEdit(str(settings.get("ai_model", "gpt-4o-mini")))
        note = QLabel(
            "Gold & Diamond AI uses an OpenAI-compatible chat API. "
            "Set GDB_AI_API_KEY in your operating system environment. "
            "The key is never saved in browser settings. API usage may have costs."
        )
        note.setWordWrap(True)
        ai_form.addRow("API base URL", self.ai_base_url)
        ai_form.addRow("Model", self.ai_model)
        ai_form.addRow(note)
        tabs.addTab(ai, "AI assistant")

        updates = QWidget()
        updates_layout = QVBoxLayout(updates)
        updates_layout.addWidget(QLabel("<h2>Gold &amp; Diamond Updates</h2>"))
        updates_layout.addWidget(QLabel(
            "Check GitHub Releases for the latest stable version. "
            "The official installers and release notes are hosted by AtDev Dev."
        ))
        updates_layout.addStretch(1)
        self.check_updates_button = QPushButton("Check for updates on GitHub")
        self.check_updates_button.clicked.connect(self._open_updates)
        updates_layout.addWidget(self.check_updates_button)
        tabs.addTab(updates, "Updates")

        about = QWidget()
        about_layout = QVBoxLayout(about)
        credits = QLabel(
            "<h2>◆ Gold &amp; Diamond Browser</h2>"
            "<p><b>Created by AtDev Dev</b></p>"
            "<p>Browser interface and Memingo-first application logic by AtDev Dev.</p>"
            "<p>Powered by Memingo and Qt WebEngine / Chromium.</p>"
            "<p>Project license: Apache License 2.0. See LICENSE in the source repository.</p>"
            "<p>Third-party components retain their own licenses and trademarks.</p>"
        )
        credits.setWordWrap(True)
        about_layout.addWidget(credits)
        about_layout.addStretch(1)
        tabs.addTab(about, "Credits & license")

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        save = QPushButton("Save settings")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        root.addLayout(buttons)

    def _open_updates(self):
        from .update_dialog import UpdateDialog
        owner = self.parent()
        version = owner.config.get("version", "0.0.0") if owner else "0.0.0"
        dialog = UpdateDialog(version, self)
        dialog.exec()

    def _save(self):
        home = self.home_page.text().strip() or "https://gold-diamond.local/"
        if not home.startswith(("https://", "http://")):
            home = "https://" + home
        base_url = self.ai_base_url.text().strip().rstrip("/")
        if not base_url.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            self.ai_base_url.setFocus()
            self.ai_base_url.selectAll()
            return
        model = self.ai_model.text().strip() or "gpt-4o-mini"
        self.values.update({
            "startup_page": home,
            "search_engine": self.search_engine.currentData(),
            "restore_session": self.restore_session.isChecked(),
            "theme": self.theme.currentData(),
            "ai_base_url": base_url,
            "ai_model": model,
        })
        self.accept()
