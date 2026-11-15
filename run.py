"""Application entry point for Gold & Diamond Browser."""
from __future__ import annotations

import sys
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from browser.memingo_bridge import load_config
from browser.window import GoldDiamondWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Gold & Diamond Browser")
    app.setOrganizationName("AtDev Dev")
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    icon_path = bundle_root / "assets" / "gold-diamond-icon.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    try:
        config = load_config()
        window = GoldDiamondWindow(config)
        window.show()
        return app.exec()
    except Exception as exc:
        QMessageBox.critical(None, "Gold & Diamond Browser", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
