import type { TopicOption } from "./api";

const COOKIE_NAME = "case_breaker_progress";
const MAX_TOPICS = 24;

export type TopicProgress = { attempts: number; passes: number };
export type LearnerProgress = Record<string, TopicProgress>;

export function readProgress(): LearnerProgress {
  const entry = document.cookie.split("; ").find((item) => item.startsWith(`${COOKIE_NAME}=`));
  if (!entry) return {};
  try {
    const parsed: unknown = JSON.parse(decodeURIComponent(entry.slice(COOKIE_NAME.length + 1)));
    if (!parsed || typeof parsed !== "object") return {};
    return Object.fromEntries(Object.entries(parsed).slice(0, MAX_TOPICS).flatMap(([topic, value]) => {
      if (!value || typeof value !== "object") return [];
      const record = value as Partial<TopicProgress>;
      return typeof record.attempts === "number" && typeof record.passes === "number"
        ? [[topic, { attempts: Math.max(0, record.attempts), passes: Math.max(0, record.passes) }]]
        : [];
    }));
  } catch { return {}; }
}

export function recordOutcome(topic: TopicOption, passed: boolean): LearnerProgress {
  const progress = readProgress();
  const current = progress[topic] ?? { attempts: 0, passes: 0 };
  const next = { ...progress, [topic]: { attempts: current.attempts + 1, passes: current.passes + Number(passed) } };
  document.cookie = `${COOKIE_NAME}=${encodeURIComponent(JSON.stringify(next))}; Path=/; Max-Age=15552000; SameSite=Lax`;
  return next;
}
