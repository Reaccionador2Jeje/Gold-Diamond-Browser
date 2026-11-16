"""Premium Qt WebEngine interface for Gold & Diamond Browser."""
from __future__ import annotations

from html import escape
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QDockWidget, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QInputDialog,
    QMainWindow, QMenu, QMessageBox, QProgressBar, QPushButton, QStatusBar,
    QTabWidget, QToolBar, QVBoxLayout, QWidget, QSplitter,
)
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView

from .ai_assistant import AIAssistantDialog
from .profile_store import active_profile_id, create_profile, enabled_extensions, set_active_profile
from .ui.ecosystem_dialog import EcosystemDialog
from .ui.dashboard import build_dashboard
from .ui.settings_dialog import SettingsDialog
from .ui.theme import build_stylesheet

from .memingo_bridge import (
    add_bookmark, add_reading_item, clear_history, list_bookmarks, list_history,
    list_reading_list, load_settings, load_session, record_history, remove_bookmark,
    remove_reading_item, resolve_url, save_setting, save_session,
    list_workspaces, save_workspace,
)


ACCENT_GOLD = "#e5b85c"
ACCENT_BLUE = "#75d8e8"


class GoldDiamondWindow(QMainWindow):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.theme = config["theme"]
        self.settings = load_settings()
        self.theme_name = self.settings.get("theme", "graphite")
        self._download_connections = set()
        self.download_items = []
        self.download_manager = None
        self.closed_tabs: list[dict[str, str]] = []

        self.active_profile_id = active_profile_id()
        self._session_profiles_seen = {self.active_profile_id}
        self.browser_profiles = {}
        self.split_view: QWebEngineView | None = None
        self.split_panel: QWidget | None = None
        self.splitter: QSplitter | None = None
        self.split_address: QLineEdit | None = None
        self.setWindowTitle(f'{config["name"]}  ◆  {config["version"]}')
        icon_path = Path(__file__).resolve().parents[1] / "assets" / "gold-diamond-icon.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
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
        self.tabs.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.tabBar().customContextMenuRequested.connect(self.show_tab_context_menu)
        self.tabs.currentChanged.connect(self.sync_address)
        self.setCentralWidget(self.tabs)

        self._build_navigation()
        self._build_bookmark_bar()
        self._build_sidebar()
        self._build_status()
        self._build_menus()
        self._register_shortcuts()
        self.restore_saved_session()

    def _stylesheet(self) -> str:
        return build_stylesheet(self.theme_name)

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
        self._action(toolbar, "Reader", "Simplify the current page", self.toggle_reader_mode, "Ctrl+Shift+E")
        self._action(toolbar, "Translate", "Translate the current page", self.translate_page)
        self._action(toolbar, "Capture", "Save a screenshot of this page", self.save_screenshot)
        self._action(toolbar, "Private", "Open an isolated private tab", self.private_window, "Ctrl+Shift+N")
        self._action(toolbar, "Mute", "Mute or unmute this tab", self.toggle_tab_audio)
        self._action(toolbar, "Tabs", "Find and switch tabs", self.find_tab, "Ctrl+Shift+A")
        self._action(toolbar, "Downloads", "Open download manager", self.show_downloads, "Ctrl+J")
        self._action(toolbar, "Ask AI", "Ask Gold & Diamond AI", self.show_ai_assistant)
        self._action(toolbar, "Settings", "Configure Gold & Diamond Browser", self.show_settings)
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

    def _build_bookmark_bar(self):
        self.refresh_bookmark_bar()

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
        self._menu_action(view_menu, "Reader mode", self.toggle_reader_mode)
        self._menu_action(view_menu, "Translate page", self.translate_page)
        self._menu_action(view_menu, "Capture page screenshot", self.save_screenshot)
        self._menu_action(view_menu, "Toggle Split View", self.toggle_split_view, "Ctrl+Shift+V")

        spaces_menu = bar.addMenu("Workspaces")
        self._menu_action(spaces_menu, "Save current tabs as workspace…", self.save_current_workspace, "Ctrl+Shift+W")
        self._menu_action(spaces_menu, "Open workspace…", self.open_workspace)

        tools_menu = bar.addMenu("Tools")
        self._menu_action(tools_menu, "Set current page as startup page", self.set_startup_page, "Ctrl+Shift+H")
        self._menu_action(tools_menu, "Clear browsing history", self.clear_browsing_history)
        self._menu_action(tools_menu, "Download Manager", self.show_downloads, "Ctrl+J")
        self._menu_action(tools_menu, "Save page as PDF", self.save_page_pdf)
        self._menu_action(tools_menu, "Browser settings", self.show_settings)
        self._menu_action(tools_menu, "Ask Gold & Diamond AI", self.show_ai_assistant)
        self._menu_action(tools_menu, "Browser Ecosystem · Profiles · Extensions · Privacy", self.show_ecosystem_manager)
        self._menu_action(tools_menu, "Reopen closed tab", self.reopen_closed_tab)
        self._menu_action(tools_menu, "Find tab…", self.find_tab, "Ctrl+Shift+A")
        self._menu_action(tools_menu, "Mute / unmute current tab", self.toggle_tab_audio)
        self._menu_action(tools_menu, "Copy current page address", self.copy_current_url, "Ctrl+Shift+C")
        self._menu_action(tools_menu, "Save page HTML…", self.save_page_html)
        self._menu_action(tools_menu, "Copy page text", self.copy_page_text)
        self._menu_action(tools_menu, "Summarize this page with AI", self.summarize_page_with_ai)
        self._menu_action(tools_menu, "Save to Reading List", self.save_to_reading_list, "Ctrl+Shift+S")
        self._menu_action(tools_menu, "Open Reading List", self.show_reading_list, "Ctrl+Shift+R")
        self._menu_action(tools_menu, "Close tabs to the right", self.close_tabs_to_right)
        self._menu_action(tools_menu, "Duplicate current tab", lambda: self.duplicate_tab(self.tabs.currentIndex()))
        themes_menu = tools_menu.addMenu("Appearance")
        for theme_name, label in (
            ("graphite", "Graphite Gold"), ("midnight", "Midnight Blue"),
            ("pearl", "Pearl Light"), ("forest", "Emerald Forest"),
        ):
            self._menu_action(themes_menu, label, lambda selected=theme_name: self.change_theme(selected))

        help_menu = bar.addMenu("Help")\n        self._menu_action(help_menu, "Check for updates…", self.show_updates)
        self._menu_action(help_menu, "About Gold & Diamond", self.show_about)
        self._menu_action(help_menu, "Credits & licenses", self.show_credits)

    def _register_shortcuts(self):
        self._shortcut("Ctrl+Shift+R", self.show_reading_list)
        self._shortcut("Ctrl+R", self.reload_page)
        self._shortcut("Ctrl+Shift+S", self.save_to_reading_list)
        self._shortcut("Escape", self.close_find)
        self._shortcut("Ctrl+L", self.focus_address)
        self._shortcut("Ctrl+Shift+T", self.reopen_closed_tab)
        self._shortcut("Ctrl+J", self.show_downloads)
        self._shortcut("Ctrl+Shift+E", self.toggle_reader_mode)

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

    def current_profile_id(self) -> str:
        view = self.current_view()
        profile_id = view.property("gdb_profile_id") if view is not None else None
        return str(profile_id) if profile_id else self.active_profile_id

    def new_tab(
        self,
        url: str | None = None,
        private: bool = False,
        profile_id: str | None = None,
    ):
        view = QWebEngineView()
        view.setProperty("private_mode", private)
        view.setProperty("internal_home", False)
        if private:
            private_profile = QWebEngineProfile(self)
            private_page = QWebEnginePage(private_profile, view)
            view.setPage(private_page)
            view.setProperty("gdb_profile_id", None)
        else:
            profile_id = profile_id or self.active_profile_id
            self._session_profiles_seen.add(profile_id)
            view.setProperty("gdb_profile_id", profile_id)
            view.setPage(QWebEnginePage(self._persistent_profile(profile_id), view))
        index = self.tabs.addTab(view, "New tab")
        self.tabs.setCurrentIndex(index)
        view.urlChanged.connect(lambda qurl, browser=view: self.update_address(qurl, browser))
        view.titleChanged.connect(lambda title, browser=view: self.update_title(title, browser))
        view.iconChanged.connect(lambda icon, browser=view: self.update_icon(icon, browser))
        view.loadStarted.connect(self.load_started)
        view.loadProgress.connect(self.progress.setValue)
        view.loadFinished.connect(lambda ok, browser=view: self.page_loaded(ok, browser))
        profile = view.page().profile()
        if id(profile) not in self._download_connections:
            profile.downloadRequested.connect(self.handle_download)
            self._download_connections.add(id(profile))
        if not url or url.rstrip("/") == "https://gold-diamond.local":
            view.setProperty("internal_home", True)
            view.setHtml(self.start_page_html(), QUrl("https://gold-diamond.local/"))
            self.address.setText("gold-diamond.local")
        else:
            view.setUrl(QUrl(url))
        self.address.setFocus()

    def _persistent_profile(self, profile_id: str) -> QWebEngineProfile:
        if profile_id in self.browser_profiles:
            return self.browser_profiles[profile_id]
        from .memingo_bridge import DATA_DIR
        profile_dir = DATA_DIR / 'profiles' / profile_id
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile = QWebEngineProfile(profile_id, self)
        profile.setPersistentStoragePath(str(profile_dir / 'storage'))
        profile.setCachePath(str(profile_dir / 'cache'))
        # Keep authentication cookies and web storage across restarts and OAuth redirects.
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self.browser_profiles[profile_id] = profile
        return profile

    def start_page_html(self, profile_id: str | None = None) -> str:
        try:
            bookmarks = list_bookmarks(profile_id or self.current_profile_id())
        except Exception:
            bookmarks = []
        return build_dashboard(self.theme_name, bookmarks, self.settings.get('search_engine', 'https://www.google.com/search?q='))

    def navigate(self):
        try:
            typed = self.address.text().strip().rstrip("/")
            if typed in {"gold-diamond.local", "https://gold-diamond.local", "http://gold-diamond.local"}:
                view = self.current_view()
                if view:
                    view.setProperty("internal_home", True)
                    view.setHtml(self.start_page_html(), QUrl("https://gold-diamond.local/"))
                    self.address.setText("gold-diamond.local")
                return
            url = resolve_url(self.address.text(), self.settings.get("search_engine"))
            view = self.current_view()
            if view:
                view.setProperty("internal_home", False)
                view.setUrl(QUrl(url))
        except Exception as exc:
            self.status.showMessage(f"Navigation error: {exc}", 6000)

    def navigate_to(self, url: str):
        view = self.current_view()
        if view is None:
            return
        if not isinstance(url, str):
            self.status.showMessage("Invalid navigation address", 3500)
            return
        if url.rstrip("/") == "https://gold-diamond.local":
            view.setProperty("internal_home", True)
            view.setHtml(self.start_page_html(), QUrl("https://gold-diamond.local/"))
            self.address.setText("gold-diamond.local")
            return
        target = QUrl(url)
        if target.scheme() not in {"http", "https"} or not target.host():
            self.status.showMessage("Only HTTP and HTTPS addresses can be opened", 3500)
            return
        view.setProperty("internal_home", False)
        view.setUrl(target)

    def load_started(self):
        self.progress.setValue(0)
        self.progress.show()
        self.security_label.setText("◌  CONNECTING")

    def page_loaded(self, ok: bool, browser: QWebEngineView):
        if browser is self.current_view():
            self.progress.hide()
            mode = "  PRIVATE" if browser.property("private_mode") else ""
            host = browser.url().host().lower()
            state = "◆  HOME" if browser.property("internal_home") or host == "gold-diamond.local" else ("◆  SECURE" if browser.url().scheme() == "https" else "◇  READY")
            self.security_label.setText(state + mode)
        self.status.showMessage("Page loaded" if ok else "Page could not be loaded", 4000)
        url = browser.url().toString()
        if ok and url.startswith(("https://", "http://")) and "gold-diamond.local" not in url and not browser.property("private_mode"):
            try:
                record_history(url, browser.title() or url, browser.property("gdb_profile_id") or "default")
            except Exception as exc:
                self.status.showMessage(f"History error: {exc}", 5000)

    def update_address(self, qurl: QUrl, browser: QWebEngineView):
        if qurl.host().lower() == "gold-diamond.local":
            browser.setProperty("internal_home", True)
        elif qurl.scheme() not in {"", "about"}:
            browser.setProperty("internal_home", False)
        if browser is self.current_view():
            self.address.setText("gold-diamond.local" if browser.property("internal_home") else qurl.toString())

    def update_title(self, title: str, browser: QWebEngineView):
        index = self.tabs.indexOf(browser)
        if index >= 0:
            prefix = "◆ " if browser.property("pinned_tab") else ""
            self.tabs.setTabText(index, prefix + (title or "New tab")[:26])
            if browser is self.current_view():
                self.setWindowTitle(f"{title or 'Gold & Diamond'}  ◆  Gold & Diamond Browser")

    def update_icon(self, icon: QIcon, browser: QWebEngineView):
        index = self.tabs.indexOf(browser)
        if index >= 0 and not icon.isNull():
            self.tabs.setTabIcon(index, icon)

    def sync_address(self, _index: int):
        view = self.current_view()
        if view and (view.property("internal_home") or view.url().host().lower() == "gold-diamond.local"):
            self.address.setText("gold-diamond.local")
        elif view and view.url().scheme() in ("http", "https"):
            self.address.setText(view.url().toString())
        else:
            self.address.clear()
        self.refresh_bookmark_bar()

    def _saved_menu(self, entries: list[dict], empty: str, title: str):
        profile_id = self.current_profile_id()
        safe_entries = []
        for item in entries if isinstance(entries, list) else []:
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            if not isinstance(url, str) or not url.startswith(("https://", "http://")):
                continue
            label = item.get("title")
            safe_entries.append((url, label if isinstance(label, str) and label else url))
        menu = QMenu(title, self)
        if not safe_entries:
            disabled = menu.addAction(empty)
            disabled.setEnabled(False)
        for url, label in reversed(safe_entries):
            item_menu = menu.addMenu(label[:45])
            open_action = item_menu.addAction("Open")
            open_action.triggered.connect(lambda checked=False, target=url: self.navigate_to(target))
            remove_action = item_menu.addAction("Remove bookmark")
            remove_action.triggered.connect(
                lambda checked=False, target=url, owner=profile_id:
                    self.remove_saved_bookmark(target, owner)
            )
        menu.addSeparator()
        menu.addAction("Open library sidebar", self.toggle_sidebar)
        menu.exec(self.mapToGlobal(self.rect().center()))

    def show_bookmarks(self):
        try:
            self._saved_menu(list_bookmarks(self.current_profile_id()), "No bookmarks saved yet", "Your bookmarks")
        except Exception as exc:
            self.status.showMessage(f"Could not load bookmarks: {exc}", 5000)

    def show_history(self):
        try:
            self._saved_menu(list_history(self.current_profile_id()), "No browsing history yet", "Recently visited")
        except Exception as exc:
            self.status.showMessage(f"Could not load history: {exc}", 5000)

    def save_to_reading_list(self):
        view = self.current_view()
        if not view:
            return
        url = view.url().toString()
        if not url.startswith(("https://", "http://")):
            self.status.showMessage("Open a website before saving it", 3500)
            return
        try:
            add_reading_item(url, view.title() or url)
            self.status.showMessage("Saved to Reading List · Ctrl+Shift+R to open", 4000)
        except Exception as exc:
            self.status.showMessage(f"Reading List error: {exc}", 5000)

    def show_reading_list(self):
        try:
            entries = list_reading_list()
        except Exception as exc:
            self.status.showMessage(f"Could not load Reading List: {exc}", 5000)
            return
        entries = entries if isinstance(entries, list) else []
        menu = QMenu("Reading List · Read later", self)
        if not entries:
            empty = menu.addAction("No saved pages yet")
            empty.setEnabled(False)
        safe_entries = [
            item for item in entries
            if isinstance(item, dict)
            and isinstance(item.get("url"), str)
            and item["url"].startswith(("https://", "http://"))
        ]
        for item in reversed(safe_entries):
            url = item["url"]
            title = item.get("title")
            label = title if isinstance(title, str) and title else url
            submenu = menu.addMenu(label[:48])
            submenu.addAction("Open page", lambda target=url: self.navigate_to(target))
            submenu.addAction("Remove from Reading List", lambda target=url: self.remove_reading_item_entry(target))
        menu.addSeparator()
        menu.addAction("Save current page", self.save_to_reading_list)
        menu.exec(self.mapToGlobal(self.rect().center()))

    def remove_reading_item_entry(self, url: str):
        try:
            remove_reading_item(url)
            self.status.showMessage("Removed from Reading List", 3000)
        except Exception as exc:
            self.status.showMessage(f"Could not remove saved page: {exc}", 5000)


    def save_current_workspace(self):
        urls = []
        for index in range(self.tabs.count()):
            view = self.tabs.widget(index)
            if not isinstance(view, QWebEngineView) or view.property("private_mode"):
                continue
            url = view.url().toString()
            if url.startswith(("https://", "http://")) and "gold-diamond.local" not in url:
                urls.append(url)
        if not urls:
            self.status.showMessage("Open at least one regular website before saving a workspace", 4000)
            return
        name, accepted = QInputDialog.getText(self, "Save workspace", "Workspace name:")
        if not accepted or not name.strip():
            return
        try:
            save_workspace(name.strip(), urls)
            self.status.showMessage(f'Workspace "{name.strip()}" saved · {len(urls)} tabs', 4000)
        except Exception as exc:
            QMessageBox.warning(self, "Workspaces", f"Could not save workspace: {exc}")

    def open_workspace(self):
        try:
            workspaces = list_workspaces()
        except Exception as exc:
            QMessageBox.warning(self, "Workspaces", f"Could not load workspaces: {exc}")
            return
        workspaces = workspaces if isinstance(workspaces, list) else []
        valid = [
            item for item in workspaces
            if isinstance(item, dict) and isinstance(item.get("tabs"), list)
            and any(isinstance(url, str) and url.startswith(("https://", "http://")) for url in item["tabs"])
        ]
        if not valid:
            self.status.showMessage("No saved workspaces yet", 3500)
            return
        labels = [
            f'{item.get("name") if isinstance(item.get("name"), str) and item.get("name") else "Workspace"} · {len(item["tabs"])} tabs'
            for item in valid
        ]
        selected, accepted = QInputDialog.getItem(
            self, "Open workspace", "Choose a saved workspace:", labels, 0, False
        )
        if not accepted:
            return
        workspace = valid[labels.index(selected)]
        urls = [
            url for url in workspace["tabs"]
            if isinstance(url, str) and url.startswith(("https://", "http://"))
        ]
        for url in urls:
            self.new_tab(url)
        self.status.showMessage(f'Workspace "{workspace.get("name") or "Workspace"}" opened', 4000)

    def toggle_split_view(self):
        if self.splitter is not None:
            self.setCentralWidget(self.tabs)
            if self.split_view is not None:
                self.split_view.deleteLater()
            if self.splitter is not None:
                self.splitter.deleteLater()
            self.split_view = None
            self.split_panel = None
            self.splitter = None
            self.split_address = None
            self.status.showMessage("Split View closed", 3000)
            return

        source = self.current_view()
        if source is None:
            self.status.showMessage("Open a tab before enabling Split View", 3500)
            return

        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)
        panel_layout.setSpacing(6)
        header = QHBoxLayout()
        header.addWidget(QLabel("◆  SPLIT VIEW"))
        address = QLineEdit()
        address.setPlaceholderText("Search or enter an address for this pane")
        address.setText(source.url().toString())
        address.returnPressed.connect(self.navigate_split_view)
        header.addWidget(address, 1)
        close_button = QPushButton("×")
        close_button.setToolTip("Close Split View")
        close_button.clicked.connect(self.toggle_split_view)
        header.addWidget(close_button)
        panel_layout.addLayout(header)

        view = QWebEngineView()
        view.setProperty("private_mode", bool(source.property("private_mode")))
        view.setProperty("gdb_profile_id", source.property("gdb_profile_id"))
        view.setProperty("internal_home", bool(source.property("internal_home")))
        view.setPage(QWebEnginePage(source.page().profile(), view))
        view.urlChanged.connect(lambda qurl, field=address: field.setText(qurl.toString()))
        view.loadFinished.connect(lambda ok, browser=view: self.page_loaded(ok, browser))
        panel_layout.addWidget(view, 1)

        profile = view.page().profile()
        if id(profile) not in self._download_connections:
            profile.downloadRequested.connect(self.handle_download)
            self._download_connections.add(id(profile))

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.tabs)
        splitter.addWidget(panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        self.setCentralWidget(splitter)

        self.split_view = view
        self.split_panel = panel
        self.splitter = splitter
        self.split_address = address
        if source.property("internal_home"):
            view.setHtml(self.start_page_html(), QUrl("https://gold-diamond.local/"))
        else:
            view.setUrl(source.url())
        self.status.showMessage("Split View enabled · navigate independently in the right pane", 4500)

    def navigate_split_view(self):
        if self.split_view is None or self.split_address is None:
            return
        try:
            url = resolve_url(self.split_address.text(), self.settings.get("search_engine"))
            self.split_view.setProperty("internal_home", False)
            self.split_view.setUrl(QUrl(url))
        except Exception as exc:
            self.status.showMessage(f"Split View navigation error: {exc}", 5000)

    def remove_saved_bookmark(self, url: str, profile_id: str | None = None):
        try:
            remove_bookmark(url, profile_id or self.current_profile_id())
            self.refresh_bookmark_bar()
            self.status.showMessage("Bookmark removed", 3500)
        except Exception as exc:
            self.status.showMessage(f"Could not remove bookmark: {exc}", 5000)

    def refresh_bookmark_bar(self):
        if not hasattr(self, "bookmark_toolbar"):
            return
        self.bookmark_toolbar.clear()
        title = self.bookmark_toolbar.addAction("◆  FAVORITES")
        title.setEnabled(False)
        try:
            items = list_bookmarks(self.current_profile_id())[-5:]
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
            add_bookmark(url, view.title() or url, self.current_profile_id())
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
            self.show_downloads()

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

    def _ensure_download_manager(self):
        if self.download_manager is None:
            from .ui.download_manager import DownloadManagerDialog
            self.download_manager = DownloadManagerDialog(self)
        return self.download_manager

    def handle_download(self, download: QWebEngineDownloadRequest):
        """Accept downloads into the user's Downloads folder and track them live."""
        try:
            download_dir = Path.home() / "Downloads"
            download_dir.mkdir(parents=True, exist_ok=True)
            suggested = Path(download.downloadFileName() or "download").name
            if not suggested or suggested in {".", ".."}:
                suggested = "download"
            target = download_dir / suggested
            stem, suffix = target.stem, target.suffix
            counter = 1
            while target.exists():
                target = download_dir / f"{stem} ({counter}){suffix}"
                counter += 1

            download.setDownloadDirectory(str(download_dir))
            download.setDownloadFileName(target.name)
            manager = self._ensure_download_manager()
            manager.add_download(download, target)

            for signal_name in ("receivedBytesChanged", "totalBytesChanged", "stateChanged", "isFinishedChanged"):
                signal = getattr(download, signal_name, None)
                if signal is not None:
                    signal.connect(lambda *args, request=download: manager.refresh(request))

            download.accept()
            self.download_items.append({"name": target.name, "path": str(target), "state": "Downloading"})
            self.status.showMessage(f"Download started: {target.name}", 5000)
            manager.show()
            manager.raise_()
            manager.activateWindow()
        except Exception as exc:
            self.status.showMessage(f"Could not start download: {exc}", 7000)
            QMessageBox.warning(self, "Download error", f"Gold & Diamond could not start this download.\\n\\n{exc}")

    def download_finished(self, download, name: str):
        state = "Completed" if download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted else "Failed"
        for item in reversed(self.download_items):
            if item["name"] == name and item["state"] == "Downloading":
                item["state"] = state
                break
        if self.download_manager is not None:
            self.download_manager.refresh(download)
        self.status.showMessage(f"{name}: {state.lower()}", 5000)

    def show_downloads(self):
        manager = self._ensure_download_manager()
        manager.show()
        manager.raise_()
        manager.activateWindow()

    def open_download_folder(self, path: str):
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).parent)))

    def clear_browsing_history(self):
        answer = QMessageBox.question(self, "Clear history", "Delete all recorded browsing history for this tab’s profile?")
        if answer == QMessageBox.StandardButton.Yes:
            try:
                clear_history(self.current_profile_id())
                self.status.showMessage("Browsing history cleared", 4000)
            except Exception as exc:
                self.status.showMessage(f"Could not clear history: {exc}", 5000)

    def show_ecosystem_manager(self):
        dialog = EcosystemDialog(self)
        result = dialog.exec()
        try:
            for extension_id, checkbox in dialog.extension_values.items():
                from .profile_store import set_extension_enabled
                set_extension_enabled(extension_id, checkbox.isChecked())
            if dialog.new_profile_name:
                profile = create_profile(dialog.new_profile_name)
                self.active_profile_id = profile['id']
                self._session_profiles_seen.add(self.active_profile_id)
                self.status.showMessage('Profile created; new tabs use it', 4500)
            elif dialog.profile_to_activate:
                set_active_profile(dialog.profile_to_activate)
                self.active_profile_id = dialog.profile_to_activate
                self._session_profiles_seen.add(self.active_profile_id)
                self.refresh_bookmark_bar()
                self.status.showMessage('Active profile changed; existing tabs keep their original profile', 5000)
            if result == 4:
                self.clear_profile_data()
        except Exception as exc:
            QMessageBox.warning(self, 'Browser Ecosystem', f'Could not apply changes: {exc}')

    def clear_profile_data(self):
        profile = self._persistent_profile(self.active_profile_id)
        profile.clearHttpCache()
        profile.cookieStore().deleteAllCookies()
        try:
            clear_history(self.active_profile_id)
        except Exception:
            pass
        self.status.showMessage('Cache, cookies and local browsing history cleared', 5000)

    def show_updates(self):
        from .ui.update_dialog import UpdateDialog
        dialog = UpdateDialog(self.config.get("version", "0.0.0"), self)
        dialog.exec()

    def show_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return
        try:
            for key, value in dialog.values.items():
                if key in {"startup_page", "search_engine", "restore_session", "theme", "ai_base_url", "ai_model"}:
                    self.settings = save_setting(key, value)
            self.theme_name = self.settings.get("theme", self.theme_name)
            self.setStyleSheet(self._stylesheet())
            self.status.showMessage("Settings saved", 4000)
        except Exception as exc:
            QMessageBox.warning(self, "Settings", f"Could not save settings: {exc}")

    def show_ai_assistant(self):
        dialog = AIAssistantDialog(self.settings, self)
        dialog.exec()

    def summarize_page_with_ai(self):
        view = self.current_view()
        if not view:
            return
        self.status.showMessage("Reading page content for Gold & Diamond AI…", 3000)

        def open_context(text):
            if not text or not text.strip():
                self.status.showMessage("No readable page text was found", 3500)
                return
            dialog = AIAssistantDialog(self.settings, self, page_context=text[:20000])
            dialog.exec()

        view.page().runJavaScript("document.body ? document.body.innerText : ''", open_context)

    def show_credits(self):
        QMessageBox.about(
            self, "Credits & licenses",
            "<h2 style='color:#e5b85c'>◆ Gold &amp; Diamond Browser</h2>"
            "<p><b>Created by AtDev Dev.</b></p>"
            "<p>Application interface and Memingo-first browser logic by AtDev Dev.</p>"
            "<p>Powered by Memingo and Qt WebEngine / Chromium.</p>"
            "<p>Gold &amp; Diamond Browser is distributed under the Apache License 2.0. "
            "See the LICENSE file in the source repository.</p>"
            "<p>Third-party components retain their respective licenses and trademarks.</p>",
        )

    def change_theme(self, theme_name: str):
        if theme_name not in {"graphite", "midnight", "pearl", "forest"}:
            return
        try:
            self.settings = save_setting("theme", theme_name)
            self.theme_name = theme_name
            self.setStyleSheet(self._stylesheet())
            self.status.showMessage(f"Theme changed to {theme_name}", 4000)
        except Exception as exc:
            self.status.showMessage(f"Could not save theme: {exc}", 5000)

    def restore_saved_session(self):
        urls = []
        if self.settings.get("restore_session", True):
            try:
                urls = load_session(self.active_profile_id)
            except Exception as exc:
                self.status.showMessage(f"Session restore unavailable: {exc}", 5000)
        valid = [url for url in urls if isinstance(url, str) and url.startswith(("https://", "http://"))]
        if valid:
            for url in valid:
                self.new_tab(url)
        else:
            self.new_tab(self.settings.get("startup_page") or self.config.get("home_url"))

    def persist_session(self):
        sessions: dict[str, list[str]] = {}
        for index in range(self.tabs.count()):
            view = self.tabs.widget(index)
            if not isinstance(view, QWebEngineView) or view.property("private_mode"):
                continue
            profile_id = view.property("gdb_profile_id") or "default"
            url = view.url().toString()
            if url.startswith(("https://", "http://")) and "gold-diamond.local" not in url:
                sessions.setdefault(profile_id, []).append(url)
        try:
            for profile_id in self._session_profiles_seen:
                save_session(sessions.get(profile_id, []), profile_id)
        except Exception as exc:
            self.status.showMessage(f"Could not save session: {exc}", 5000)

    def focus_address(self):
        self.address.setFocus()
        self.address.selectAll()

    def show_tab_context_menu(self, position):
        tab_bar = self.tabs.tabBar()
        index = tab_bar.tabAt(position)
        menu = QMenu(self)
        if index < 0:
            menu.addAction("New tab", self.new_tab)
            menu.addAction("Reopen closed tab", self.reopen_closed_tab)
        else:
            view = self.tabs.widget(index)
            menu.addAction("Duplicate tab", lambda: self.duplicate_tab(index))
            pin_text = "Unpin tab" if view.property("pinned_tab") else "Pin tab"
            menu.addAction(pin_text, lambda: self.toggle_pin_tab(index))
            menu.addAction("Reload tab", view.reload)
            menu.addSeparator()
            menu.addAction("Close tab", lambda: self.close_tab(index))
            menu.addAction("Close other tabs", lambda: self.close_other_tabs(index))
            menu.addAction("New tab", self.new_tab)
            menu.addAction("Reopen closed tab", self.reopen_closed_tab)
        menu.exec(tab_bar.mapToGlobal(position))

    def duplicate_tab(self, index: int):
        view = self.tabs.widget(index)
        if not isinstance(view, QWebEngineView):
            return
        url = view.url().toString()
        private = bool(view.property("private_mode"))
        self.new_tab(
            url if url.startswith(("https://", "http://")) else None,
            private=private,
            profile_id=view.property("gdb_profile_id") or self.active_profile_id,
        )

    def toggle_pin_tab(self, index: int):
        view = self.tabs.widget(index)
        if not isinstance(view, QWebEngineView):
            return
        pinned = not bool(view.property("pinned_tab"))
        view.setProperty("pinned_tab", pinned)
        title = view.title() or "New tab"
        self.tabs.setTabText(index, ("◆ " if pinned else "") + title[:26])
        self.status.showMessage("Tab pinned" if pinned else "Tab unpinned", 2500)

    def close_other_tabs(self, keep_index: int):
        for index in reversed(range(self.tabs.count())):
            if index != keep_index:
                self.close_tab(index)

    def close_tabs_to_right(self):
        current = self.tabs.currentIndex()
        if current < 0:
            return
        for index in reversed(range(current + 1, self.tabs.count())):
            self.close_tab(index)
        self.status.showMessage("Tabs to the right closed", 3000)

    def find_tab(self):
        entries = []
        for index in range(self.tabs.count()):
            view = self.tabs.widget(index)
            if isinstance(view, QWebEngineView):
                title = view.title() or "New tab"
                host = view.url().host()
                label = f"{index + 1}. {title[:55]}" + (f" — {host}" if host else "")
                entries.append((label, index))
        if not entries:
            return
        labels = [label for label, _ in entries]
        selected, accepted = QInputDialog.getItem(
            self, "Tab switcher", "Find or select an open tab:", labels, self.tabs.currentIndex(), False
        )
        if accepted:
            for label, index in entries:
                if label == selected:
                    self.tabs.setCurrentIndex(index)
                    break

    def toggle_tab_audio(self):
        view = self.current_view()
        if not view:
            return
        muted = not bool(view.property("gdb_audio_muted"))
        view.page().setAudioMuted(muted)
        view.setProperty("gdb_audio_muted", muted)
        self.status.showMessage("Tab muted" if muted else "Tab audio enabled", 3000)

    def copy_current_url(self):
        view = self.current_view()
        if not view:
            return
        url = view.url().toString()
        if url.startswith(("https://", "http://")):
            QApplication.clipboard().setText(url)
            self.status.showMessage("Page address copied", 2500)

    def save_page_html(self):
        view = self.current_view()
        if not view:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save page HTML", str(Path.home() / "Downloads" / "webpage.html"),
            "HTML files (*.html)"
        )
        if not filename:
            return
        def write_html(source):
            try:
                Path(filename).write_text(source or "", encoding="utf-8")
                self.status.showMessage(f"HTML saved: {filename}", 5000)
            except OSError as exc:
                QMessageBox.warning(self, "Save page HTML", str(exc))
        view.page().toHtml(write_html)

    def copy_page_text(self):
        view = self.current_view()
        if not view:
            return
        def copy_text(value):
            QApplication.clipboard().setText(value or "")
            self.status.showMessage("Page text copied", 2500)
        view.page().runJavaScript("document.body ? document.body.innerText : ''", copy_text)

    def reopen_closed_tab(self):
        if not self.closed_tabs:
            self.status.showMessage("There are no recently closed tabs", 3000)
            return
        item = self.closed_tabs.pop()
        self.new_tab(item["url"])
        self.status.showMessage("Recently closed tab restored", 3000)

    def toggle_session_restore(self):
        enabled = not self.settings.get("restore_session", True)
        try:
            self.settings = save_setting("restore_session", enabled)
            self.status.showMessage("Session restore " + ("enabled" if enabled else "disabled"), 3500)
        except Exception as exc:
            self.status.showMessage(f"Could not update session settings: {exc}", 5000)

    def toggle_reader_mode(self):
        if 'reader' not in enabled_extensions():
            self.status.showMessage('Reader Mode is disabled in Browser Ecosystem → Extension center', 4500)
            return
        view = self.current_view()
        if not view:
            return
        if view.property("reader_mode"):
            view.setProperty("reader_mode", False)
            view.reload()
            self.status.showMessage("Reader mode disabled", 3000)
            return
        script = """
        (() => {
          const style = document.createElement('style');
          style.id = 'gdb-reader-style';
          style.textContent = 'html,body{background:#f4f0e7!important;color:#252525!important;font-family:Georgia,serif!important}body{max-width:820px!important;margin:40px auto!important;padding:32px!important;line-height:1.85!important;font-size:19px!important;box-shadow:0 8px 45px #0002!important}img,video,figure{max-width:100%!important;height:auto!important}nav,aside,footer,[role="navigation"],[role="complementary"]{display:none!important}a{color:#76551b!important}h1,h2,h3{line-height:1.25!important}';
          document.getElementById('gdb-reader-style')?.remove();
          document.head.appendChild(style);
        })();
        """
        view.page().runJavaScript(script)
        view.setProperty("reader_mode", True)
        self.status.showMessage("Reader mode enabled · reload to restore original layout", 4500)

    def translate_page(self):
        if 'translator' not in enabled_extensions():
            self.status.showMessage('Quick Translate is disabled in Browser Ecosystem → Extension center', 4500)
            return
        view = self.current_view()
        if not view:
            return
        url = view.url().toString()
        if not url.startswith(("https://", "http://")):
            self.status.showMessage("Open a website first", 3000)
            return
        from urllib.parse import quote
        self.navigate_to("https://translate.google.com/translate?sl=auto&tl=es&u=" + quote(url, safe=""))
        
    def save_screenshot(self):
        if 'capture' not in enabled_extensions():
            self.status.showMessage('Page Capture is disabled in Browser Ecosystem → Extension center', 4500)
            return
        view = self.current_view()
        if not view:
            return
        default = Path.home() / "Downloads" / "gold-diamond-page.png"
        filename, _ = QFileDialog.getSaveFileName(
            self, "Capture page", str(default), "PNG image (*.png);;JPEG image (*.jpg *.jpeg)"
        )
        if filename:
            if view.grab().save(filename):
                self.status.showMessage(f"Screenshot saved: {filename}", 5000)
            else:
                self.status.showMessage("Screenshot could not be saved", 4000)

    def change_search(self, engine: str):
        try:
            self.settings = save_setting("search_engine", engine)
            self.status.showMessage("Search engine preference saved", 4000)
        except Exception as exc:
            self.status.showMessage(f"Could not save search preference: {exc}", 5000)

    def set_startup_page(self):
        view = self.current_view()
        if view and view.url().scheme() in ("http", "https"):
            try:
                self.settings = save_setting("startup_page", view.url().toString())
                self.status.showMessage("Startup page saved", 4000)
            except Exception as exc:
                self.status.showMessage(f"Could not save startup page: {exc}", 5000)

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
            "<h2 style='color:#e5b85c'>◆ Gold &amp; Diamond Browser</h2>"
            "<p>Created by <b>AtDev Dev</b>.</p>"
            "<p>A modern browsing experience powered by Chromium and Memingo.</p>"
            "<p><b>Memingo-First.</b> Built to explore, learn and create.</p>"
            "<p>Distributed under the Apache License 2.0.</p>",
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
        if index < 0 or index >= self.tabs.count():
            return
        view = self.tabs.widget(index)
        if isinstance(view, QWebEngineView):
            url = view.url().toString()
            if not view.property("private_mode") and url.startswith(("https://", "http://")) and "gold-diamond.local" not in url:
                self.closed_tabs.append({"url": url, "title": view.title() or url})
                self.closed_tabs = self.closed_tabs[-10:]
        self.tabs.removeTab(index)
        if view:
            view.deleteLater()
        if self.tabs.count() == 0:
            self.new_tab()

    def closeEvent(self, event):
        self.persist_session()
        event.accept()
