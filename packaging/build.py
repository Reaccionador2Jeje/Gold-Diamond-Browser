"""Build the frozen desktop application and its platform icon assets."""
from __future__ import annotations

import os
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"


def create_icon_files() -> None:
    """Rasterize the vector logo and create a multi-resolution Windows ICO."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    source = ASSETS / "gold-diamond-icon.svg"
    renderer = QSvgRenderer(str(source))
    if not renderer.isValid():
        raise RuntimeError("Gold & Diamond SVG icon could not be loaded")

    preview = QImage(512, 512, QImage.Format.Format_ARGB32)
    preview.fill(Qt.GlobalColor.transparent)
    painter = QPainter(preview)
    renderer.render(painter)
    painter.end()
    if not preview.save(str(ASSETS / "gold-diamond-icon.png"), "PNG"):
        raise RuntimeError("Could not write the application PNG icon")

    sizes = (16, 24, 32, 48, 64, 128, 256)
    images = []
    for size in sizes:
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        pixels = bytearray()
        for y in range(size - 1, -1, -1):
            for x in range(size):
                color = image.pixelColor(x, y)
                pixels.extend((color.blue(), color.green(), color.red(), color.alpha()))
        mask_row = ((size + 31) // 32) * 4
        mask = bytes(mask_row * size)
        header = struct.pack(
            "<IIIHHIIIIII", 40, size, size * 2, 1, 32, 0,
            len(pixels), 0, 0, 0, 0,
        )
        images.append(header + pixels + mask)

    directory_size = 6 + 16 * len(images)
    offset = directory_size
    directory = bytearray(struct.pack("<HHH", 0, 1, len(images)))
    for size, data in zip(sizes, images):
        directory.extend(struct.pack(
            "<BBBBHHII", 0 if size == 256 else size,
            0 if size == 256 else size, 0, 0, 1, 32, len(data), offset,
        ))
        offset += len(data)
    (ASSETS / "gold-diamond-icon.ico").write_bytes(directory + b"".join(images))


def main() -> int:
    create_icon_files()
    separator = os.pathsep
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--windowed", "--onedir",
        "--name", "GoldDiamondBrowser",
        "--icon", str(ASSETS / "gold-diamond-icon.ico"),
        "--collect-all", "PySide6",
        "--collect-all", "shiboken6",
        "--collect-all", "memingo",
        "--add-data", f"main.mgo{separator}.",
        "--add-data", f"ecosystem{separator}ecosystem",
        "--add-data", f"assets{separator}assets",
        "run.py",
    ]
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
