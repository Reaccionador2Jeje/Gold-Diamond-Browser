"""Thin native adapter for executing Memingo browser modules."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from memingo.interpreter import execute

ROOT = Path(__file__).resolve().parents[1]
ECOSYSTEM = ROOT / "ecosystem"


def _user_data_directory() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    directory = base / "Gold-Diamond-Browser"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


DATA_DIR = _user_data_directory()


def run_memingo(
    path: Path,
    *,
    extra_env: dict[str, str] | None = None,
    project_directory: Path = ROOT,
) -> list[str]:
    previous: dict[str, str | None] = {}
    try:
        for key, value in (extra_env or {}).items():
            previous[key] = os.environ.get(key)
            os.environ[key] = value
        source = path.read_text(encoding="utf-8")
        return list(execute(source, project_directory=project_directory))
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _json_result(module: str, *, extra_env: dict[str, str] | None = None) -> dict[str, Any]:
    output = run_memingo(ECOSYSTEM / module, extra_env=extra_env)
    if not output:
        raise RuntimeError(f"Memingo module {module} returned no result")
    result = json.loads(output[-1])
    if not isinstance(result, dict):
        raise RuntimeError(f"Memingo module {module} must return a JSON object")
    return result


def load_config() -> dict[str, Any]:
    output = run_memingo(ROOT / "main.mgo")
    if not output:
        raise RuntimeError("main.mgo did not return browser configuration")
    config = json.loads(output[-1])
    if not isinstance(config, dict):
        raise RuntimeError("Memingo browser configuration must be an object")
    return config


def load_settings() -> dict[str, Any]:
    output = run_memingo(
        ECOSYSTEM / "settings.mgo",
        extra_env={"GDB_REQUEST": json.dumps({"action": "get"})},
        project_directory=DATA_DIR,
    )
    if not output:
        raise RuntimeError("Memingo settings module returned no result")
    return json.loads(output[-1])


def save_setting(key: str, value: Any) -> dict[str, Any]:
    output = run_memingo(
        ECOSYSTEM / "settings.mgo",
        extra_env={"GDB_REQUEST": json.dumps({"action": "set", "key": key, "value": value})},
        project_directory=DATA_DIR,
    )
    if not output:
        raise RuntimeError("Memingo settings module returned no result")
    return json.loads(output[-1])


def resolve_url(value: str, search_engine: str | None = None) -> str:
    environment = {"GDB_INPUT": value}
    if search_engine:
        environment["GDB_SEARCH_ENGINE"] = search_engine
    result = _json_result("navigation.mgo", extra_env=environment)
    url = result.get("url")
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        raise RuntimeError("Memingo returned an invalid navigation URL")
    return url
