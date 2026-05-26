"use client";

import { useState, useEffect, useCallback } from "react";
import { Icons } from "../icons";
import { api, taskDueLabel, reminderTime } from "@/lib/api";
import type { Task, Reminder } from "@/types";

function BriefCard({
  title,
  count,
  icon,
  children,
}: {
  title: string;
  count?: number | null;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="brief-card">
      <div className="brief-card-head">
        <div className="brief-card-icon">{icon}</div>
        <div className="brief-card-title">{title}</div>
        {count != null && (
          <div className="brief-card-count">{count}</div>
        )}
      </div>
      <div className="brief-card-body">{children}</div>
    </div>
  );
}

function TaskItem({ task }: { task: Task }) {
  const pm =
    task.priority === "high"
      ? "var(--danger)"
      : task.priority === "low"
      ? "var(--text-subtle)"
      : "var(--warn)";
  return (
    <div className="brief-row">
      <span className="prio-dot" style={{ background: pm }} />
      <div className="brief-row-label">{task.title}</div>
      <div className="brief-row-due">
        {taskDueLabel(task.due_date, task.status)}
      </div>
    </div>
  );
}

function ReminderItem({ rem }: { rem: Reminder }) {
  const active = !rem.fired || rem.is_recurring;
  return (
    <div className={`brief-row${!active ? " is-paused" : ""}`}>
      <div className="brief-row-time">{reminderTime(rem.remind_at)}</div>
      <div className="brief-row-label">{rem.message}</div>
      {!active && <div className="brief-row-badge">発火済</div>}
    </div>
  );
}

export default function BriefingScreen() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [t, r] = await Promise.all([
        api.tasks.list("pending"),
        api.reminders.list(false),
      ]);
      setTasks(t);
      setReminders(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const now = new Date();
  const hour = now.getHours();
  const greeting =
    hour < 12 ? "おはようございます" : hour < 18 ? "こんにちは" : "おつかれさまです";
  const dateStr = now.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });
  const timeStr = now.toLocaleTimeString("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
  });

  const todayTasks = tasks.filter((t) => {
    if (!t.due_date) return false;
    const d = new Date(t.due_date);
    const today = new Date();
    return (
      d.getFullYear() === today.getFullYear() &&
      d.getMonth() === today.getMonth() &&
      d.getDate() === today.getDate()
    );
  });

  const todayReminders = reminders.filter((r) => {
    const d = new Date(r.remind_at);
    const today = new Date();
    return (
      d.getFullYear() === today.getFullYear() &&
      d.getMonth() === today.getMonth() &&
      d.getDate() === today.getDate()
    );
  });

  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">ブリーフィング</h1>
          <span className="head-sub">{dateStr}</span>
        </div>
        <div className="head-right">
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            title="読み上げ（準備中）"
            disabled
          >
            <span className="btn-ico">{Icons.volume}</span>
            読み上げ
          </button>
          <button
            type="button"
            className="icon-btn"
            title="更新"
            onClick={load}
          >
            {Icons.refresh}
          </button>
        </div>
      </header>

      <div className="brief-scroll">
        <div className="brief-inner">
          <div className="brief-hero">
            <div className="brief-greeting">{greeting}</div>
            <div className="brief-date">{dateStr}</div>
            <div className="brief-time">{timeStr}</div>
          </div>

          {loading ? (
            <div className="screen-loading" style={{ height: 200 }}>
              読み込み中…
            </div>
          ) : (
            <div className="brief-grid">
              {/* Tasks */}
              <BriefCard
                title="今日のタスク"
                count={todayTasks.length}
                icon={
                  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2.5" y="2.5" width="11" height="11" rx="2"/>
                    <path d="m5.5 8 2 2 3.5-4"/>
                  </svg>
                }
              >
                {todayTasks.length === 0 ? (
                  <div className="brief-row" style={{ color: "var(--text-muted)", fontSize: 12 }}>
                    今日のタスクはありません
                  </div>
                ) : (
                  todayTasks.slice(0, 5).map((t) => (
                    <TaskItem key={t.id} task={t} />
                  ))
                )}
              </BriefCard>

              {/* All pending tasks */}
              <BriefCard
                title="未完了タスク"
                count={tasks.length}
                icon={
                  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2.5" y="2.5" width="11" height="11" rx="2"/>
                    <path d="m5.5 8 2 2 3.5-4"/>
                  </svg>
                }
              >
                {tasks.length === 0 ? (
                  <div className="brief-row" style={{ color: "var(--text-muted)", fontSize: 12 }}>
                    未完了のタスクはありません
                  </div>
                ) : (
                  tasks.slice(0, 5).map((t) => (
                    <TaskItem key={t.id} task={t} />
                  ))
                )}
              </BriefCard>

              {/* Reminders */}
              <BriefCard
                title="今日のリマインダー"
                count={todayReminders.length}
                icon={
                  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 11V7a4 4 0 0 1 8 0v4"/>
                    <path d="M2.5 11h11"/>
                    <path d="M6.5 13.5a1.5 1.5 0 0 0 3 0"/>
                  </svg>
                }
              >
                {todayReminders.length === 0 ? (
                  <div className="brief-row" style={{ color: "var(--text-muted)", fontSize: 12 }}>
                    今日のリマインダーはありません
                  </div>
                ) : (
                  todayReminders.map((r) => (
                    <ReminderItem key={r.id} rem={r} />
                  ))
                )}
              </BriefCard>

              {/* All reminders */}
              <BriefCard
                title="すべてのリマインダー"
                count={reminders.length}
                icon={
                  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 11V7a4 4 0 0 1 8 0v4"/>
                    <path d="M2.5 11h11"/>
                    <path d="M6.5 13.5a1.5 1.5 0 0 0 3 0"/>
                  </svg>
                }
              >
                {reminders.length === 0 ? (
                  <div className="brief-row" style={{ color: "var(--text-muted)", fontSize: 12 }}>
                    リマインダーはありません
                  </div>
                ) : (
                  reminders.slice(0, 5).map((r) => (
                    <ReminderItem key={r.id} rem={r} />
                  ))
                )}
              </BriefCard>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
