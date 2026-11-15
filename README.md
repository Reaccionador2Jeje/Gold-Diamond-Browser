# Gold & Diamond Browser

**Gold & Diamond Browser** is a cross-platform desktop browser built with Memingo and Qt WebEngine (Chromium).

## Version 0.1.0

- Real websites rendered with Qt WebEngine.
- Browser configuration and address/search resolution are authored in Memingo.
- Back, forward, reload and home controls.
- Multiple tabs, close/reorder tabs and keyboard shortcuts.
- Memingo-managed bookmarks and browsing history, with toolbar menus.
- Dark graphite UI with gold and diamond accents.
- Automated native installers for Windows, Linux and macOS are built by GitHub Actions.

## Architecture — Memingo-First

Memingo is the primary application and policy language. New browser behavior should be implemented in Memingo before considering a native-language implementation.

- `main.mgo` defines application identity, theme and window configuration.
- `ecosystem/navigation.mgo` owns address interpretation and search routing.
- `ecosystem/settings.mgo` owns default settings and persistent settings updates.
- `ecosystem/bookmarks.mgo` owns bookmark storage and updates.
- `ecosystem/history.mgo` owns visit recording and history storage.
- `browser/memingo_bridge.py` is a narrow execution and serialization adapter.
- `browser/window.py` is the native Qt host: widgets, Chromium WebEngine events and platform integration.
- `run.py` starts the desktop application.

Python remains only where a native host is required: Qt WebEngine, desktop widgets, process startup, user data directory discovery and the Memingo runtime adapter. Browser policies and user-facing application rules belong in Memingo. The long-term goal is to reduce the host layer as Memingo gains suitable native bindings.

Persistent settings are stored in the operating system's user data directory, not inside the installed application folder.

## Requirements for running from source

- Python 3.10+
- Memingo 0.2+
- PySide6 6.7+ (includes Qt WebEngine components)

## Setup from source

Clone both repositories side by side:

\`\`\`text
workspace/
├── Memingo/
└── Gold-Diamond-Browser/
\`\`\`

Install Memingo from its local checkout:

\`\`\`bash
cd Memingo
python -m pip install -e .
cd ../Gold-Diamond-Browser
python -m venv .venv
\`\`\`

Activate the environment:

\`\`\`powershell
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
\`\`\`

\`\`\`bash
# Linux / macOS
source .venv/bin/activate
\`\`\`

Install browser dependencies and launch:

\`\`\`bash
python -m pip install -r requirements.txt
python run.py
\`\`\`

## Installers

The release workflow builds these packages on native GitHub-hosted runners:

| Platform | Package | Installation |
|---|---|---|
| Windows x64 | \`.exe\` | Graphical Inno Setup wizard, Start Menu shortcut and optional desktop shortcut |
| Debian/Ubuntu x64 | \`.deb\` | Install with the system package installer or \`sudo apt install ./gold-diamond-browser_0.1.0_amd64.deb\` |
| Fedora/RHEL x64 | \`.rpm\` | Install with the system package installer or \`sudo dnf install ./gold-diamond-browser-0.1.0-1.x86_64.rpm\` |
| macOS | \`.dmg\` | Open the disk image and drag the app to Applications |

To publish version 0.1.0, create and push the tag:

\`\`\`bash
git tag v0.1.0
git push origin v0.1.0
\`\`\`

GitHub Actions then builds all platform installers and attaches them to a GitHub Release named **Gold & Diamond Browser v0.1.0**. The release is published only after all three platform builds succeed.

Packages are not code-signed or notarized yet. Windows SmartScreen and macOS Gatekeeper may show warnings until signing identities are configured.

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+T | New tab |
| Ctrl+W | Close tab |
| Ctrl+R | Reload |
| Alt+Left | Back |
| Alt+Right | Forward |
| Alt+Home | Home |
| Ctrl+D | Add bookmark |
| Ctrl+Shift+B | Show bookmarks |
| Ctrl+H | Show browsing history |
| Ctrl+Shift+H | Set current page as startup page |

## Roadmap

- 0.2.0 — Memingo-first architecture, persistent settings, bookmarks and browsing history.
- 0.3.0 — downloads manager and privacy controls.
- 1.0.0 — signed installers, update mechanism and broader platform validation.
