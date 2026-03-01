/**
 * G-uests Quest Sync Bookmarklet
 * ─────────────────────────────────────────────────────────────────────────────
 * Run this inside the Discord desktop app's DevTools console, or save it as a
 * bookmarklet. It reads active quest IDs from Discord's internal QuestsStore,
 * then commits them to quests-config.json in your GitHub repo — which
 * automatically triggers the GitHub Action to rebuild the data feed.
 *
 * SETUP:
 *   1. Create a GitHub fine-grained PAT at https://github.com/settings/tokens
 *      → Repository access: nottherealtar/G-uests
 *      → Permissions: Contents = Read and write
 *   2. Replace YOUR_GITHUB_PAT below with that token
 *   3. To use as a bookmarklet: minify this script and prefix with "javascript:"
 *      (use https://www.toptal.com/developers/javascript-minifier)
 *
 * USAGE:
 *   - Open Discord desktop app
 *   - Press Ctrl+Shift+I to open DevTools
 *   - Paste this script into the Console tab and press Enter
 *   - A popup will confirm how many quest IDs were synced
 */

(async function GuestSync() {

  // ── CONFIG ── replace before use ─────────────────────────────────────────
  const GITHUB_TOKEN = 'YOUR_GITHUB_PAT';
  const REPO_OWNER   = 'nottherealtar';
  const REPO_NAME    = 'G-uests';
  const CONFIG_PATH  = 'quests-config.json';
  // ─────────────────────────────────────────────────────────────────────────

  // ── Step 1: Read active quest IDs from Discord's internal Flux store ──────
  let questIds = [];
  try {
    if (typeof webpackChunkdiscord_app === 'undefined') {
      throw new Error('webpackChunkdiscord_app not found — run this inside the Discord desktop app.');
    }

    const wpRequire = webpackChunkdiscord_app.push([[Symbol()], {}, r => r]);
    webpackChunkdiscord_app.pop();

    const find = filter => Object.values(wpRequire.c).find(x => {
      try { return filter(x); } catch { return false; }
    });

    // Try multiple selector patterns across Discord build variants
    const QuestsStore =
      find(x => x?.exports?.A?.proto?.getQuest)?.exports?.A  ||
      find(x => x?.exports?.Z?.proto?.getQuest)?.exports?.Z  ||
      find(x => x?.exports?.ZP?.proto?.getQuest)?.exports?.ZP;

    if (!QuestsStore) throw new Error('QuestsStore module not found in this Discord build.');

    const now = Date.now();
    questIds = [...QuestsStore.quests.values()]
      .filter(q =>
        q?.config?.expiresAt &&
        new Date(q.config.expiresAt).getTime() > now &&
        !q.userStatus?.completedAt
      )
      .map(q => String(q.id))
      .filter(Boolean);

    console.log('[G-uests] Active quest IDs found:', questIds);
  } catch (err) {
    alert('❌ Failed to read QuestsStore:\n' + err.message);
    return;
  }

  if (questIds.length === 0) {
    alert('No active quests found in your Discord client.\n\nMake sure you have quests available and haven\'t already completed them all.');
    return;
  }

  // ── Step 2: Fetch current quests-config.json from GitHub ─────────────────
  const apiUrl  = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${CONFIG_PATH}`;
  const headers = {
    'Authorization': `token ${GITHUB_TOKEN}`,
    'Accept':        'application/vnd.github.v3+json',
    'Content-Type':  'application/json',
  };

  let currentSha  = null;
  let existingIds = [];

  try {
    const res = await fetch(apiUrl, { headers });
    if (res.ok) {
      const file    = await res.json();
      currentSha    = file.sha;
      const decoded = JSON.parse(atob(file.content.replace(/\s/g, '')));
      existingIds   = decoded.quest_ids || [];
    }
  } catch (err) {
    console.warn('[G-uests] Could not read existing config (will create fresh):', err);
  }

  // ── Step 3: Merge, deduplicate ────────────────────────────────────────────
  const merged = [...new Set([...existingIds, ...questIds])];
  const added  = questIds.filter(id => !existingIds.includes(id));

  if (added.length === 0) {
    alert(`ℹ️ All ${questIds.length} active quest(s) are already in the config.\nNothing to update.`);
    return;
  }

  // ── Step 4: Commit updated config to GitHub ───────────────────────────────
  const newContent = JSON.stringify({ quest_ids: merged }, null, 2) + '\n';
  const encoded    = btoa(unescape(encodeURIComponent(newContent)));
  const body       = {
    message: `chore: sync quest IDs [${added.join(', ')}]`,
    content: encoded,
    ...(currentSha ? { sha: currentSha } : {}),
  };

  try {
    const res = await fetch(apiUrl, {
      method:  'PUT',
      headers,
      body:    JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || res.statusText);
    }

    alert(
      `✅ Synced!\n\n` +
      `Added ${added.length} new quest ID(s):\n${added.join('\n')}\n\n` +
      `The GitHub Action is now rebuilding the data feed.`
    );
  } catch (err) {
    alert('❌ Failed to update GitHub:\n' + err.message + '\n\nCheck that your GITHUB_PAT is correct and has Contents write access.');
  }

})();
