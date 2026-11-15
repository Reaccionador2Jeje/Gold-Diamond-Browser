# Gold & Diamond Browser

**Gold & Diamond Browser** is a cross-platform desktop browser built with Memingo and Qt WebEngine (Chromium).

## Version 0.5.0 — Browser Ecosystem

- Real websites rendered with Qt WebEngine.
- Browser configuration and address/search resolution are authored in Memingo.
- Back, forward, reload and home controls.
- Multiple tabs, close/reorder tabs and keyboard shortcuts.
- A redesigned graphite-and-gold interface with a branded start dashboard and quick-launch tiles.
- Dedicated favorites toolbar and slide-out library sidebar.
- Isolated private tabs that do not write visits to the browser's local history.
- In-page text search, adjustable zoom and PDF export.
- Download tracking for the current session and quick access to the Downloads folder.
- Search engine selection: Google, DuckDuckGo or Bing.
- Four switchable interface themes: Graphite Gold, Midnight Blue, Pearl Light and Emerald Forest.
- A modular UI package separates visual themes and the new-tab dashboard from the browser controller.
- A redesigned new-tab experience with a live clock, date, search field, categorized shortcuts and a saved-bookmarks strip.
- Tab context menu with duplicate, pin, close-other-tabs and reopen-closed-tab actions.
- Reader mode, page translation, page screenshots and faster address-bar focus shortcuts.
- Browser dashboard search follows the selected search engine.
- Gold & Diamond AI chat dialog with an OpenAI-compatible API endpoint and model selector.
- Dedicated settings window with General, Appearance, AI assistant, Credits and License sections.
- gold-diamond.local is the default branded home page and new-tab address.
- AtDev Dev credits and Apache License 2.0 attribution in the application.
- A custom gold-and-cyan diamond app icon is generated as PNG, Windows ICO and macOS ICNS during packaging; Linux desktop launchers include the icon.
- Session restore: reopen regular tabs after restarting; private tabs are excluded.
- Theme preferences and saved sessions are persisted by Memingo.
- Memingo-managed bookmarks and browsing history, with add/remove and clear-history actions.
- Dark graphite UI with gold and diamond accents.
- Browser profiles with separate persistent Chromium storage; new tabs use the active profile while existing tabs remain in their original profile.\n- Built-in Extension Center for Reader Mode, Quick Translate and Page Capture; these are native browser tools, not Chrome Web Store extensions.\n- Privacy Center to clear the active profile cache, cookies and locally recorded browsing history. This does not provide anonymity or erase website/network records.\n- Automated native installers for Windows, Linux and macOS are built by GitHub Actions after all platform builds succeed.

## Architecture — Memingo-First

Memingo is the primary application and policy language. New browser behavior should be implemented in Memingo before considering a native-language implementation.

- `main.mgo` defines application identity, theme and window configuration.
- `ecosystem/navigation.mgo` owns address interpretation and search routing.
- `ecosystem/settings.mgo` owns default settings and persistent settings updates.
- `ecosystem/bookmarks.mgo` owns bookmark storage and updates.
- `ecosystem/history.mgo` owns visit recording and history storage.
- `browser/memingo_bridge.py` is a narrow execution and serialization adapter.
- `browser/window.py` is the Qt browser controller and Chromium WebEngine integration.
- `browser/ui/theme.py` contains reusable visual themes.
- `browser/ui/dashboard.py` renders the branded new-tab dashboard.
- `browser/ui/settings_dialog.py` provides the native settings and credits interface.
- `browser/ai_assistant.py` provides the optional OpenAI-compatible chat window.
- `assets/gold-diamond-icon.svg` is the scalable brand icon; packaging generates native icon formats.
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


## Gold & Diamond AI setup

Gold & Diamond AI supports chat-completions-compatible API providers. Configure the provider base URL and model in Tools → Browser settings → AI assistant. The API key is intentionally not stored in browser settings; set it in the environment before launching the browser:

PowerShell:

    $env:GDB_AI_API_KEY = "your-provider-api-key"
    python run.py

Linux / macOS:

    export GDB_AI_API_KEY="your-provider-api-key"
    python run.py

Remote API providers must use HTTPS. Localhost HTTP endpoints are allowed for local AI servers. Provider usage may incur charges; check the provider's pricing and use an account only with the account owner's permission.

## Credits and license

Gold & Diamond Browser is created by **AtDev Dev** and distributed under the **Apache License 2.0** (see LICENSE). The browser uses Memingo and Qt WebEngine / Chromium; their respective projects and third-party components retain their own licenses and trademarks.

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
| Ctrl+Shift+N | Open private tab |
| Ctrl+Shift+T | Reopen closed tab |
| Ctrl+Shift+E | Toggle reader mode |
| Ctrl+L | Focus address bar |
| Ctrl+J | Open downloads |
| Ctrl+Shift+L | Toggle library sidebar |
| Ctrl+F | Find text on page |
| Ctrl++ / Ctrl+- | Zoom in / out |
| Ctrl+0 | Reset zoom |
| F11 | Fullscreen |
| Ctrl+Q | Quit |

## Roadmap

- 0.2.0 — Premium interface, dashboard, private tabs, downloads, PDF export and expanded Memingo-first features.
- 0.3.0 — theme system, session restore and Memingo-managed browser preferences.
- 0.4 development — modular UI, dashboard refresh, tab management and page tools.
- 0.5 development — AI assistant, full settings, AtDev Dev credits, Apache license attribution, branded home page and desktop icon.
- Future — extension framework, profiles, sync and advanced privacy controls.
- 1.0.0 — signed installers, update mechanism and broader platform validation.
