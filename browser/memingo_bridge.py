"""Small host bridge: Memingo decides configuration and URL resolution."""
from __future__ import annotations

import json
import os
from pathlib import Path

from memingo.interpreter import execute

ROOT = Path(__file__).resolve().parents[1]


def run_memingo(path: Path, *, extra_env: dict[str, str] | None = None) -> list[str]:
    previous: dict[str, str | None] = {}
    try:
        for key, value in (extra_env or {}).items():
            previous[key] = os.environ.get(key)
            os.environ[key] = value
        source = path.read_text(encoding="utf-8")
        return list(execute(source, project_directory=ROOT))
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def load_config() -> dict:
    output = run_memingo(ROOT / "main.mgo")
    if not output:
        raise RuntimeError("main.mgo did not return browser configuration")
    config = json.loads(output[-1])
    if not isinstance(config, dict):
        raise RuntimeError("Memingo browser configuration must be an object")
    return config


def resolve_url(value: str) -> str:
    output = run_memingo(ROOT / "src" / "navigation.mgo", extra_env={"GDB_INPUT": value})
    if not output:
        raise RuntimeError("Memingo navigation module returned no result")
    result = json.loads(output[-1])
    url = result.get("url")
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        raise RuntimeError("Memingo returned an invalid navigation URL")
    return url
