"""Application entry point for Gold & Diamond Browser."""
from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication, QMessageBox

from browser.memingo_bridge import load_config
from browser.window import GoldDiamondWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Gold & Diamond Browser")
    app.setOrganizationName("AtDev")
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
