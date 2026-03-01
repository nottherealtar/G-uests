#!/usr/bin/env python3
"""
Reads quest IDs from quests-config.json, fetches each quest's config from
Discord's API (/quests/{id}), enriches with detectable-app data, generates
banner images, and writes Data-Feed/index.html + Data-Feed/quests.json.

Requires: DISCORD_TOKEN env var (personal Discord user token, not a bot token).
Add active quest IDs to quests-config.json when new Discord quests launch.
"""

import base64, io, json, os, re, sys
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

API_BASE   = "https://discord.com/api/v9"
CDN_BASE   = "https://cdn.discordapp.com"
CONFIG_FILE = Path("quests-config.json")
ASSETS_DIR  = Path("Data-Feed/Assets")
FEED_HTML   = Path("Data-Feed/index.html")
FEED_JSON   = Path("Data-Feed/quests.json")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Discord user-facing endpoints need these headers to return real data.
_super_props = base64.b64encode(json.dumps({
    "os": "Windows",
    "browser": "Discord Client",
    "release_channel": "stable",
    "client_version": "1.0.9035",
    "os_version": "10.0.19045",
    "os_arch": "x64",
    "app_arch": "x64",
    "system_locale": "en-US",
    "browser_user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) discord/1.0.9035 Chrome/128.0.6613.186 "
        "Electron/32.2.7 Safari/537.36"
    ),
    "browser_version": "32.2.7",
    "client_build_number": 349345,
    "native_build_number": 50714,
    "client_event_source": None,
}, separators=(',', ':'), ensure_ascii=False).encode()).decode()

HEADERS = {
    "Authorization": DISCORD_TOKEN,
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) discord/1.0.9035 Chrome/128.0.6613.186 "
        "Electron/32.2.7 Safari/537.36"
    ),
    "X-Super-Properties": _super_props,
    "X-Discord-Locale": "en-US",
    "Content-Type": "application/json",
    "Accept": "*/*",
}
PUBLIC_HEADERS = {k: v for k, v in HEADERS.items() if k != "Authorization"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get(url, auth=True, **kwargs):
    h = HEADERS if auth else PUBLIC_HEADERS
    r = requests.get(url, headers=h, timeout=20, **kwargs)
    r.raise_for_status()
    return r

def safe_name(text):
    return re.sub(r'[<>:"/\\|?*]', '', text).strip()

def get_exe_stem(app: dict) -> str:
    exes = [e for e in app.get("executables", [])
            if e.get("os") == "win32" and not e.get("is_launcher", False)]
    if not exes:
        exes = [e for e in app.get("executables", []) if e.get("os") == "win32"]
    if not exes:
        return safe_name(app.get("name", "game")).replace(" ", "")
    return Path(exes[0]["name"]).stem

def build_href(game_name: str, exe_stem: str) -> str:
    return rf"#Steam\steamapps\common\{safe_name(game_name)}\Binaries\Win64\{exe_stem}"

def create_banner(icon_bytes: bytes, size=(440, 220)) -> bytes:
    w, h = size
    banner = Image.new("RGB", (w, h), (18, 18, 30))
    if icon_bytes:
        try:
            icon = Image.open(io.BytesIO(icon_bytes)).convert("RGBA")
            icon.thumbnail((int(h * 0.85), int(h * 0.85)), Image.LANCZOS)
            banner.paste(icon, ((w - icon.width) // 2, (h - icon.height) // 2), icon)
        except Exception:
            pass
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    for i in range(30):
        draw.rectangle([0, h - 30 + i, w, h - 30 + i + 1],
                       fill=(0, 0, 0, int(120 * i / 30)))
    banner.paste(Image.new("RGB", (w, h), (0, 0, 0)), (0, 0), vignette.split()[3])
    buf = io.BytesIO()
    banner.save(buf, "PNG", optimize=True)
    return buf.getvalue()

# ---------------------------------------------------------------------------
# Step 1 – Read quest IDs from config
# ---------------------------------------------------------------------------
if not CONFIG_FILE.exists():
    print(f"ERROR: {CONFIG_FILE} not found.")
    sys.exit(1)

config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
quest_ids = config.get("quest_ids", [])

if not quest_ids:
    print("No quest IDs in quests-config.json — nothing to do.")
    print("Add active quest IDs to quests-config.json to populate the feed.")
    sys.exit(0)

print(f"Processing {len(quest_ids)} quest ID(s): {quest_ids}")

# ---------------------------------------------------------------------------
# Step 2 – Load detectable applications (public, no auth)
# ---------------------------------------------------------------------------
print("Loading Discord detectable applications...")
try:
    det_map = {a["id"]: a for a in get(f"{API_BASE}/applications/detectable", auth=False).json()}
    print(f"  Loaded {len(det_map)} applications.")
except Exception as e:
    print(f"WARNING: Could not load detectable apps — {e}")
    det_map = {}

# ---------------------------------------------------------------------------
# Step 3 – Fetch each quest config from Discord
# ---------------------------------------------------------------------------
game_entries = []

for quest_id in quest_ids:
    print(f"\nFetching quest {quest_id}...")
    try:
        data = get(f"{API_BASE}/quests/{quest_id}").json()
    except requests.HTTPError as e:
        body = ""
        try: body = e.response.text[:300]
        except Exception: pass
        print(f"  WARNING: Could not fetch quest {quest_id} — {e} {body}")
        print("  Skipping (quest may have expired or ID is wrong).")
        continue

    cfg      = data.get("config", data)   # some endpoints wrap in "config"
    app_obj  = cfg.get("application", {})
    app_id   = app_obj.get("id", "")
    app_name = (
        cfg.get("messages", {}).get("game_title")
        or app_obj.get("name")
        or f"Quest {quest_id}"
    )

    det       = det_map.get(app_id, {})
    game_name = det.get("name") or app_name
    icon_hash = det.get("icon_hash", "")
    exe_stem  = get_exe_stem(det) if det else safe_name(game_name).replace(" ", "")
    href      = build_href(game_name, exe_stem)

    # Download icon → generate banner
    banner_filename = f"{app_id or quest_id}.png"
    banner_path     = ASSETS_DIR / banner_filename

    icon_data = None
    if not banner_path.exists() and icon_hash:
        try:
            icon_data = get(
                f"{CDN_BASE}/app-icons/{app_id}/{icon_hash}.png?size=512",
                auth=False
            ).content
            print(f"  Downloaded icon for {game_name}")
        except Exception as e:
            print(f"  WARNING: icon download failed — {e}")

    if not banner_path.exists():
        banner_path.write_bytes(create_banner(icon_data or b""))
        print(f"  Generated banner → {banner_filename}")

    entry = {
        "quest_id": quest_id,
        "app_id":   app_id,
        "name":     game_name,
        "banner":   banner_filename,
        "href":     href,
        "exe":      exe_stem,
    }
    game_entries.append(entry)
    print(f"  + {game_name}  →  {exe_stem}.exe")

if not game_entries:
    print("\nNo valid quests resolved — feed unchanged.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Step 4 – Write Data-Feed/index.html
# ---------------------------------------------------------------------------
divs = "\n\n".join(
    f'    <div data-name="{e["name"]}" style="padding-bottom:20px;padding-left:12px;">\n'
    f'        <img src="./Assets/{e["banner"]}" alt="{e["name"]}" style="display:block;">\n'
    f'        <a href="{e["href"]}">\n'
    f'            <img src="./Assets/button.png" alt="">\n'
    f'        </a>\n'
    f'    </div>'
    for e in game_entries
)

FEED_HTML.write_text(
    '<!DOCTYPE html>\n<html lang="en">\n'
    '<head><meta charset="UTF-8"><title></title></head>\n'
    '<body style="background-color:#19191d;">\n\n'
    + divs +
    '\n\n</body>\n</html>\n',
    encoding="utf-8"
)
print(f"\nWrote {len(game_entries)} quest(s) to {FEED_HTML}")

# ---------------------------------------------------------------------------
# Step 5 – Write Data-Feed/quests.json
# ---------------------------------------------------------------------------
FEED_JSON.write_text(json.dumps(game_entries, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote metadata to {FEED_JSON}")
