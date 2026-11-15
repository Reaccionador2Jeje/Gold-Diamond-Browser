"""Visual theme system for Gold & Diamond Browser."""
from __future__ import annotations


PALETTES = {
    "graphite": {
        "bg": "#0b0f17", "bar": "#111827", "field": "#0d1420",
        "panel": "#172235", "tab": "#202b3b", "hover": "#25364a",
        "text": "#edf2f8", "muted": "#91a0b4", "border": "#34445a",
        "gold": "#e5b85c", "blue": "#75d8e8",
    },
    "midnight": {
        "bg": "#080d20", "bar": "#111a36", "field": "#0c1530",
        "panel": "#17264a", "tab": "#202f57", "hover": "#2b4172",
        "text": "#eef2ff", "muted": "#a1b1d8", "border": "#354b7c",
        "gold": "#9fbcff", "blue": "#72e4ff",
    },
    "pearl": {
        "bg": "#edf1f7", "bar": "#dce4ef", "field": "#ffffff",
        "panel": "#e4eaf3", "tab": "#f8faff", "hover": "#d5e0ef",
        "text": "#182438", "muted": "#53647b", "border": "#b8c6d8",
        "gold": "#a36c12", "blue": "#087f9b",
    },
    "forest": {
        "bg": "#081713", "bar": "#10251e", "field": "#0b1e18",
        "panel": "#18352a", "tab": "#204536", "hover": "#2b5b45",
        "text": "#e9f6ed", "muted": "#9bb9a4", "border": "#365c49",
        "gold": "#d8c27a", "blue": "#80d9b0",
    },
}


def build_stylesheet(theme_name: str = "graphite") -> str:
    p = PALETTES.get(theme_name, PALETTES["graphite"])
    return f"""
    QWidget {{ color: {p["text"]}; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 10pt; }}
    QMainWindow, QTabWidget::pane {{ background: {p["bg"]}; border: 0; }}
    QToolBar {{ background: {p["bar"]}; border: 0; spacing: 6px; padding: 8px 12px; }}
    QToolButton {{ color: {p["text"]}; background: {p["panel"]}; border: 1px solid {p["border"]};
        border-radius: 10px; padding: 8px 11px; }}
    QToolButton:hover {{ background: {p["hover"]}; border-color: {p["gold"]}; }}
    QLineEdit {{ background: {p["field"]}; color: {p["text"]}; border: 1px solid {p["border"]};
        border-radius: 13px; padding: 11px 15px; selection-background-color: {p["blue"]}; }}
    QLineEdit:focus {{ border: 1px solid {p["gold"]}; }}
    QTabBar::tab {{ background: {p["bar"]}; color: {p["muted"]}; padding: 11px 18px;
        margin-right: 3px; border-top-left-radius: 10px; border-top-right-radius: 10px; }}
    QTabBar::tab:selected {{ color: {p["gold"]}; background: {p["tab"]}; border-bottom: 2px solid {p["gold"]}; }}
    QTabBar::tab:hover {{ background: {p["hover"]}; }}
    QStatusBar {{ background: {p["bar"]}; color: {p["muted"]}; border-top: 1px solid {p["border"]}; }}
    QDockWidget {{ color: {p["gold"]}; background: {p["panel"]}; border: 1px solid {p["border"]}; }}
    QDockWidget::title {{ background: {p["bar"]}; padding: 10px; }}
    QListWidget {{ background: {p["panel"]}; border: 0; outline: 0; padding: 6px; }}
    QListWidget::item {{ padding: 10px; border-radius: 7px; }}
    QListWidget::item:selected {{ background: {p["hover"]}; color: {p["gold"]}; }}
    QPushButton {{ background: {p["tab"]}; color: {p["text"]}; border: 1px solid {p["border"]};
        border-radius: 9px; padding: 8px 12px; }}
    QPushButton:hover {{ border-color: {p["gold"]}; }}
    QProgressBar {{ background: {p["panel"]}; border: 0; border-radius: 3px; height: 4px; }}
    QProgressBar::chunk {{ background: {p["gold"]}; border-radius: 3px; }}
    """
