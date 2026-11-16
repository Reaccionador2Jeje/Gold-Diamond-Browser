"""Consistent pure-black UI theme for Gold & Diamond Browser."""
from __future__ import annotations

PALETTES = {
    "graphite": {
        "bg": "#000000", "bar": "#050505", "field": "#080808",
        "panel": "#0b0b0b", "tab": "#101010", "hover": "#1b1b1b",
        "text": "#f5f5f5", "muted": "#a0a0a0", "border": "#303030",
        "gold": "#e5b85c", "blue": "#75d8e8",
    },
    "midnight": {
        "bg": "#000000", "bar": "#030407", "field": "#07090d",
        "panel": "#0a0c10", "tab": "#10141b", "hover": "#1b222d",
        "text": "#f0f3f8", "muted": "#9ba8ba", "border": "#303744",
        "gold": "#9fbcff", "blue": "#72e4ff",
    },
    "pearl": {
        "bg": "#000000", "bar": "#050505", "field": "#080808",
        "panel": "#0b0b0b", "tab": "#101010", "hover": "#1b1b1b",
        "text": "#f5f5f5", "muted": "#a0a0a0", "border": "#303030",
        "gold": "#d8b36a", "blue": "#75cfe0",
    },
    "forest": {
        "bg": "#000000", "bar": "#030806", "field": "#060a08",
        "panel": "#090e0b", "tab": "#101812", "hover": "#19251d",
        "text": "#eff7f0", "muted": "#9eb5a3", "border": "#2d4033",
        "gold": "#d8c27a", "blue": "#80d9b0",
    },
}


def build_stylesheet(theme_name: str = "graphite") -> str:
    p = PALETTES.get(theme_name, PALETTES["graphite"])
    return f"""
    QWidget {{ color: {p["text"]}; background-color: {p["bg"]}; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 10pt; }}
    QMainWindow, QDialog, QTabWidget::pane, QStackedWidget {{ background: #000000; border: 0; }}
    QToolBar, QMenuBar, QStatusBar {{ background: #050505; color: {p["text"]}; border: 0; spacing: 6px; padding: 6px; }}
    QToolButton, QPushButton {{ color: {p["text"]}; background: #101010; border: 1px solid {p["border"]}; border-radius: 9px; padding: 8px 12px; }}
    QToolButton:hover, QPushButton:hover {{ background: #1b1b1b; border-color: {p["gold"]}; }}
    QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser, QComboBox, QSpinBox, QDoubleSpinBox {{ background: #080808; color: {p["text"]}; border: 1px solid {p["border"]}; border-radius: 8px; padding: 8px; selection-background-color: {p["gold"]}; selection-color: #000000; }}
    QComboBox QAbstractItemView, QMenu {{ background: #080808; color: {p["text"]}; border: 1px solid {p["border"]}; selection-background-color: #202020; selection-color: {p["gold"]}; }}
    QMenuBar::item {{ background: transparent; padding: 6px 10px; }}
    QMenuBar::item:selected, QMenu::item:selected {{ background: #202020; color: {p["gold"]}; }}
    QTabBar::tab {{ background: #080808; color: {p["muted"]}; padding: 10px 16px; border: 1px solid #202020; }}
    QTabBar::tab:selected {{ color: {p["gold"]}; background: #151515; border-bottom: 2px solid {p["gold"]}; }}
    QTabBar::tab:hover {{ background: #1b1b1b; }}
    QDockWidget {{ color: {p["gold"]}; background: #080808; border: 1px solid {p["border"]}; }}
    QDockWidget::title {{ background: #050505; padding: 10px; }}
    QListWidget, QTreeWidget, QTableWidget {{ background: #070707; color: {p["text"]}; border: 1px solid #202020; outline: 0; padding: 5px; alternate-background-color: #101010; }}
    QListWidget::item, QTreeWidget::item {{ padding: 8px; }}
    QListWidget::item:selected, QTreeWidget::item:selected {{ background: #202020; color: {p["gold"]}; }}
    QCheckBox {{ color: {p["text"]}; spacing: 8px; background: transparent; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; }}
    QProgressBar {{ background: #151515; border: 0; border-radius: 3px; height: 4px; }}
    QProgressBar::chunk {{ background: {p["gold"]}; border-radius: 3px; }}
    QScrollBar:vertical {{ background: #050505; width: 10px; }}
    QScrollBar::handle:vertical {{ background: #333333; min-height: 24px; border-radius: 4px; }}
    QLabel {{ background: transparent; }}
    """
