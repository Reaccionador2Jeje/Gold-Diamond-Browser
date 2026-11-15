"""Persistent browser profiles and built-in extension preferences."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .memingo_bridge import DATA_DIR

STORE = DATA_DIR / "ecosystem.json"
DEFAULT_PROFILE = {"id": "default", "name": "Personal"}
BUILTIN_EXTENSIONS = [
    {"id": "reader", "name": "Reader Mode", "description": "Simplify articles for comfortable reading."},
    {"id": "translator", "name": "Quick Translate", "description": "Open the current page in Google Translate."},
    {"id": "capture", "name": "Page Capture", "description": "Save a screenshot of the visible page."},
]


def _load() -> dict[str, Any]:
    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            raw_profiles = data.get("profiles", [])
            profiles = []
            if isinstance(raw_profiles, list):
                for item in raw_profiles:
                    if not isinstance(item, dict):
                        continue
                    profile_id = item.get("id")
                    name = item.get("name")
                    if isinstance(profile_id, str) and profile_id and isinstance(name, str) and name:
                        profiles.append({"id": profile_id, "name": name})
            if not any(item["id"] == "default" for item in profiles):
                profiles.insert(0, DEFAULT_PROFILE.copy())
            data["profiles"] = profiles
            if data.get("active_profile") not in {item["id"] for item in profiles}:
                data["active_profile"] = "default"
            valid_extensions = {item["id"] for item in BUILTIN_EXTENSIONS}
            raw_extensions = data.get("extensions", [])
            data["extensions"] = (
                [item for item in raw_extensions if item in valid_extensions]
                if isinstance(raw_extensions, list) else
                [item["id"] for item in BUILTIN_EXTENSIONS]
            )
            return data
    except (OSError, ValueError, TypeError):
        pass
    return {"profiles": [DEFAULT_PROFILE.copy()], "active_profile": "default", "extensions": [x["id"] for x in BUILTIN_EXTENSIONS]}


def _save(data: dict[str, Any]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    temp = STORE.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(STORE)


def list_profiles() -> list[dict[str, str]]:
    data = _load()
    profiles = data.get("profiles", [])
    return profiles if isinstance(profiles, list) and profiles else [DEFAULT_PROFILE.copy()]


def active_profile_id() -> str:
    data = _load()
    active = data.get("active_profile", "default")
    return active if any(p.get("id") == active for p in list_profiles()) else "default"


def create_profile(name: str) -> dict[str, str]:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-_")[:32]
    if not clean:
        raise ValueError("Profile name must contain letters or numbers.")
    data = _load()
    profiles = data.setdefault("profiles", [DEFAULT_PROFILE.copy()])
    profile_id = clean.lower()
    base, suffix = profile_id, 2
    while any(p.get("id") == profile_id for p in profiles):
        profile_id = f"{base}-{suffix}"
        suffix += 1
    item = {"id": profile_id, "name": name.strip()[:48]}
    profiles.append(item)
    data["active_profile"] = profile_id
    _save(data)
    return item


def set_active_profile(profile_id: str) -> None:
    data = _load()
    if not any(p.get("id") == profile_id for p in data.get("profiles", [])):
        raise ValueError("Unknown browser profile.")
    data["active_profile"] = profile_id
    _save(data)


def enabled_extensions() -> set[str]:
    data = _load()
    values = data.get("extensions", [])
    valid = {x["id"] for x in BUILTIN_EXTENSIONS}
    return set(values) & valid if isinstance(values, list) else set()


def set_extension_enabled(extension_id: str, enabled: bool) -> None:
    valid = {x["id"] for x in BUILTIN_EXTENSIONS}
    if extension_id not in valid:
        raise ValueError("Unknown built-in extension.")
    data = _load()
    values = set(data.get("extensions", [])) & valid
    values.add(extension_id) if enabled else values.discard(extension_id)
    data["extensions"] = sorted(values)
    _save(data)
