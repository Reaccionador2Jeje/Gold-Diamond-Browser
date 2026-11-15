# Gold & Diamond Browser

**Gold & Diamond Browser** is a cross-platform desktop browser built with Memingo and Qt WebEngine (Chromium).

## Version 0.1.0

- Real websites rendered with Qt WebEngine.
- Browser configuration and address/search resolution are authored in Memingo.
- Back, forward, reload and home controls.
- Multiple tabs, close/reorder tabs and keyboard shortcuts.
- Dark graphite UI with gold and diamond accents.

## Architecture

Memingo is the browser's application brain:
- `main.mgo` defines application identity, theme and window configuration.
- `src/navigation.mgo` resolves typed addresses and search queries.
- `browser/memingo_bridge.py` is the narrow adapter that executes Memingo programs.
- `browser/window.py` provides the Qt WebEngine interface.
- `run.py` starts the desktop application.

## Requirements

- Python 3.10+
- Memingo 0.2+
- PySide6 6.7+ (includes Qt WebEngine components)

## Setup

Clone both repositories side by side:

```text
workspace/
├── Memingo/
└── Gold-Diamond-Browser/
```

Install Memingo from its local checkout:

```bash
cd Memingo
python -m pip install -e .
cd ../Gold-Diamond-Browser
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

Install browser dependencies and launch:

```bash
python -m pip install -r requirements.txt
python run.py
```

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+T | New tab |
| Ctrl+W | Close tab |
| Ctrl+R | Reload |
| Alt+Left | Back |
| Alt+Right | Forward |
| Alt+Home | Home |

On macOS, Qt maps the standard shortcuts according to the platform keyboard conventions.

## Platform support

The codebase targets Windows, Linux and macOS. Install and test dependencies on each target operating system; native packaging and signing are planned for a later milestone.

## Roadmap

- 0.2.0 — bookmarks, browsing history and persistent settings.
- 0.3.0 — downloads manager and privacy controls.
- 1.0.0 — platform-specific installers and release automation.
