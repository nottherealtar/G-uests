#!/usr/bin/env python3
"""
Fetches active Discord quests, matches them against Discord's detectable
application database, generates banner images, and writes Data-Feed/index.html.

Requires: DISCORD_TOKEN env var (your personal Discord user token).
"""

import io, json, os, re, sys
import requests
from pathlib import Path
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "").strip()
if not DISCORD_TOKEN:
    print("ERROR: DISCORD_TOKEN environment variable is not set.")
    sys.exit(1)

API_BASE  = "https://discord.com/api/v9"
CDN_BASE  = "https://cdn.discordapp.com"

ASSETS_DIR = Path("Data-Feed/Assets")
FEED_HTML  = Path("Data-Feed/index.html")
FEED_JSON  = Path("Data-Feed/quests.json")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

AUTH_HEADERS = {
    "Authorization": DISCORD_TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
}
PUBLIC_HEADERS = {k: v for k, v in AUTH_HEADERS.items() if k != "Authorization"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get(url, auth=True, **kwargs):
    h = AUTH_HEADERS if auth else PUBLIC_HEADERS
    r = requests.get(url, headers=h, timeout=20, **kwargs)
    r.raise_for_status()
    return r

def safe_name(text):
    """Strip characters that are invalid in Windows paths."""
    return re.sub(r'[<>:"/\\|?*]', '', text).strip()

def get_exe_stem(app: dict) -> str:
    """Return the best Windows executable stem (no path, no .exe)."""
    exes = [e for e in app.get("executables", [])
            if e.get("os") == "win32" and not e.get("is_launcher", False)]
    if not exes:
        exes = [e for e in app.get("executables", []) if e.get("os") == "win32"]
    if not exes:
        return safe_name(app.get("name", "game")).replace(" ", "")
    return Path(exes[0]["name"]).stem   # handles "bin/game.exe" → "game"

def build_href(game_name: str, exe_stem: str) -> str:
    """Construct the Windows path that Discord will see as the running game."""
    dir_name = safe_name(game_name)
    return rf"#Steam\steamapps\common\{dir_name}\Binaries\Win64\{exe_stem}"

def create_banner(icon_bytes: bytes, size=(440, 220)) -> bytes:
    """
    Generates a banner PNG: dark gradient background with the Discord
    app icon centred and slightly enlarged.
    """
    w, h = size
    # Dark background
    banner = Image.new("RGB", (w, h), (18, 18, 30))

    try:
        icon = Image.open(io.BytesIO(icon_bytes)).convert("RGBA")
        icon.thumbnail((int(h * 0.85), int(h * 0.85)), Image.LANCZOS)
        x = (w - icon.width) // 2
        y = (h - icon.height) // 2
        banner.paste(icon, (x, y), icon)
    except Exception:
        pass

    # Subtle vignette at edges
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    for i in range(30):
        alpha = int(120 * (i / 30))
        draw.rectangle([0, h - 30 + i, w, h - 30 + i + 1], fill=(0, 0, 0, alpha))
    banner.paste(Image.new("RGB", (w, h), (0, 0, 0)), (0, 0),
                 vignette.split()[3])

    buf = io.BytesIO()
    banner.save(buf, "PNG", optimize=True)
    return buf.getvalue()

# ---------------------------------------------------------------------------
# Step 1 – Fetch active quests (requires user auth)
# ---------------------------------------------------------------------------
print("Fetching active quests from Discord...")
try:
    resp = get(f"{API_BASE}/quests")
    quests_raw = resp.json()
except requests.HTTPError as e:
    print(f"ERROR: Could not fetch quests — {e}")
    print("Check that DISCORD_TOKEN is a valid user token (not a bot token).")
    sys.exit(1)

# API returns list or {"quests": [...]}
quests = quests_raw if isinstance(quests_raw, list) else quests_raw.get("quests", [])
print(f"  Found {len(quests)} active quest(s).")

if not quests:
    print("No active quests right now — feed unchanged.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Step 2 – Load all detectable applications (no auth needed, ~1 800 games)
# ---------------------------------------------------------------------------
print("Loading Discord detectable applications database...")
try:
    detectable = get(f"{API_BASE}/applications/detectable", auth=False).json()
    det_map = {app["id"]: app for app in detectable}
    print(f"  Loaded {len(det_map)} applications.")
except Exception as e:
    print(f"WARNING: Could not load detectable apps — {e}")
    det_map = {}

# ---------------------------------------------------------------------------
# Step 3 – Build game entries
# ---------------------------------------------------------------------------
game_entries = []
seen_ids = set()

for quest in quests:
    cfg = quest.get("config", {})

    # Application ID lives at config.application.id
    app_obj  = cfg.get("application", {})
    app_id   = app_obj.get("id") or cfg.get("application_id")
    app_name = app_obj.get("name", "")

    if not app_id or app_id in seen_ids:
        continue
    seen_ids.add(app_id)

    # Merge data from detectable map (richer than quest config)
    det = det_map.get(app_id, {})
    game_name = det.get("name") or app_name or f"Game {app_id}"
    icon_hash = det.get("icon_hash", "")
    exe_stem  = get_exe_stem(det) if det else safe_name(game_name).replace(" ", "")
    href      = build_href(game_name, exe_stem)

    # Download icon → generate banner
    banner_filename = f"{app_id}.png"
    banner_path = ASSETS_DIR / banner_filename

    if not banner_path.exists():
        icon_data = None
        if icon_hash:
            try:
                icon_data = get(
                    f"{CDN_BASE}/app-icons/{app_id}/{icon_hash}.png?size=512",
                    auth=False
                ).content
                print(f"  Downloaded icon for {game_name}")
            except Exception as e:
                print(f"  WARNING: icon download failed for {game_name} — {e}")

        banner_bytes = create_banner(icon_data or b"")
        banner_path.write_bytes(banner_bytes)
        print(f"  Generated banner → {banner_filename}")

    game_entries.append({
        "app_id":   app_id,
        "name":     game_name,
        "banner":   banner_filename,
        "href":     href,
        "exe":      exe_stem,
    })
    print(f"  + {game_name}  ({exe_stem}.exe)")

# ---------------------------------------------------------------------------
# Step 4 – Write Data-Feed/index.html
# ---------------------------------------------------------------------------
divs = []
for e in game_entries:
    divs.append(
        f'    <div data-name="{e["name"]}" style="padding-bottom:20px;padding-left:12px;">\n'
        f'        <img src="./Assets/{e["banner"]}" alt="{e["name"]}" style="display:block;">\n'
        f'        <a href="{e["href"]}">\n'
        f'            <img src="./Assets/button.png" alt="">\n'
        f'        </a>\n'
        f'    </div>'
    )

html = (
    '<!DOCTYPE html>\n'
    '<html lang="en">\n'
    '<head><meta charset="UTF-8"><title></title></head>\n'
    '<body style="background-color:#19191d;">\n\n'
    + "\n\n".join(divs) +
    '\n\n</body>\n</html>\n'
)
FEED_HTML.write_text(html, encoding="utf-8")
print(f"\nWrote {len(game_entries)} quest(s) to {FEED_HTML}")

# ---------------------------------------------------------------------------
# Step 5 – Write Data-Feed/quests.json (for future use / debugging)
# ---------------------------------------------------------------------------
FEED_JSON.write_text(json.dumps(game_entries, indent=2, ensure_ascii=False),
                     encoding="utf-8")
print(f"Wrote metadata to {FEED_JSON}")
