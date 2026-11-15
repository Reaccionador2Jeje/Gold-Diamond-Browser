"""Premium Qt WebEngine interface for Gold & Diamond Browser."""
from __future__ import annotations

from html import escape
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QMainWindow, QMenu, QMessageBox, QProgressBar, QPushButton, QStatusBar,
    QTabWidget, QToolBar, QVBoxLayout, QWidget,
)
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView

from .memingo_bridge import (
    add_bookmark, clear_history, list_bookmarks, list_history, load_settings,
    record_history, resolve_url, save_setting,
)


ACCENT_GOLD = "#e5b85c"
ACCENT_BLUE = "#75d8e8"


class GoldDiamondWindow(QMainWindow):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.theme = config["theme"]
        self.settings = load_settings()
        self._download_connections = set()
        self.setWindowTitle(f'{config["name"]}  ◆  {config["version"]}')
        self.setWindowIconText("G◆D")
        window = config.get("window", {})
        self.resize(window.get("width", 1440), window.get("height", 920))
        self.setMinimumSize(980, 650)
        self.setStyleSheet(self._stylesheet())

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.sync_address)
        self.setCentralWidget(self.tabs)

        self._build_navigation()
        self._build_bookmark_bar()
        self._build_sidebar()
        self._build_status()
        self._build_menus()
        self._register_shortcuts()
        self.new_tab()

    def _stylesheet(self) -> str:
        return f"""
        QWidget {{ color: #edf2f8; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 10pt; }}
        QMainWindow, QTabWidget::pane {{ background: #0b0f17; border: 0; }}
        QToolBar {{ background: #111827; border: 0; spacing: 6px; padding: 8px 12px; }}
        QToolButton {{ color: #dce5ef; background: #1a2535; border: 1px solid #29384b;
            border-radius: 10px; padding: 8px 11px; }}
        QToolButton:hover {{ background: #25364a; border-color: {ACCENT_GOLD}; color: #fff; }}
        QLineEdit {{ background: #0d1420; color: #f4f7fb; border: 1px solid #34445a;
            border-radius: 13px; padding: 11px 15px; selection-background-color: {ACCENT_BLUE}; }}
        QLineEdit:focus {{ border: 1px solid {ACCENT_GOLD}; }}
        QTabBar::tab {{ background: #111827; color: #91a0b4; padding: 11px 18px;
            margin-right: 3px; border-top-left-radius: 10px; border-top-right-radius: 10px; }}
        QTabBar::tab:selected {{ color: {ACCENT_GOLD}; background: #202b3b; border-bottom: 2px solid {ACCENT_GOLD}; }}
        QTabBar::tab:hover {{ background: #1b293a; }}
        QStatusBar {{ background: #111827; color: #aab8c9; border-top: 1px solid #263448; }}
        QDockWidget {{ color: {ACCENT_GOLD}; background: #101827; border: 1px solid #263448; }}
        QDockWidget::title {{ background: #172235; padding: 10px; }}
        QListWidget {{ background: #101827; border: 0; outline: 0; padding: 6px; }}
        QListWidget::item {{ padding: 10px; border-radius: 7px; }}
        QListWidget::item:selected {{ background: #26364b; color: {ACCENT_GOLD}; }}
        QPushButton {{ background: #202e41; color: #edf2f8; border: 1px solid #34465d;
            border-radius: 9px; padding: 8px 12px; }}
        QPushButton:hover {{ border-color: {ACCENT_GOLD}; background: #293b52; }}
        QProgressBar {{ background: #1c293a; border: 0; border-radius: 3px; height: 4px; }}
        QProgressBar::chunk {{ background: {ACCENT_GOLD}; border-radius: 3px; }}
        """

    def _build_navigation(self):
        toolbar = QToolBar("Main navigation")
        toolbar.setMovable(False)
        toolbar.setObjectName("MainNavigation")
        self.addToolBar(toolbar)
        self._action(toolbar, "‹", "Back", self.go_back, "Alt+Left")
        self._action(toolbar, "›", "Forward", self.go_forward, "Alt+Right")
        self._action(toolbar, "↻", "Reload", self.reload_page, "Ctrl+R")
        self._action(toolbar, "⌂", "Home", self.go_home, "Alt+Home")
        self._action(toolbar, "★", "Bookmark this page", self.add_current_bookmark, "Ctrl+D")

        self.address = QLineEdit()
        self.address.setMinimumWidth(360)
        self.address.setPlaceholderText("  Search the web or enter an address")
        self.address.returnPressed.connect(self.navigate)
        toolbar.addWidget(self.address)
        self._action(toolbar, "Go", "Open address", self.navigate, "Return")
        self._action(toolbar, "＋", "New tab", self.new_tab, "Ctrl+T")
        self._action(toolbar, "Find", "Find text on this page", self.toggle_find, "Ctrl+F")
        self._action(toolbar, "−", "Zoom out", lambda: self.change_zoom(-0.1), "Ctrl+-")
        self._action(toolbar, "+", "Zoom in", lambda: self.change_zoom(0.1), "Ctrl++")
        self._action(toolbar, "Private", "Open an isolated private tab", self.private_window, "Ctrl+Shift+N")
        self._action(toolbar, "☰", "Toggle library sidebar", self.toggle_sidebar, "Ctrl+Shift+L")

        self.progress = QProgressBar()
        self.progress.setMaximumWidth(130)
        self.progress.setTextVisible(False)
        self.progress.hide()
        toolbar.addWidget(self.progress)

        self.bookmark_toolbar = QToolBar("Quick bookmarks")
        self.bookmark_toolbar.setMovable(False)
        self.bookmark_toolbar.setObjectName("QuickBookmarks")
        self.addToolBar(self.bookmark_toolbar)
        self.refresh_bookmark_bar()

    def _build_bookmark_bar(self):
        self.bookmark_toolbar.addAction("◆  Gold & Diamond")
        self.bookmark_toolbar.actions()[0].setEnabled(False)
        self.bookmark_toolbar.addSeparator()
        self.bookmark_toolbar.addAction("＋ Add current page", self.add_current_bookmark)
        self.bookmark_toolbar.addAction("All bookmarks  ▾", self.show_bookmarks)

    def _build_sidebar(self):
        self.sidebar = QDockWidget("YOUR LIBRARY  ◆", self)
        self.sidebar.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 12, 10, 12)
        heading = QLabel("Gold & Diamond")
        heading.setStyleSheet(f"font-size: 17pt; font-weight: 700; color: {ACCENT_GOLD}; padding: 8px;")
        subtitle = QLabel("Your browsing space")
        subtitle.setStyleSheet("color: #8999ae; padding: 0 8px 10px;")
        layout.addWidget(heading)
        layout.addWidget(subtitle)
        self.sidebar_list = QListWidget()
        self.sidebar_list.addItems(["⌂   Start page", "★   Bookmarks", "◷   History", "↓   Downloads"])
        self.sidebar_list.currentRowChanged.connect(self.sidebar_selected)
        layout.addWidget(self.sidebar_list)
        self.sidebar.setWidget(panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)
        self.sidebar.hide()

    def _build_status(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.security_label = QLabel("◆  READY")
        self.security_label.setStyleSheet(f"color: {ACCENT_BLUE}; padding: 0 8px;")
        self.status.addPermanentWidget(self.security_label)
        self.status.showMessage("Gold & Diamond Browser is ready")

    def _build_menus(self):
        bar = self.menuBar()
        bar.setStyleSheet("QMenuBar { background:#111827; color:#dce5ef; padding:5px; } QMenuBar::item:selected { background:#26364b; } QMenu { background:#172235; color:#edf2f8; border:1px solid #34465d; } QMenu::item:selected { background:#2b4059; }")
        file_menu = bar.addMenu("File")
        self._menu_action(file_menu, "New tab", self.new_tab, "Ctrl+T")
        self._menu_action(file_menu, "Close tab", self.close_current_tab, "Ctrl+W")
        self._menu_action(file_menu, "New private tab", self.private_window, "Ctrl+Shift+N")
        self._menu_action(file_menu, "Save page as PDF", self.save_page_pdf)
        file_menu.addSeparator()
        self._menu_action(file_menu, "Quit", self.close, "Ctrl+Q")

        edit_menu = bar.addMenu("Edit")
        self._menu_action(edit_menu, "Find on page", self.toggle_find, "Ctrl+F")
        self._menu_action(edit_menu, "Zoom in", lambda: self.change_zoom(0.1), "Ctrl++")
        self._menu_action(edit_menu, "Zoom out", lambda: self.change_zoom(-0.1), "Ctrl+-")
        self._menu_action(edit_menu, "Reset zoom", lambda: self.set_zoom(1.0), "Ctrl+0")

        view_menu = bar.addMenu("View")
        self._menu_action(view_menu, "Toggle sidebar", self.toggle_sidebar, "Ctrl+Shift+L")
        self._menu_action(view_menu, "Fullscreen", self.toggle_fullscreen, "F11")
        self._menu_action(view_menu, "Show bookmarks", self.show_bookmarks, "Ctrl+Shift+B")
        self._menu_action(view_menu, "Show history", self.show_history, "Ctrl+H")

        tools_menu = bar.addMenu("Tools")
        self._menu_action(tools_menu, "Set current page as startup page", self.set_startup_page, "Ctrl+Shift+H")
        self._menu_action(tools_menu, "Clear browsing history", self.clear_browsing_history)
        self._menu_action(tools_menu, "Save page as PDF", self.save_page_pdf)
        self._menu_action(tools_menu, "Browser settings", self.show_settings)

        help_menu = bar.addMenu("Help")
        self._menu_action(help_menu, "About Gold & Diamond", self.show_about)

    def _register_shortcuts(self):
        self._shortcut("Ctrl+Shift+R", self.reload_page)
        self._shortcut("Escape", self.close_find)

    def _action(self, toolbar, label, tooltip, callback, shortcut=None):
        action = QAction(label, self)
        action.setToolTip(tooltip)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(callback)
        toolbar.addAction(action)
        return action

    def _menu_action(self, menu, label, callback, shortcut=None):
        action = QAction(label, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(callback)
        menu.addAction(action)
        return action

    def _shortcut(self, sequence, callback):
        action = QAction(self)
        action.setShortcut(QKeySequence(sequence))
        action.triggered.connect(callback)
        self.addAction(action)

    def current_view(self) -> QWebEngineView | None:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, QWebEngineView) else None

    def new_tab(self, url: str | None = None, private: bool = False):
        view = QWebEngineView()
        view.setProperty("private_mode", private)
        if private:
            private_profile = QWebEngineProfile(self)
            private_page = QWebEnginePage(private_profile, view)
            view.setPage(private_page)
        index = self.tabs.addTab(view, "New tab")
        self.tabs.setCurrentIndex(index)
        view.urlChanged.connect(lambda qurl, browser=view: self.update_address(qurl, browser))
        view.titleChanged.connect(lambda title, browser=view: self.update_title(title, browser))
        view.loadStarted.connect(self.load_started)
        view.loadProgress.connect(self.progress.setValue)
        view.loadFinished.connect(lambda ok, browser=view: self.page_loaded(ok, browser))
        profile = view.page().profile()
        if id(profile) not in self._download_connections:
            profile.downloadRequested.connect(self.handle_download)
            self._download_connections.add(id(profile))
        if url:
            view.setUrl(QUrl(url))
        else:
            view.setHtml(self.start_page_html(), QUrl("https://gold-diamond.local/"))
            self.address.clear()
        self.address.setFocus()

    def start_page_html(self) -> str:
        tiles = [
            ("Search", "https://www.google.com", "⌕", "Search the web"),
            ("YouTube", "https://www.youtube.com", "▶", "Videos and creators"),
            ("Wikipedia", "https://www.wikipedia.org", "◇", "Explore knowledge"),
            ("GitHub", "https://github.com", "⌘", "Build something"),
            ("DuckDuckGo", "https://duckduckgo.com", "◈", "Private search"),
            ("Memingo", "https://github.com/Reaccionador2Jeje/Memingo", "M", "The language behind this browser"),
        ]
        cards = "".join(
            f'<a class="tile" href="{url}"><span class="glyph">{glyph}</span><b>{name}</b><small>{desc}</small></a>'
            for name, url, glyph, desc in tiles
        )
        return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
        <style>
        *{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(ellipse at 50% 0%,#26364d 0%,#111a29 38%,#090e17 80%);color:#f4f7fb;font-family:Segoe UI,Arial,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center}}
        main{{width:min(900px,90%);padding:60px 20px;text-align:center}} .mark{{font-size:44px;color:#e5b85c;text-shadow:0 0 35px #d5a84b55}} h1{{font-size:42px;letter-spacing:1px;margin:10px 0 8px}} h1 em{{font-style:normal;color:#e5b85c}} .sub{{color:#9eafc4;font-size:15px;margin-bottom:44px}} .line{{height:1px;width:100px;background:linear-gradient(90deg,transparent,#e5b85c,transparent);margin:22px auto 30px}}
        .grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;text-align:left}} .tile{{text-decoration:none;color:#f4f7fb;background:linear-gradient(145deg,#1b293c,#121c2b);border:1px solid #34465a;border-radius:17px;padding:22px;min-height:125px;transition:.18s}} .tile:hover{{border-color:#e5b85c;transform:translateY(-3px);background:#24364b}} .glyph{{display:block;font-size:26px;color:#75d8e8;margin-bottom:13px}} b{{display:block;font-size:15px}} small{{display:block;color:#94a6bb;margin-top:5px;font-size:12px}} footer{{margin-top:44px;color:#71839a;font-size:12px}} .spark{{color:#75d8e8}}
        @media(max-width:600px){{h1{{font-size:30px}}.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}main{{padding:30px 5px}}}}
        </style></head><body><main><div class="mark">◆</div><h1>GOLD <em>&</em> DIAMOND</h1><div class="sub">A brighter way to explore the web.</div><div class="line"></div><section class="grid">{cards}</section><footer>POWERED BY <span class="spark">MEMINGO</span> · CHROMIUM ENGINE · MADE TO EXPLORE</footer></main></body></html>"""

    def navigate(self):
        try:
            url = resolve_url(self.address.text(), self.settings.get("search_engine"))
            view = self.current_view()
            if view:
                view.setUrl(QUrl(url))
        except Exception as exc:
            self.status.showMessage(f"Navigation error: {exc}", 6000)

    def navigate_to(self, url: str):
        if self.current_view():
            self.current_view().setUrl(QUrl(url))

    def load_started(self):
        self.progress.setValue(0)
        self.progress.show()
        self.security_label.setText("◌  CONNECTING")

    def page_loaded(self, ok: bool, browser: QWebEngineView):
        if browser is self.current_view():
            self.progress.hide()
            mode = "  PRIVATE" if browser.property("private_mode") else ""
            self.security_label.setText(("◆  SECURE" if browser.url().scheme() == "https" else "◇  READY") + mode)
        self.status.showMessage("Page loaded" if ok else "Page could not be loaded", 4000)
        url = browser.url().toString()
        if ok and url.startswith(("https://", "http://")) and not browser.property("private_mode"):
            try:
                record_history(url, browser.title() or url)
            except Exception as exc:
                self.status.showMessage(f"History error: {exc}", 5000)

    def update_address(self, qurl: QUrl, browser: QWebEngineView):
        if browser is self.current_view():
            self.address.setText(qurl.toString())

    def update_title(self, title: str, browser: QWebEngineView):
        index = self.tabs.indexOf(browser)
        if index >= 0:
            self.tabs.setTabText(index, (title or "New tab")[:28])
            if browser is self.current_view():
                self.setWindowTitle(f"{title or 'Gold & Diamond'}  ◆  Gold & Diamond Browser")

    def sync_address(self, _index: int):
        view = self.current_view()
        if view and view.url().scheme() in ("http", "https"):
            self.address.setText(view.url().toString())
        else:
            self.address.clear()

    def _saved_menu(self, entries: list[dict], empty: str, title: str):
        menu = QMenu(title, self)
        if not entries:
            disabled = menu.addAction(empty)
            disabled.setEnabled(False)
        for item in reversed(entries):
            url = item.get("url", "")
            label = item.get("title") or url
            if url:
                action = menu.addAction(label[:55])
                action.setToolTip(url)
                action.triggered.connect(lambda checked=False, target=url: self.navigate_to(target))
        menu.addSeparator()
        menu.addAction("Open library sidebar", self.toggle_sidebar)
        menu.exec(self.mapToGlobal(self.rect().center()))

    def show_bookmarks(self):
        self._saved_menu(list_bookmarks(), "No bookmarks saved yet", "Your bookmarks")

    def show_history(self):
        self._saved_menu(list_history(), "No browsing history yet", "Recently visited")

    def refresh_bookmark_bar(self):
        if not hasattr(self, "bookmark_toolbar"):
            return
        self.bookmark_toolbar.clear()
        title = self.bookmark_toolbar.addAction("◆  FAVORITES")
        title.setEnabled(False)
        try:
            items = list_bookmarks()[-5:]
        except Exception:
            items = []
        for item in items:
            action = self.bookmark_toolbar.addAction((item.get("title") or item.get("url", "Page"))[:18])
            action.setToolTip(item.get("url", ""))
            action.triggered.connect(lambda checked=False, target=item.get("url", ""): self.navigate_to(target))
        self.bookmark_toolbar.addSeparator()
        self.bookmark_toolbar.addAction("＋ Save", self.add_current_bookmark)
        self.bookmark_toolbar.addAction("Library ▾", self.show_bookmarks)

    def add_current_bookmark(self):
        view = self.current_view()
        if not view:
            return
        url = view.url().toString()
        if not url.startswith(("https://", "http://")):
            self.status.showMessage("Open a website before bookmarking it", 4000)
            return
        try:
            add_bookmark(url, view.title() or url)
            self.refresh_bookmark_bar()
            self.status.showMessage("★  Added to your library", 4000)
        except Exception as exc:
            self.status.showMessage(f"Bookmark error: {exc}", 6000)

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def sidebar_selected(self, row: int):
        if row == 0:
            self.new_tab()
        elif row == 1:
            self.show_bookmarks()
        elif row == 2:
            self.show_history()
        elif row == 3:
            self.status.showMessage("Downloads are saved to your Downloads folder", 5000)

    def toggle_find(self):
        if not hasattr(self, "find_bar"):
            self.find_bar = QWidget()
            layout = QHBoxLayout(self.find_bar)
            layout.setContentsMargins(10, 6, 10, 6)
            self.find_input = QLineEdit()
            self.find_input.setPlaceholderText("Find in this page…")
            self.find_input.textChanged.connect(self.find_text)
            close = QPushButton("×")
            close.clicked.connect(self.close_find)
            layout.addWidget(QLabel("FIND"))
            layout.addWidget(self.find_input)
            layout.addWidget(close)
            self.addToolBarBreak()
            self.find_toolbar = QToolBar("Find")
            self.find_toolbar.addWidget(self.find_bar)
            self.addToolBar(self.find_toolbar)
            self.find_toolbar.hide()
        self.find_toolbar.show()
        self.find_input.setFocus()
        self.find_input.selectAll()

    def find_text(self, text: str):
        if self.current_view():
            self.current_view().findText(text)

    def close_find(self):
        if hasattr(self, "find_toolbar"):
            self.find_toolbar.hide()
            if self.current_view():
                self.current_view().findText("")

    def change_zoom(self, delta: float):
        view = self.current_view()
        if view:
            view.setZoomFactor(max(0.5, min(2.0, view.zoomFactor() + delta)))
            self.status.showMessage(f"Page zoom: {round(view.zoomFactor() * 100)}%", 2500)

    def set_zoom(self, value: float):
        if self.current_view():
            self.current_view().setZoomFactor(value)

    def handle_download(self, download: QWebEngineDownloadRequest):
        suggested = download.downloadFileName()
        target = Path.home() / "Downloads" / suggested
        target.parent.mkdir(parents=True, exist_ok=True)
        download.setDownloadDirectory(str(target.parent))
        download.setDownloadFileName(target.name)
        download.accept()
        self.status.showMessage(f"Downloading: {suggested}", 5000)
        download.isFinishedChanged.connect(
            lambda: self.status.showMessage(f"Download finished: {suggested}", 6000)
        )

    def clear_browsing_history(self):
        answer = QMessageBox.question(self, "Clear history", "Delete all recorded browsing history?")
        if answer == QMessageBox.StandardButton.Yes:
            clear_history()
            self.status.showMessage("Browsing history cleared", 4000)

    def show_settings(self):
        menu = QMenu("Quick settings", self)
        menu.addAction("Set current page as startup page", self.set_startup_page)
        menu.addAction("Google search", lambda: self.change_search("https://www.google.com/search?q="))
        menu.addAction("DuckDuckGo search", lambda: self.change_search("https://duckduckgo.com/?q="))
        menu.addAction("Bing search", lambda: self.change_search("https://www.bing.com/search?q="))
        menu.exec(self.mapToGlobal(self.rect().center()))

    def change_search(self, engine: str):
        self.settings = save_setting("search_engine", engine)
        self.status.showMessage("Search engine preference saved", 4000)

    def set_startup_page(self):
        view = self.current_view()
        if view and view.url().scheme() in ("http", "https"):
            self.settings = save_setting("startup_page", view.url().toString())
            self.status.showMessage("Startup page saved", 4000)

    def private_window(self):
        self.new_tab(private=True)
        self.status.showMessage("Private tab opened — browsing history is not recorded", 5000)

    def save_page_pdf(self):
        view = self.current_view()
        if not view:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save page as PDF", str(Path.home() / "Downloads" / "webpage.pdf"), "PDF files (*.pdf)"
        )
        if filename:
            view.page().printToPdf(filename)
            self.status.showMessage("Preparing PDF export…", 4000)

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def show_about(self):
        QMessageBox.about(
            self, "About Gold & Diamond Browser",
            "<h2 style='color:#e5b85c'>◆ Gold & Diamond Browser</h2>"
            "<p>A modern browsing experience powered by Chromium and Memingo.</p>"
            "<p><b>Memingo-First.</b> Built to explore, learn and create.</p>",
        )

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
        self.new_tab(self.settings.get("startup_page", self.config.get("home_url", "https://www.google.com")))

    def close_current_tab(self):
        self.close_tab(self.tabs.currentIndex())

    def close_tab(self, index: int):
        if self.tabs.count() <= 1:
            self.new_tab()
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if widget:
            widget.deleteLater()
