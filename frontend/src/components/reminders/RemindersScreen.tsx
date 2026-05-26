"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { Icons } from "../icons";
import { api, reminderTime, reminderNextFire, reminderRepeatLabel } from "@/lib/api";
import type { Reminder, ConfirmHandle } from "@/types";

const REPEAT_COLORS: Record<string, string> = {
  "毎日":  "var(--accent)",
  "毎週":  "var(--warn)",
  "毎月":  "#22C58F",
  "1回":   "var(--text-muted)",
};

function repeatColor(label: string): string {
  return REPEAT_COLORS[label] || "var(--text-muted)";
}

interface ReminderRowProps {
  rem: Reminder;
  onDelete: (rem: Reminder) => void;
}

function ReminderRow({ rem, onDelete }: ReminderRowProps) {
  const enabled = !rem.fired || rem.is_recurring;
  const time = reminderTime(rem.remind_at);
  const repeat = reminderRepeatLabel(rem);
  const nextFire = reminderNextFire(rem);
  const color = repeatColor(repeat);

  return (
    <li className={`rem ${!enabled ? "is-paused" : ""}`}>
      <div className="rem-time-col">
        <div className="rem-time">{time}</div>
      </div>

      <div className="rem-main">
        <div className="rem-title">{rem.message}</div>
        <div className="rem-sub">
          <span
            className="rem-repeat"
            style={{ "--rep-color": color } as React.CSSProperties}
          >
            {repeat}
          </span>
          <span className="rem-next">次回: {nextFire}</span>
        </div>
      </div>

      <div className="rem-controls">
        <div
          style={{
            width: 8, height: 8, borderRadius: "50%",
            background: enabled ? "var(--ok)" : "var(--text-subtle)",
          }}
          title={enabled ? "有効" : "発火済"}
        />
      </div>

      <div className="rem-actions">
        <button
          type="button"
          className="icon-btn icon-btn-soft task-delete"
          title="削除"
          onClick={() => onDelete(rem)}
        >
          {Icons.trash}
        </button>
      </div>
    </li>
  );
}

interface Props {
  confirm: ConfirmHandle;
}

export default function RemindersScreen({ confirm }: Props) {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"active" | "fired" | "all">("active");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.reminders.list(true);
      setReminders(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = useMemo(() => {
    if (tab === "active") return reminders.filter((r) => !r.fired || r.is_recurring);
    if (tab === "fired") return reminders.filter((r) => r.fired && !r.is_recurring);
    return reminders;
  }, [reminders, tab]);

  const counts = useMemo(() => ({
    active: reminders.filter((r) => !r.fired || r.is_recurring).length,
    fired: reminders.filter((r) => r.fired && !r.is_recurring).length,
    all: reminders.length,
  }), [reminders]);

  const onDelete = (rem: Reminder) =>
    confirm.open({
      title: "リマインダーを削除しますか？",
      description: "このリマインダーは完全に削除されます。",
      details: [
        { label: "タイトル", value: rem.message },
        { label: "時刻",     value: reminderTime(rem.remind_at), mono: true },
        { label: "繰り返し", value: reminderRepeatLabel(rem) },
      ],
      warning: "削除は取り消せません。",
      actionLabel: "削除する",
      destructive: true,
      onConfirm: async () => {
        try {
          await api.reminders.delete(rem.id);
        } catch {
          // 削除が失敗しても UIから除去（楽観的更新）
        }
        setReminders((rs) => rs.filter((r) => r.id !== rem.id));
      },
    });

  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">リマインダー</h1>
          <span className="head-sub">
            有効 {counts.active} 件 · 発火済 {counts.fired} 件
          </span>
        </div>
        <div className="head-right">
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

      <div className="tasks-toolbar">
        <div className="tabs">
          {(
            [
              { key: "active", label: "有効",   count: counts.active },
              { key: "fired",  label: "発火済",  count: counts.fired },
              { key: "all",    label: "すべて", count: counts.all },
            ] as const
          ).map((tb) => (
            <button
              key={tb.key}
              type="button"
              className={`tab ${tab === tb.key ? "is-active" : ""}`}
              onClick={() => setTab(tb.key)}
            >
              {tb.label}
              <span className="tab-count">{tb.count}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="tasks-scroll">
        <div className="tasks-inner">
          {loading && <div className="screen-loading">読み込み中…</div>}
          {error && !loading && (
            <div className="screen-error">
              <div className="screen-error-text">{error}</div>
            </div>
          )}
          {!loading && !error && filtered.length === 0 && (
            <div className="tasks-empty">
              <div className="tasks-empty-title">
                リマインダーはありません
              </div>
              <div className="tasks-empty-sub">
                チャットから「〜をリマインドして」と伝えて登録できます。
              </div>
            </div>
          )}
          {!loading && !error && filtered.length > 0 && (
            <ul className="rem-list">
              {filtered.map((r) => (
                <ReminderRow key={r.id} rem={r} onDelete={onDelete} />
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
