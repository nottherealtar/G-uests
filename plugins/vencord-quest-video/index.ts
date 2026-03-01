/**
 * Vencord Plugin — Quest Video Auto-Complete
 * ─────────────────────────────────────────────────────────────────────────────
 * Automatically completes WATCH_VIDEO Discord quests by sending incremental
 * timestamp progress to Discord's API.
 *
 * INSTALL:
 *   1. Clone Vencord: https://github.com/Vendicated/Vencord
 *   2. Copy this folder to src/userplugins/questVideoComplete/
 *   3. Build Vencord: pnpm build  (or pnpm watch for dev)
 *   4. Enable the plugin in Vencord settings
 *
 * USAGE:
 *   Type /completequests in any Discord channel.
 *   The command runs silently (only visible to you) and toasts progress.
 */

import definePlugin from "@utils/types";
import { findByPropsLazy } from "@webpack";
import { showToast, Toasts } from "@webpack/common";

const API = "https://discord.com/api/v9";
const STEP = 15;       // seconds per update
const DELAY = 500;     // ms between requests

const TokenModule    = findByPropsLazy("getToken");
const SuperPropsModule = findByPropsLazy("getSuperPropertiesBase64");
const QuestsStore    = findByPropsLazy("getQuest");

function getHeaders(): Record<string, string> {
    return {
        "Authorization":      TokenModule.getToken(),
        "Content-Type":       "application/json",
        "x-super-properties": SuperPropsModule.getSuperPropertiesBase64(),
        "x-discord-locale":   navigator.language || "en-US",
        "x-discord-timezone": Intl.DateTimeFormat().resolvedOptions().timeZone,
        "x-debug-options":    "bugReporterEnabled",
    };
}

async function completeVideoQuests(): Promise<void> {
    const now = Date.now();

    const quests = QuestsStore.quests instanceof Map
        ? [...QuestsStore.quests.values()]
        : [];

    const videoQuests = quests.filter((q: any) =>
        q?.config?.expiresAt &&
        new Date(q.config.expiresAt).getTime() > now &&
        !q.userStatus?.completedAt &&
        q.userStatus?.enrolledAt &&
        (q.config?.taskConfigV2?.tasks?.WATCH_VIDEO ||
         q.config?.taskConfigV2?.tasks?.WATCH_VIDEO_ON_MOBILE)
    );

    if (!videoQuests.length) {
        showToast("No active WATCH_VIDEO quests found.", Toasts.Type.MESSAGE);
        return;
    }

    showToast(`Found ${videoQuests.length} video quest(s) — starting...`, Toasts.Type.MESSAGE);

    for (const quest of videoQuests) {
        const questId    = quest.id;
        const taskConfig = quest.config?.taskConfigV2?.tasks?.WATCH_VIDEO
                        ?? quest.config?.taskConfigV2?.tasks?.WATCH_VIDEO_ON_MOBILE;
        const target     = taskConfig?.target ?? 600;
        const questName  = quest.config?.messages?.questName ?? questId;

        let current = (
            quest.userStatus?.progress?.WATCH_VIDEO?.value ??
            quest.userStatus?.progress?.WATCH_VIDEO_ON_MOBILE?.value ??
            0
        ) + STEP;

        let failed = false;

        while (current <= target + STEP) {
            const ts = Math.min(current, target);
            try {
                const res = await fetch(`${API}/quests/${questId}/video-progress`, {
                    method:      "POST",
                    credentials: "include",
                    headers:     getHeaders(),
                    body:        JSON.stringify({ timestamp: ts }),
                });

                if (!res.ok) {
                    if (res.status === 404) {
                        showToast(`❌ ${questName}: endpoint not found.`, Toasts.Type.FAILURE);
                        failed = true;
                        break;
                    }
                    const err = await res.json().catch(() => ({})) as any;
                    console.warn(`[QuestVideo] ${questId} @ ${ts}s — ${res.status}: ${err.message}`);
                }
            } catch (e: any) {
                console.warn(`[QuestVideo] ${questId} — fetch error:`, e?.message);
            }

            current += STEP;
            await new Promise(r => setTimeout(r, DELAY));
        }

        if (!failed) {
            showToast(`✅ ${questName} — complete!`, Toasts.Type.SUCCESS);
        }
    }
}

export default definePlugin({
    name: "QuestVideoAutoComplete",
    description: "Auto-completes WATCH_VIDEO Discord quests via /completequests",
    authors: [{ name: "Tar", id: 985226198508511302n }],

    commands: [
        {
            name: "completequests",
            description: "Auto-complete all active WATCH_VIDEO quests",
            execute: async () => {
                completeVideoQuests().catch(e =>
                    showToast(`Error: ${e?.message}`, Toasts.Type.FAILURE)
                );
                return { content: "⏳ Quest video auto-complete started — check toasts for progress." };
            },
        },
    ],
});
