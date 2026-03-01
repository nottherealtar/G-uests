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

  // Get live super properties from Discord's own module
  let superPropsB64 = null;
  for (const mod of Object.values(wpRequire.c)) {
    try {
      for (const [k, v] of Object.entries(mod?.exports || {})) {
        if (k === 'default' && typeof v?.getSuperPropertiesBase64 === 'function') {
          superPropsB64 = v.getSuperPropertiesBase64();
          break;
        }
      }
    } catch {}
    if (superPropsB64) break;
  }

  if (!token)        { alert('❌ Could not get Discord token.'); return; }
  if (!QuestsStore)  { alert('❌ QuestsStore not found.'); return; }
  if (!superPropsB64){ alert('❌ Could not get super properties.'); return; }

  console.log('[G-uests] Ready. token:', token.slice(0, 10) + '...');

  const headers = {
    'Authorization':       token,
    'Content-Type':        'application/json',
    'x-super-properties':  superPropsB64,
    'x-discord-locale':    navigator.language || 'en-US',
    'x-discord-timezone':  Intl.DateTimeFormat().resolvedOptions().timeZone,
    'x-debug-options':     'bugReporterEnabled',
  };

  // ── Step 2: Find active WATCH_VIDEO quests ────────────────────────────────
  const now = Date.now();
  const videoQuests = [...QuestsStore.quests.values()].filter(q =>
    q?.config?.expiresAt &&
    new Date(q.config.expiresAt) > now &&
    !q.userStatus?.completedAt &&
    q.userStatus?.enrolledAt &&
    (q.config?.taskConfigV2?.tasks?.WATCH_VIDEO || q.config?.taskConfigV2?.tasks?.WATCH_VIDEO_ON_MOBILE)
  );

  if (!videoQuests.length) {
    alert('No active WATCH_VIDEO quests found.\n\nEither you have none enrolled, or they are already completed.');
    return;
  }

  console.log(`[G-uests] Found ${videoQuests.length} video quest(s):`, videoQuests.map(q => q.id));

  // ── Step 3: Send progress for each quest ─────────────────────────────────
  for (const quest of videoQuests) {
    const questId    = quest.id;
    const taskConfig = quest.config?.taskConfigV2?.tasks?.WATCH_VIDEO
                    || quest.config?.taskConfigV2?.tasks?.WATCH_VIDEO_ON_MOBILE;
    const targetSeconds = taskConfig?.target || 600;

    console.log(`[G-uests] Quest ${questId} (${quest.config?.messages?.questName}) — target: ${targetSeconds}s`);

    const STEP     = 15;
    const DELAY_MS = 500;

    let current = (quest.userStatus?.progress?.WATCH_VIDEO?.value
               || quest.userStatus?.progress?.WATCH_VIDEO_ON_MOBILE?.value
               || 0) + STEP;

    while (current <= targetSeconds + STEP) {
      const ts = Math.min(current, targetSeconds);
      try {
        const res = await fetch(`${API}/quests/${questId}/video-progress`, {
          method:      'POST',
          credentials: 'include',
          headers,
          body:        JSON.stringify({ timestamp: ts }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          console.warn(`[G-uests] ${questId} @ ${ts}s — ${res.status}: ${err.message || res.statusText}`);
          if (res.status === 404) { console.warn(`[G-uests] ${questId} — endpoint not found, skipping quest.`); break; }
        } else {
          const body = await res.json().catch(() => ({}));
          console.log(`[G-uests] ${questId} — ${ts}/${targetSeconds}s | server progress: ${JSON.stringify(body?.progress || body)?.slice(0,80)}`);
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
