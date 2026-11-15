"""Version 0.5 browser ecosystem management dialog."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QTabWidget, QVBoxLayout, QWidget, QInputDialog,
)

from ..profile_store import BUILTIN_EXTENSIONS, enabled_extensions, list_profiles


class EcosystemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gold & Diamond · Browser Ecosystem")
        self.setMinimumSize(620, 500)
        self.profile_to_activate = None
        self.new_profile_name = None
        self.extension_values = {}
        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)

        profiles = QWidget()
        profile_layout = QVBoxLayout(profiles)
        profile_layout.addWidget(QLabel("Keep browsing contexts separate with independent Chromium profile storage."))
        self.profile_list = QListWidget()
        self.profiles = list_profiles()
        for profile in self.profiles:
            self.profile_list.addItem(f'{profile["name"]}  ·  {profile["id"]}')
        profile_layout.addWidget(self.profile_list, 1)
        profile_buttons = QHBoxLayout()
        create = QPushButton("＋ Create profile")
        activate = QPushButton("Use selected profile")
        create.clicked.connect(self._create_profile)
        activate.clicked.connect(self._activate_profile)
        profile_buttons.addWidget(create)
        profile_buttons.addWidget(activate)
        profile_layout.addLayout(profile_buttons)
        tabs.addTab(profiles, "Profiles")

        extensions = QWidget()
        extension_layout = QVBoxLayout(extensions)
        extension_layout.addWidget(QLabel("Built-in browser tools. These are native features, not Chrome Web Store extensions."))
        current = enabled_extensions()
        for extension in BUILTIN_EXTENSIONS:
            check = QCheckBox(f'{extension["name"]} — {extension["description"]}')
            check.setChecked(extension["id"] in current)
            self.extension_values[extension["id"]] = check
            extension_layout.addWidget(check)
        extension_layout.addStretch(1)
        tabs.addTab(extensions, "Extension center")

        privacy = QWidget()
        privacy_layout = QVBoxLayout(privacy)
        privacy_layout.addWidget(QLabel(
            "<h3>Privacy controls</h3>"
            "<p>Clear this browser profile's HTTP cache and cookies, or remove recorded browsing history. "
            "This does not make browsing anonymous and does not erase data held by websites or your network.</p>"
            "<p>Private tabs use a temporary profile and are not included in saved sessions.</p>"
        ))
        self.clear_privacy = QPushButton("Clear this profile’s cache, cookies and local history")
        self.clear_privacy.clicked.connect(lambda: self.done(4))
        privacy_layout.addWidget(self.clear_privacy)
        privacy_layout.addStretch(1)
        tabs.addTab(privacy, "Privacy")

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        root.addLayout(buttons)

    def _create_profile(self):
        name, ok = QInputDialog.getText(self, "New profile", "Profile name:")
        if ok and name.strip():
            self.new_profile_name = name.strip()
            self.done(2)

    def _activate_profile(self):
        index = self.profile_list.currentRow()
        if 0 <= index < len(self.profiles):
            self.profile_to_activate = self.profiles[index]["id"]
            self.done(3)
