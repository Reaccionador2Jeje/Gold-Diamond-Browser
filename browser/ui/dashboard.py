"""Branded new-tab dashboard for Gold & Diamond Browser."""
from __future__ import annotations

from html import escape


DEFAULT_TILES = [
    ("Search", "https://www.google.com", "⌕", "Search the web", "search"),
    ("YouTube", "https://www.youtube.com", "▶", "Videos and creators", "media"),
    ("Wikipedia", "https://www.wikipedia.org", "◇", "Explore knowledge", "learn"),
    ("GitHub", "https://github.com", "⌘", "Build something", "develop"),
    ("DuckDuckGo", "https://duckduckgo.com", "◈", "Search with privacy", "privacy"),
    ("Memingo", "https://github.com/Reaccionador2Jeje/Memingo", "M", "The language behind this browser", "code"),
    ("AtDev", "https://github.com/Reaccionador2Jeje", "A", "Projects and experiments", "studio"),
    ("MDN", "https://developer.mozilla.org", "文", "Web development reference", "learn"),
    ("Internet Archive", "https://archive.org", "▤", "Explore digital history", "discover"),
]


def build_dashboard(theme_name: str = "graphite", bookmarks: list[dict] | None = None, search_engine: str = "https://www.google.com/search?q=") -> str:
    palettes = {
        "graphite": ("#e5b85c", "#75d8e8", "#f4f7fb", "#9eafc4", "#080e17", "#263b50", "rgba(21,34,51,.78)", "rgba(156,184,212,.18)", "rgba(33,50,71,.88)", "rgba(15,26,41,.92)"),
        "midnight": ("#9fbcff", "#72e4ff", "#eef2ff", "#a1b1d8", "#080d20", "#243a70", "rgba(20,31,65,.82)", "rgba(130,164,255,.2)", "rgba(35,51,94,.9)", "rgba(13,23,49,.94)"),
        "pearl": ("#a36c12", "#087f9b", "#182438", "#53647b", "#e9eef6", "#ffffff", "rgba(255,255,255,.86)", "rgba(63,91,125,.22)", "rgba(255,255,255,.94)", "rgba(224,232,243,.96)"),
        "forest": ("#d8c27a", "#80d9b0", "#e9f6ed", "#9bb9a4", "#081713", "#244b3a", "rgba(19,48,37,.82)", "rgba(128,217,176,.2)", "rgba(30,69,52,.9)", "rgba(12,31,24,.94)"),
    }
    gold, cyan, ink, muted, background, glow, glass, line, tile_a, tile_b = palettes.get(theme_name, palettes["graphite"])
    search_engine = search_engine if search_engine.startswith(("https://", "http://")) else "https://www.google.com/search?q="
    tiles = "".join(
        f'<a class="tile" href="{url}"><span class="glyph">{glyph}</span>'
        f'<b>{escape(name)}</b><small>{escape(description)}</small></a>'
        for name, url, glyph, description, _category in DEFAULT_TILES
    )
    saved = bookmarks or []
    bookmark_cards = "".join(
        f'<a class="saved" href="{escape(item.get("url", ""), quote=True)}">'
        f'<span>★</span>{escape((item.get("title") or item.get("url", "Saved page"))[:32])}</a>'
        for item in saved[-6:]
        if item.get("url", "").startswith(("https://", "http://"))
    )
    if not bookmark_cards:
        bookmark_cards = '<div class="empty">Your saved pages will appear here.</div>'
    template = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<meta name="color-scheme" content="dark light"><title>Gold & Diamond — gold-diamond.local</title>
<style>
:root{--gold:__GOLD__;--cyan:__CYAN__;--ink:__INK__;--muted:__MUTED__;--bg:__BG__;--glow:__GLOW__;--glass:__GLASS__;--line:__LINE__;--tile-a:__TILE_A__;--tile-b:__TILE_B__}
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;color:var(--ink);font-family:Inter,'Segoe UI',Arial,sans-serif;background:radial-gradient(ellipse at 16% 8%,var(--glow) 0%,transparent 36%),radial-gradient(ellipse at 88% 78%,#173b42 0%,transparent 34%),linear-gradient(135deg,var(--bg),#101b2b 55%,var(--bg));}}
body:before{{content:"";position:fixed;inset:0;pointer-events:none;opacity:.16;background-image:radial-gradient(#b8d8e8 1px,transparent 1px);background-size:34px 34px;mask-image:linear-gradient(to bottom,black,transparent 85%)}}
main{{position:relative;width:min(1080px,92%);margin:auto;padding:54px 0 34px}}
.top{{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:48px}}
.brand{{display:flex;align-items:center;gap:13px}}.logo{{width:48px;height:48px;border-radius:16px;display:grid;place-items:center;font-size:25px;color:var(--gold);background:linear-gradient(145deg,#304158,#111c2c);border:1px solid #53677d;box-shadow:0 12px 35px #0006}}
.brand b{{letter-spacing:2px;font-size:14px}}.brand small{{display:block;color:var(--muted);letter-spacing:1px;margin-top:4px;font-size:10px}}
.clock{{text-align:right;color:var(--muted);font-size:12px}}#time{{font-size:24px;color:var(--ink);font-weight:650;letter-spacing:1px}}
.hero{{text-align:center;margin-bottom:34px}}.eyebrow{{font-size:11px;letter-spacing:4px;color:var(--cyan);text-transform:uppercase}}
h1{{font-size:clamp(34px,6vw,58px);letter-spacing:-2px;margin:13px 0 8px}}h1 em{{font-style:normal;color:var(--gold)}}.sub{{color:var(--muted);font-size:15px}}
.search{{display:flex;max-width:760px;margin:27px auto 0;padding:8px;background:var(--glass);border:1px solid #51647a;border-radius:18px;box-shadow:0 18px 55px #0005;backdrop-filter:blur(16px)}}
.search input{{flex:1;min-width:0;background:transparent;border:0;outline:0;color:white;padding:13px 15px;font-size:15px}}.search button{{border:0;border-radius:12px;padding:0 23px;color:#111827;background:linear-gradient(135deg,#f0d28a,#d5a64b);font-weight:750;cursor:pointer}}
.section-head{{display:flex;justify-content:space-between;align-items:end;margin:38px 0 14px}}h2{{font-size:13px;letter-spacing:2px;margin:0;color:#d8e3ef}}.hint{{font-size:11px;color:var(--muted)}}
.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px}}
.tile{{min-height:122px;text-decoration:none;color:var(--ink);background:linear-gradient(145deg,var(--tile-a),var(--tile-b));border:1px solid var(--line);border-radius:18px;padding:19px;transition:transform .18s,border-color .18s,box-shadow .18s;backdrop-filter:blur(10px)}.tile:hover{{border-color:var(--gold);transform:translateY(-4px);box-shadow:0 16px 30px #0004}}.glyph{{display:grid;place-items:center;width:34px;height:34px;border-radius:11px;background:#75d8e81a;color:var(--cyan);font-size:20px;margin-bottom:12px}}.tile b{{display:block;font-size:14px}}.tile small{{display:block;color:var(--muted);font-size:11px;margin-top:5px}}
.saved-grid{{display:flex;flex-wrap:wrap;gap:9px}}.saved{{text-decoration:none;color:#e8eff7;background:var(--glass);border:1px solid var(--line);padding:10px 13px;border-radius:12px;font-size:12px}}.saved span{{color:var(--gold);margin-right:8px}}.empty{{color:var(--muted);font-size:12px;padding:10px}}
.footer{{display:flex;justify-content:space-between;gap:15px;margin-top:50px;padding-top:18px;border-top:1px solid var(--line);color:#8193a8;font-size:10px;letter-spacing:1px}}.footer strong{{color:var(--cyan)}}
@media(max-width:680px){{main{{padding-top:28px}}.top{{margin-bottom:34px}}.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.tile{{padding:15px;min-height:110px}}.footer{{flex-direction:column}}}}
</style></head>
<body><main>
<header class="top"><div class="brand"><div class="logo">◆</div><div><b>GOLD & DIAMOND</b><small>YOUR PERSONAL WEB SPACE</small></div></div><div class="clock"><div id="time">--:--</div><div id="date">Ready to explore</div></div></header>
<section class="hero"><div class="eyebrow">A brighter way to explore</div><h1>Find your next <em>discovery.</em></h1><div class="sub">One browser. Your world of ideas, tools and knowledge.</div>
<form class="search" id="search" data-search-url="__SEARCH_ENGINE__"><input id="query" autocomplete="off" autofocus placeholder="Search the web or enter a website…" aria-label="Search the web"><button type="submit">Explore ↗</button></form></section>
<div class="section-head"><h2>QUICK LAUNCH</h2><span class="hint">Your shortcuts to the web</span></div><section class="grid">__TILES__</section>
<div class="section-head"><h2>YOUR SAVED SPACE</h2><span class="hint">Bookmarks from your library</span></div><section class="saved-grid">__BOOKMARKS__</section>
<footer class="footer"><span>POWERED BY <strong>MEMINGO</strong> · CHROMIUM ENGINE</span><span>MADE BY ATDEV DEV · GOLD & DIAMOND</span></footer>
</main><script>
const tick=()=>{{const d=new Date();document.getElementById('time').textContent=d.toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}});document.getElementById('date').textContent=d.toLocaleDateString([],{{weekday:'long',month:'long',day:'numeric'}})}};
tick();setInterval(tick,1000);
document.getElementById('search').addEventListener('submit',e=>{{e.preventDefault();const q=document.getElementById('query').value.trim();if(q)location.href=document.getElementById('search').dataset.searchUrl+encodeURIComponent(q)}});
</script></body></html>"""
    template = template.replace("{{", "{").replace("}}", "}")
    replacements = {
        "__GOLD__": gold, "__CYAN__": cyan, "__INK__": ink, "__MUTED__": muted,
        "__BG__": background, "__GLOW__": glow, "__GLASS__": glass, "__LINE__": line,
        "__TILE_A__": tile_a, "__TILE_B__": tile_b,
        "__SEARCH_ENGINE__": escape(search_engine, quote=True),
        "__TILES__": tiles, "__BOOKMARKS__": bookmark_cards,
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template
