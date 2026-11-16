"""Download manager dialog for Gold & Diamond Browser."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QProgressBar, QHeaderView,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)


class DownloadManagerDialog(QDialog):
    """Live view and controls for QWebEngineDownloadRequest objects."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Manager · Gold & Diamond")
        self.resize(820, 460)
        self.setMinimumSize(620, 340)
        self._downloads: list[dict] = []

        layout = QVBoxLayout(self)
        heading = QLabel("◆  DOWNLOAD MANAGER")
        heading.setStyleSheet("font-size:16pt;font-weight:700;color:#e5b85c;padding:8px")
        layout.addWidget(heading)
        self.summary = QLabel("No downloads yet")
        layout.addWidget(self.summary)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["File", "Status", "Progress", "Size"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        controls = QHBoxLayout()
        self.pause_button = QPushButton("Pause")
        self.resume_button = QPushButton("Resume")
        self.cancel_button = QPushButton("Cancel")
        self.open_button = QPushButton("Open file")
        self.folder_button = QPushButton("Open folder")
        self.pause_button.clicked.connect(self.pause_selected)
        self.resume_button.clicked.connect(self.resume_selected)
        self.cancel_button.clicked.connect(self.cancel_selected)
        self.open_button.clicked.connect(self.open_selected)
        self.folder_button.clicked.connect(self.open_folder_selected)
        for button in (self.pause_button, self.resume_button, self.cancel_button,
                       self.open_button, self.folder_button):
            controls.addWidget(button)
        layout.addLayout(controls)
        self.table.itemSelectionChanged.connect(self._update_controls)
        self._update_controls()

    def add_download(self, request, path: Path):
        row = self.table.rowCount()
        self.table.insertRow(row)
        name = path.name
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem("Starting…"))
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setTextVisible(True)
        self.table.setCellWidget(row, 2, progress)
        self.table.setItem(row, 3, QTableWidgetItem("—"))
        entry = {"request": request, "path": path, "row": row, "progress": progress}
        self._downloads.append(entry)
        self.refresh(request)
        self.table.selectRow(row)
        self.summary.setText(f"{len(self._downloads)} download(s) in this session")
        return entry

    def refresh(self, request):
        entry = next((item for item in self._downloads if item["request"] is request), None)
        if entry is None:
            return
        row = entry["row"]
        received = int(request.receivedBytes())
        total = int(request.totalBytes())
        state = request.state()
        state_type = type(state)
        state_name = getattr(state, "name", str(state).split(".")[-1])
        if "DownloadCompleted" in state_name:
            label = "Completed"
        elif "DownloadCancelled" in state_name:
            label = "Cancelled"
        elif "DownloadInterrupted" in state_name:
            label = "Interrupted"
        elif "DownloadInProgress" in state_name:
            label = "Downloading"
        else:
            label = "Starting…"
        if total > 0:
            percent = max(0, min(100, int(received * 100 / total)))
            entry["progress"].setValue(percent)
            size_text = f"{self._format_size(received)} / {self._format_size(total)}"
        else:
            entry["progress"].setRange(0, 0 if label == "Downloading" else 100)
            size_text = self._format_size(received) if received else "Unknown"
        self.table.item(row, 1).setText(label)
        self.table.item(row, 3).setText(size_text)
        self._update_controls()

    @staticmethod
    def _format_size(value: int) -> str:
        amount = float(value)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if amount < 1024 or unit == "TB":
                return f"{amount:.1f} {unit}"
            amount /= 1024
        return f"{amount:.1f} TB"

    def _selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        return next((item for item in self._downloads if item["row"] == row), None)

    def _update_controls(self):
        entry = self._selected()
        if entry is None:
            for button in (self.pause_button, self.resume_button, self.cancel_button,
                           self.open_button, self.folder_button):
                button.setEnabled(False)
            return
        request = entry["request"]
        state_name = getattr(request.state(), "name", str(request.state()).split(".")[-1])
        finished = bool(request.isFinished())
        paused = bool(request.isPaused()) if hasattr(request, "isPaused") else False
        self.pause_button.setEnabled(not finished and not paused and "DownloadInProgress" in state_name)
        self.resume_button.setEnabled(not finished and paused)
        self.cancel_button.setEnabled(not finished)
        exists = entry["path"].is_file()
        self.open_button.setEnabled(exists)
        self.folder_button.setEnabled(entry["path"].parent.exists())

    def pause_selected(self):
        entry = self._selected()
        if entry:
            entry["request"].pause()
            self.refresh(entry["request"])

    def resume_selected(self):
        entry = self._selected()
        if entry:
            entry["request"].resume()
            self.refresh(entry["request"])

    def cancel_selected(self):
        entry = self._selected()
        if entry:
            entry["request"].cancel()
            self.refresh(entry["request"])

    def open_selected(self):
        entry = self._selected()
        if entry and entry["path"].is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(entry["path"])))

    def open_folder_selected(self):
        entry = self._selected()
        if entry:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(entry["path"].parent)))

    def showEvent(self, event):
        super().showEvent(event)
        for entry in self._downloads:
            self.refresh(entry["request"])
