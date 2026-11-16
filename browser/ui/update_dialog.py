"""GitHub Releases update checker for Gold & Diamond Browser."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from PySide6.QtCore import QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
)


RELEASE_API = "https://api.github.com/repos/Reaccionador2Jeje/Gold-Diamond-Browser/releases/latest"


def _version_tuple(value: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", value)
    return tuple(int(part) for part in numbers[:4])


class ReleaseCheckWorker(QThread):
    completed = Signal(dict)
    failed = Signal(str)

    def run(self):
        request = urllib.request.Request(
            RELEASE_API,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Gold-Diamond-Browser-Updater",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict) or payload.get("draft") or payload.get("prerelease"):
                raise ValueError("GitHub no devolvió una release estable válida.")
            tag = payload.get("tag_name", "")
            if not isinstance(tag, str) or not tag:
                raise ValueError("La release no contiene una versión válida.")
            assets = payload.get("assets", [])
            safe_assets = []
            if isinstance(assets, list):
                for asset in assets:
                    if isinstance(asset, dict):
                        name = asset.get("name")
                        url = asset.get("browser_download_url")
                        if isinstance(name, str) and isinstance(url, str) and url.startswith("https://github.com/"):
                            safe_assets.append({"name": name, "url": url})
            self.completed.emit({
                "version": tag.lstrip("v"),
                "tag": tag,
                "url": release_url,
                "assets": safe_assets,
                "published_at": payload.get("published_at", ""),
                "body": payload.get("body", ""),
            })
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            self.failed.emit(str(exc))


class UpdateDialog(QDialog):
    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = str(current_version or "0.0.0").lstrip("v")
        self.release_url = "https://github.com/Reaccionador2Jeje/Gold-Diamond-Browser/releases"
        self.assets = []
        self.worker = None
        self.setWindowTitle("Gold & Diamond · Updates")
        self.setMinimumSize(520, 300)
        root = QVBoxLayout(self)
        title = QLabel("<h2>◆ Gold &amp; Diamond Updates</h2>")
        root.addWidget(title)
        root.addWidget(QLabel(f"Installed version: <b>{self.current_version}</b>"))
        self.status = QLabel("Check GitHub for the latest stable release.")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.details = QLabel("")
        self.details.setWordWrap(True)
        root.addWidget(self.details)
        root.addStretch(1)
        buttons = QHBoxLayout()
        self.check_button = QPushButton("Check for updates")
        self.check_button.clicked.connect(self.check_updates)
        self.download_button = QPushButton("Open GitHub download")
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.open_release)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        buttons.addWidget(self.check_button)
        buttons.addWidget(self.download_button)
        buttons.addWidget(close)
        root.addLayout(buttons)

    def check_updates(self):
        if self.worker and self.worker.isRunning():
            return
        self.check_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.status.setText("Connecting securely to GitHub Releases…")
        self.details.clear()
        self.worker = ReleaseCheckWorker(self)
        self.worker.completed.connect(self._show_release)
        self.worker.failed.connect(self._show_error)
        self.worker.finished.connect(lambda: self.check_button.setEnabled(True))
        self.worker.start()

    def _show_release(self, release: dict):
        self.release_url = release["url"]
        self.assets = release["assets"]
        latest = release["version"]
        if _version_tuple(latest) > _version_tuple(self.current_version):
            self.status.setText(f"<span style='color:#e5b85c'><b>Update available: {latest}</b></span>")
            self.details.setText(
                f"Installed: {self.current_version}\nLatest stable: {latest}\n"
                "Open the GitHub release page to download the installer for your system."
            )
            self.download_button.setEnabled(True)
        else:
            self.status.setText("You are using the latest published stable version.")
            self.details.setText(f"Installed: {self.current_version}\nLatest stable: {latest}")
            self.download_button.setEnabled(True)

    def _show_error(self, message: str):
        self.status.setText("Could not check GitHub Releases.")
        self.details.setText(message[:500] + "\nCheck your internet connection and try again.")

    def open_release(self):
        QDesktopServices.openUrl(QUrl(self.release_url))

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.wait(2000)
        super().closeEvent(event)
