import type { Task, Reminder, Memo, LogEntry } from "@/types";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  chat: {
    send: (message: string, sessionId?: string) =>
      request<{
        reply: string;
        intent: string;
        session_id: string;
        tools_called: string[];
      }>("/api/chat", {
        method: "POST",
        body: JSON.stringify({ message, session_id: sessionId }),
      }),
  },
  tasks: {
    list: (status?: string) =>
      request<Task[]>(`/api/tasks${status ? `?status=${status}` : ""}`),
    create: (data: {
      title: string;
      description?: string;
      priority?: string;
      due_date?: string;
    }) =>
      request<Task>("/api/tasks", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (
      id: string,
      data: Partial<{
        title: string;
        status: string;
        priority: string;
        due_date: string;
      }>
    ) =>
      request<Task>(`/api/tasks/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      fetch(`/api/tasks/${id}`, { method: "DELETE" }).then((res) => {
        if (!res.ok && res.status !== 204)
          throw new Error(`API ${res.status}: ${res.statusText}`);
      }),
  },
  reminders: {
    list: (includeFired = false) =>
      request<Reminder[]>(`/api/reminders?include_fired=${includeFired}`),
    create: (data: {
      message: string;
      remind_at: string;
      is_recurring?: boolean;
      recurrence_rule?: string;
    }) =>
      request<Reminder>("/api/reminders", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      fetch(`/api/reminders/${id}`, { method: "DELETE" }).then((res) => {
        if (!res.ok && res.status !== 204)
          throw new Error(`API ${res.status}: ${res.statusText}`);
      }),
  },
  memos: {
    list: (limit = 50) => request<Memo[]>(`/api/memos?limit=${limit}`),
    get: (id: string) => request<Memo>(`/api/memos/${id}`),
    create: (data: { title?: string; content: string }) =>
      request<Memo>("/api/memos", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: string, data: { title?: string; content?: string }) =>
      request<Memo>(`/api/memos/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
  },
  logs: {
    list: (params?: { limit?: number; offset?: number; intent?: string }) => {
      const { limit = 50, offset = 0, intent } = params || {};
      const qs = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
        ...(intent ? { intent } : {}),
      });
      return request<{ count: number; offset: number; entries: LogEntry[] }>(
        `/api/logs?${qs}`
      );
    },
  },
};

// ─── Task display helpers ──────────────────────────────────────────────────

export type DueGroup = "today" | "tomorrow" | "week" | "later";

export function taskDueGroup(dueDate: string | null): DueGroup {
  if (!dueDate) return "later";
  const due = new Date(dueDate);
  const today = startOfDay(new Date());
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const endOfWeek = new Date(today);
  endOfWeek.setDate(endOfWeek.getDate() + 7);
  const dueDay = startOfDay(due);
  if (dueDay.getTime() === today.getTime()) return "today";
  if (dueDay.getTime() === tomorrow.getTime()) return "tomorrow";
  if (dueDay < endOfWeek) return "week";
  return "later";
}

export function taskDueLabel(dueDate: string | null, status: string): string {
  if (status === "done") return "完了";
  if (!dueDate) return "期限なし";
  const due = new Date(dueDate);
  const today = startOfDay(new Date());
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dueDay = startOfDay(due);
  const hhmm = due.toLocaleTimeString("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
  });
  if (dueDay.getTime() === today.getTime())
    return hhmm === "00:00" ? "今日" : `今日 ${hhmm}`;
  if (dueDay.getTime() === tomorrow.getTime())
    return hhmm === "00:00" ? "明日" : `明日 ${hhmm}`;
  return due.toLocaleDateString("ja-JP", { month: "numeric", day: "numeric" });
}

function startOfDay(d: Date): Date {
  const r = new Date(d);
  r.setHours(0, 0, 0, 0);
  return r;
}

// ─── Reminder display helpers ──────────────────────────────────────────────

export function reminderTime(remindAt: string): string {
  return new Date(remindAt).toLocaleTimeString("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function reminderNextFire(rem: Reminder): string {
  if (rem.fired && !rem.is_recurring) return "発火済";
  const due = new Date(rem.remind_at);
  const today = startOfDay(new Date());
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dueDay = startOfDay(due);
  const hhmm = due.toLocaleTimeString("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
  });
  if (dueDay.getTime() === today.getTime()) return `今日 ${hhmm}`;
  if (dueDay.getTime() === tomorrow.getTime()) return `明日 ${hhmm}`;
  return due.toLocaleDateString("ja-JP", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function reminderRepeatLabel(rem: Reminder): string {
  if (!rem.is_recurring) return "1回";
  if (!rem.recurrence_rule) return "繰り返し";
  const r = rem.recurrence_rule.toLowerCase();
  if (r.includes("daily") || r.includes("毎日")) return "毎日";
  if (r.includes("weekly") || r.includes("毎週")) return "毎週";
  if (r.includes("monthly") || r.includes("毎月")) return "毎月";
  return rem.recurrence_rule;
}
