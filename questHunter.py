import os, io, sys, subprocess, requests, traceback, webbrowser, shutil, base64
from tkinter import Tk, Label, Frame, Canvas, PhotoImage
from PIL import Image, ImageTk
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding="utf-8")
icon_b64 = """
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
"""
# ── Remote feed ── update YOUR_GITHUB_USERNAME after pushing to G-uests ──
GITHUB_USER  = "nottherealtar"
REPO_NAME    = "G-uests"
RAW_BASE     = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/Data-Feed"
REMOTE_HTML  = f"{RAW_BASE}/index.html"
# ─────────────────────────────────────────────────────────────────────────
LOCAL_HTML   = os.path.join(os.getcwd(), "Data-Feed", "index.html")
LOCAL_ASSETS = os.path.join(os.getcwd(), "Data-Feed", "Assets")
BG_COLOR = "#19191d"
APP_SIZE = "430x900"
icon_bytes = base64.b64decode(icon_b64)
ROOT = os.path.join(os.getcwd(), "Binaries", "Win64")
print(f"Detected ROOT folder: {ROOT}")
root = Tk()
root.title("Guests - Game Quest Player")
root.geometry(APP_SIZE)
root.configure(bg=BG_COLOR)
root.resizable(False, False)
icon_img = ImageTk.PhotoImage(Image.open(io.BytesIO(icon_bytes)))
root.iconphoto(True, icon_img)
canvas = Canvas(root, bg=BG_COLOR, highlightthickness=0, borderwidth=0)
canvas.pack(fill="both", expand=True)
content_frame = Frame(canvas, bg=BG_COLOR)
canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
def on_mouse_wheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
def update_scroll_region(event=None):
    canvas.configure(scrollregion=canvas.bbox("all"))
root.bind_all("<MouseWheel>", on_mouse_wheel)
content_frame.bind("<Configure>", update_scroll_region)
Label(content_frame,
      text="🎮 Guests - Game Quest Player for Discord  |  Made by Tar",
      bg=BG_COLOR, fg="white", wraplength=380+50, justify="left", anchor="w").pack(pady=(10,5))

mfs_path = os.path.join(ROOT, "main.mfs")
if not os.path.exists(mfs_path):
    gif_py = os.path.join(os.getcwd(), "gif.py")
    if os.path.exists(gif_py):
        build_lbl = Label(content_frame, text="⚙️ First-time setup: building launcher stub, please wait...",
                          bg=BG_COLOR, fg="yellow", wraplength=380+50, justify="left", anchor="w")
        build_lbl.pack(pady=(5,5), padx=12)
        root.update()
        try:
            result = subprocess.run(
                [sys.executable, "-m", "PyInstaller", "--onefile", "--noconsole", "--name", "gif", gif_py],
                capture_output=True, text=True, timeout=300
            )
            built_exe = os.path.join(os.getcwd(), "dist", "gif.exe")
            if result.returncode == 0 and os.path.exists(built_exe):
                os.makedirs(ROOT, exist_ok=True)
                shutil.copyfile(built_exe, mfs_path)
                size_mb = os.path.getsize(mfs_path) // (1024 * 1024)
                build_lbl.config(text=f"✅ Setup complete! Launcher stub built ({size_mb} MB)", fg="lime")
            else:
                build_lbl.config(text="❌ Build failed. Run: pip install pyinstaller", fg="red")
        except FileNotFoundError:
            build_lbl.config(text="❌ PyInstaller not found. Run: pip install pyinstaller", fg="red")
        except subprocess.TimeoutExpired:
            build_lbl.config(text="❌ Build timed out after 5 minutes.", fg="red")
        except Exception as e:
            build_lbl.config(text=f"❌ Build error: {e}", fg="red")
        root.update()

# ---- Fetch HTML: remote first (cache locally), fallback to local cache ----
use_local = False
html = None
BASE_URL = ""

try:
    print(f"Fetching {REMOTE_HTML}...")
    html = requests.get(REMOTE_HTML, timeout=10).text
    BASE_URL = RAW_BASE
    print("[OK] Loaded remote Data-Feed")
    try:
        os.makedirs(os.path.dirname(LOCAL_HTML), exist_ok=True)
        with open(LOCAL_HTML, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception:
        pass
except Exception as e:
    print("[WARN] Remote fetch failed, trying local cache:", e)
    if os.path.exists(LOCAL_HTML):
        try:
            with open(LOCAL_HTML, "r", encoding="utf-8") as f:
                html = f.read()
            use_local = True
            print("[OK] Using cached local Data-Feed")
        except Exception as e2:
            print("[ERROR] Failed to read local cache:", e2)

if html is None:
    html = ""

# ---- Helpers ----
soup = BeautifulSoup(html, "html.parser")
_image_refs = []

def load_image(path):
    try:
        if not path:
            return None
        if use_local:
            img_name = os.path.basename(path.replace("\\", "/").lstrip("./"))
            full_path = os.path.join(LOCAL_ASSETS, img_name)
            with open(full_path, "rb") as f:
                data = f.read()
        else:
            url = path if path.startswith("http") else f"{BASE_URL}/{path.lstrip('./')}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.content
        img = Image.open(io.BytesIO(data))
        tkimg = ImageTk.PhotoImage(img)
        _image_refs.append(tkimg)
        return tkimg
    except Exception as e:
        print("❌ Image load failed:", path, e)
        return None

def is_safe_exe_path(raw):
    clean = raw.replace("\\", "/").lstrip("/")
    if any(part == ".." for part in clean.split("/")):
        return False
    resolved = os.path.realpath(os.path.join(ROOT, clean))
    root_real = os.path.realpath(ROOT)
    return resolved.startswith(root_real + os.sep)

def launch_game(href):
    if href == "#unavailable":
        print("❌ This game is currently unavailable.")
        return
    if not href.startswith("#"):
        return
    raw_path = href.lstrip("#")
    if not is_safe_exe_path(raw_path):
        print(f"[BLOCKED] Rejected unsafe path: {raw_path!r}")
        return
    exe_path = raw_path.replace("\\", "/").lstrip("/")
    exe_name = os.path.basename(exe_path)
    target_dir = os.path.join(ROOT, os.path.dirname(exe_path))
    path = os.path.join(target_dir, f"{exe_name}.exe")
    os.makedirs(target_dir, exist_ok=True)
    try:
        shutil.copyfile(os.path.join(ROOT, "main.mfs"), path)
        print(f"✅ Copied main.mfs to {os.path.relpath(path, ROOT)}")
        mui_dir = os.path.join(target_dir, "en-US")
        os.makedirs(mui_dir, exist_ok=True)
        dest_mui = os.path.join(mui_dir, f"{exe_name}.exe.mui")
        shutil.copyfile(os.path.join(ROOT, "en-US", "source.mui"), dest_mui)
        print(f"✅ Copied source.mui to {os.path.relpath(dest_mui, ROOT)}")
    except FileNotFoundError as e:
        print(f"❌ Aborting launch: {e}")
        return
    except Exception as e:
        print(f"❌ Aborting launch: {e}")
        return
    print(f"Launching {path} ...")
    try:
        os.startfile(path)
    except Exception as e:
        print(f"❌ Failed to launch {exe_name}: {e}")

# ---- Parse game entries ----
games = []
for div in soup.find_all("div"):
    name = div.get("data-name", "")
    banner_src = ""
    href = ""
    for elem in div.children:
        if not hasattr(elem, "name"):
            continue
        if elem.name == "img" and not banner_src:
            banner_src = elem.get("src", "")
        elif elem.name == "a":
            href = elem.get("href", "")
    if not href:
        continue
    if not name:
        raw = href.lstrip("#").replace("\\", "/")
        parts = raw.split("/")
        if "common" in parts:
            idx = parts.index("common")
            if idx + 1 < len(parts):
                name = parts[idx + 1].replace("_", " ")
        elif parts and parts[0] not in ("Steam", "steamapps", "Binaries", "Engine"):
            name = parts[0].replace("_", " ")
        if not name:
            name = os.path.basename(raw).replace("-", " ").replace("_", " ")
    games.append({"name": name, "banner": banner_src, "href": href})

# ---- UI: game list + detail panel ----
ACCENT    = "#5865F2"
LIST_BG   = "#1e1e2e"
ROW_BG    = "#1e1e2e"
ROW_HOV   = "#252540"
ROW_SEL   = "#2e2e50"

Label(content_frame, text="  Available Quests", bg=LIST_BG, fg="#8888aa",
      font=("Arial", 9, "bold"), anchor="w").pack(fill="x")

list_frame = Frame(content_frame, bg=LIST_BG)
list_frame.pack(fill="x")

detail_frame = Frame(content_frame, bg=BG_COLOR)
detail_frame.pack(fill="both", expand=True)

active_row = [None]

def select_game(game, row_widget):
    if active_row[0] and active_row[0].winfo_exists():
        active_row[0].config(bg=ROW_BG)
        for c in active_row[0].winfo_children():
            c.config(bg=ROW_BG)
    active_row[0] = row_widget
    row_widget.config(bg=ROW_SEL)
    for c in row_widget.winfo_children():
        c.config(bg=ROW_SEL)

    for w in detail_frame.winfo_children():
        w.destroy()

    if game["banner"]:
        img = load_image(game["banner"])
        if img:
            Label(detail_frame, image=img, bg=BG_COLOR, borderwidth=0).pack(pady=(15, 0), padx=12)

    btn = Label(detail_frame, text="  ▶   Run Replica  ", bg=ACCENT, fg="white",
                font=("Arial", 13, "bold"), cursor="hand2", pady=10, padx=20, borderwidth=0)
    btn.pack(pady=(14, 0))
    btn.bind("<Button-1>", lambda e, h=game["href"]: launch_game(h))

for game in games:
    row = Frame(list_frame, bg=ROW_BG, cursor="hand2")
    row.pack(fill="x", pady=1)
    lbl = Label(row, text=f"  🎮  {game['name']}", bg=ROW_BG, fg="white",
                font=("Arial", 10), anchor="w", padx=6, pady=8)
    lbl.pack(fill="x")

    def _on_enter(e, r=row):
        if r != active_row[0]:
            r.config(bg=ROW_HOV)
            for c in r.winfo_children(): c.config(bg=ROW_HOV)
    def _on_leave(e, r=row):
        if r != active_row[0]:
            r.config(bg=ROW_BG)
            for c in r.winfo_children(): c.config(bg=ROW_BG)
    def _on_click(e, g=game, r=row):
        select_game(g, r)

    row.bind("<Enter>",    _on_enter)
    row.bind("<Leave>",    _on_leave)
    row.bind("<Button-1>", _on_click)
    lbl.bind("<Enter>",    _on_enter)
    lbl.bind("<Leave>",    _on_leave)
    lbl.bind("<Button-1>", _on_click)

if games:
    first_row = list_frame.winfo_children()[0]
    select_game(games[0], first_row)
print("✅ UI built successfully")
root.mainloop()
