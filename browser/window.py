"""Qt WebEngine browser window."""
from __future__ import annotations

from urllib.parse import urlparse

from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QLineEdit, QMainWindow, QTabWidget, QToolBar, QStatusBar,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from .memingo_bridge import resolve_url


class GoldDiamondWindow(QMainWindow):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.theme = config["theme"]
        self.setWindowTitle(f'{config["name"]} — {config["version"]}')
        window = config.get("window", {})
        self.resize(window.get("width", 1280), window.get("height", 820))
        self.setMinimumSize(
            window.get("minimum_width", 860),
            window.get("minimum_height", 560),
        )
        self.setStyleSheet(f"""
            QMainWindow, QTabWidget::pane {{ background: {self.theme["background"]}; color: {self.theme["text"]}; border: 0; }}
            QToolBar {{ background: {self.theme["surface"]}; border: 0; spacing: 7px; padding: 9px; }}
            QToolButton {{ color: {self.theme["text"]}; background: {self.theme["surface_alt"]}; border: 1px solid #30394a; border-radius: 9px; padding: 8px 12px; }}
            QToolButton:hover {{ border-color: {self.theme["gold"]}; }}
            QLineEdit {{ background: {self.theme["surface_alt"]}; color: {self.theme["text"]}; border: 1px solid #354154; border-radius: 11px; padding: 10px 14px; selection-background-color: {self.theme["diamond"]}; }}
            QLineEdit:focus {{ border: 1px solid {self.theme["gold"]}; }}
            QTabBar::tab {{ background: {self.theme["surface"]}; color: {self.theme["muted"]}; padding: 10px 18px; margin-right: 3px; border-top-left-radius: 8px; border-top-right-radius: 8px; }}
            QTabBar::tab:selected {{ color: {self.theme["gold"]}; background: {self.theme["surface_alt"]}; }}
            QStatusBar {{ background: {self.theme["surface"]}; color: {self.theme["muted"]}; }}
        """)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.sync_address)
        self.setCentralWidget(self.tabs)

        toolbar = QToolBar("Navigation")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.add_action(toolbar, "‹", "Back", self.go_back, "Alt+Left")
        self.add_action(toolbar, "›", "Forward", self.go_forward, "Alt+Right")
        self.add_action(toolbar, "↻", "Reload", self.reload_page, "Ctrl+R")
        self.add_action(toolbar, "⌂", "Home", self.go_home, "Alt+Home")

        self.address = QLineEdit()
        self.address.setPlaceholderText("Search or enter a web address")
        self.address.returnPressed.connect(self.navigate)
        toolbar.addWidget(self.address)

        self.add_action(toolbar, "＋", "New tab", self.new_tab, "Ctrl+T")
        self.add_action(toolbar, "✕", "Close tab", self.close_current_tab, "Ctrl+W")

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.new_tab(config.get("home_url", "https://www.google.com"))

    def add_action(self, toolbar: QToolBar, label: str, tooltip: str, callback, shortcut: str):
        action = QAction(label, self)
        action.setToolTip(tooltip)
        action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(callback)
        toolbar.addAction(action)

    def current_view(self) -> QWebEngineView | None:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, QWebEngineView) else None

    def new_tab(self, url: str | None = None):
        view = QWebEngineView()
        index = self.tabs.addTab(view, "New tab")
        self.tabs.setCurrentIndex(index)
        view.urlChanged.connect(lambda qurl, browser=view: self.update_address(qurl, browser))
        view.titleChanged.connect(lambda title, browser=view: self.update_title(title, browser))
        view.loadStarted.connect(lambda: self.status.showMessage("Loading…"))
        view.loadFinished.connect(lambda ok: self.status.showMessage("Ready" if ok else "Page load failed", 4000))
        view.setUrl(QUrl(url or self.config.get("home_url", "https://www.google.com")))
        self.address.setFocus()

    def navigate(self):
        try:
            url = resolve_url(self.address.text())
            view = self.current_view()
            if view:
                view.setUrl(QUrl(url))
        except Exception as exc:
            self.status.showMessage(f"Navigation error: {exc}", 6000)

    def update_address(self, qurl: QUrl, browser: QWebEngineView):
        if browser is self.current_view():
            self.address.setText(qurl.toString())

    def update_title(self, title: str, browser: QWebEngineView):
        index = self.tabs.indexOf(browser)
        if index >= 0:
            self.tabs.setTabText(index, (title or "New tab")[:24])

    def sync_address(self, _index: int):
        view = self.current_view()
        if view:
            self.address.setText(view.url().toString())

    def go_back(self):
        if self.current_view():
            self.current_view().back()

    def go_forward(self):
        if self.current_view():
            self.current_view().forward()

    def reload_page(self):
        if self.current_view():
            self.current_view().reload()

    def go_home(self):
        view = self.current_view()
        if view:
            view.setUrl(QUrl(self.config.get("home_url", "https://www.google.com")))

    def close_current_tab(self):
        self.close_tab(self.tabs.currentIndex())

    def close_tab(self, index: int):
        if self.tabs.count() <= 1:
            self.new_tab()
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if widget:
            widget.deleteLater()
        if self.tabs.count() == 0:
            self.new_tab()

