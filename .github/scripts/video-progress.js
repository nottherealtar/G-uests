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

  // ── Step 1: Find QuestsStore and API module ───────────────────────────────
  const wpRequire = webpackChunkdiscord_app.push([[Symbol()], {}, r => r]);
  webpackChunkdiscord_app.pop();

  let QuestsStore = null;
  let api = null;

  for (const mod of Object.values(wpRequire.c)) {
    try {
      for (const val of Object.values(mod?.exports || {})) {
        if (typeof val?.getQuest === 'function' && val.quests instanceof Map) QuestsStore = val;
        if (!api && (typeof val?.post === 'function') && (typeof val?.get === 'function') && val?.post?.toString().includes('url')) api = val;
      }
    } catch {}
    if (QuestsStore && api) break;
  }

  if (!QuestsStore) { alert('❌ QuestsStore not found.'); return; }
  if (!api) { alert('❌ Discord API module not found.'); return; }

  // ── Step 2: Find active video quests ─────────────────────────────────────
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
    const targetSeconds = quest.config?.taskConfig?.targetMinutes * 60
                       || quest.config?.taskConfig?.targetDuration
                       || 600; // fallback 10 min

    console.log(`[G-uests] Starting video quest ${questId} — target: ${targetSeconds}s`);

    const STEP     = 15;   // seconds per update
    const DELAY_MS = 500;  // ms between requests (avoid rate limiting)

    let current = (quest.userStatus?.progress?.video?.timestamp || 0) + STEP;

    while (current <= targetSeconds + STEP) {
      try {
        await api.post({
          url:  `/quests/${questId}/video-progress`,
          body: { timestamp: Math.min(current, targetSeconds) },
        });
        console.log(`[G-uests] Quest ${questId} — progress: ${current}/${targetSeconds}s`);
      } catch (e) {
        console.warn(`[G-uests] Quest ${questId} — request failed at ${current}s:`, e?.message);
      }
      current += STEP;
      await new Promise(r => setTimeout(r, DELAY_MS));
    }

    console.log(`[G-uests] ✅ Quest ${questId} video progress complete.`);
  }

  alert(`✅ Video progress sent for ${videoQuests.length} quest(s).\n\nCheck your Discord quests panel to confirm completion.`);

})();
