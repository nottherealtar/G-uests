# Guests — Game Quest Player for Discord

A lightweight Python GUI that lets you complete Discord Quests without downloading full games. Made by **Tar**.

---

### How It Works

Guests fetches active quest data from the [G-uests](https://github.com/nottherealtar/G-uests) data feed, then emulates the required local game file structure and launches a placeholder executable so Discord registers game activity.

---

### Setup

**Requirements:** Python 3, then:
```bash
pip install requests beautifulsoup4 Pillow
```

**Run:**
```bash
python questHunter.py
```

The app auto-compiles the placeholder executable (`main.mfs`) on first run if `gif.py` is present.

---

### Usage

1. Launch the app — it fetches the latest active quests automatically.
2. Select a game from the list.
3. Click **Run Replica**.
4. Keep the process running until your Discord Quest progress updates (typically 15–30 minutes).
5. Close when done.

---

### Keeping Quests Up to Date

Quest IDs are managed in the [G-uests](https://github.com/nottherealtar/G-uests) repo. When new Discord quests appear, run the sync script from the Discord desktop app DevTools console (`sync-quests.js`) to push new IDs — this triggers the GitHub Action to rebuild the feed automatically.

---

### Disclaimer

For educational and convenience purposes only. Use responsibly. Spoofing game presence may violate Discord's Terms of Service. Use at your own risk.

---

### License

MIT — see `LICENSE`.
