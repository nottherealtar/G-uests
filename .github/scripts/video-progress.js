/**
 * G-uests Video Quest Auto-Watcher
 * ─────────────────────────────────────────────────────────────────────────────
 * Run this inside the Discord desktop app's DevTools console.
 * Finds all active WATCH_VIDEO quests and sends progress updates to Discord's
 * API to simulate watching the required video, completing the quest.
 *
 * USAGE:
 *   - Open Discord desktop app
 *   - Press Ctrl+Shift+I to open DevTools
 *   - Type "allow pasting" and press Enter
 *   - Paste this script into the Console tab and press Enter
 */

(async function VideoWatcher() {

  const API = 'https://discord.com/api/v9';

  // ── Step 1: Get Discord token from internal store ─────────────────────────
  const wpRequire = webpackChunkdiscord_app.push([[Symbol()], {}, r => r]);
  webpackChunkdiscord_app.pop();

  let token = null;
  let QuestsStore = null;

  for (const mod of Object.values(wpRequire.c)) {
    try {
      for (const val of Object.values(mod?.exports || {})) {
        if (!token && typeof val?.getToken === 'function') {
          const t = val.getToken();
          if (typeof t === 'string' && t.length > 20) token = t;
        }
        if (!QuestsStore && typeof val?.getQuest === 'function' && val.quests instanceof Map) {
          QuestsStore = val;
        }
      }
    } catch {}
    if (token && QuestsStore) break;
  }

  if (!token)       { alert('❌ Could not get Discord token.'); return; }
  if (!QuestsStore) { alert('❌ QuestsStore not found.'); return; }

  const headers = {
    'Authorization': token,
    'Content-Type':  'application/json',
  };

  // ── Step 2: Find active WATCH_VIDEO quests ────────────────────────────────
  const now = Date.now();
  const videoQuests = [...QuestsStore.quests.values()].filter(q =>
    q?.config?.expiresAt &&
    new Date(q.config.expiresAt) > now &&
    !q.userStatus?.completedAt &&
    q.userStatus?.enrolledAt &&
    q.config?.taskConfig?.taskType === 'WATCH_VIDEO'
  );

  if (!videoQuests.length) {
    alert('No active WATCH_VIDEO quests found.\n\nEither you have none enrolled, or they are already completed.');
    return;
  }

  console.log(`[G-uests] Found ${videoQuests.length} video quest(s):`, videoQuests.map(q => q.id));

  // ── Step 3: Send progress for each quest ─────────────────────────────────
  for (const quest of videoQuests) {
    const questId       = quest.id;
    const targetSeconds = (quest.config?.taskConfig?.targetMinutes ?? 0) * 60
                       || quest.config?.taskConfig?.targetDuration
                       || 600;

    console.log(`[G-uests] Quest ${questId} — target: ${targetSeconds}s`);

    const STEP     = 15;
    const DELAY_MS = 500;

    let current = ((quest.userStatus?.progress?.video?.timestamp) || 0) + STEP;

    while (current <= targetSeconds + STEP) {
      const ts = Math.min(current, targetSeconds);
      try {
        const res = await fetch(`${API}/quests/${questId}/video-progress`, {
          method:  'POST',
          headers,
          body:    JSON.stringify({ timestamp: ts }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          console.warn(`[G-uests] ${questId} @ ${ts}s — ${res.status}: ${err.message || res.statusText}`);
        } else {
          console.log(`[G-uests] ${questId} — ${ts}/${targetSeconds}s`);
        }
      } catch (e) {
        console.warn(`[G-uests] ${questId} — fetch error:`, e.message);
      }
      current += STEP;
      await new Promise(r => setTimeout(r, DELAY_MS));
    }

    console.log(`[G-uests] ✅ Quest ${questId} done.`);
  }

  alert(`✅ Video progress sent for ${videoQuests.length} quest(s).\nCheck your Discord quests panel to confirm completion.`);

})();
