"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { Icons } from "../icons";
import { api, taskDueGroup, taskDueLabel, type DueGroup } from "@/lib/api";
import type { Task, ConfirmHandle } from "@/types";

const GROUP_ORDER: Array<{ key: DueGroup; label: string }> = [
  { key: "today",    label: "今日" },
  { key: "tomorrow", label: "明日" },
  { key: "week",     label: "今週" },
  { key: "later",    label: "後で" },
];

const PRIORITY_META: Record<string, { dot: string; label: string }> = {
  high:   { dot: "var(--danger)", label: "高" },
  medium: { dot: "var(--warn)",   label: "中" },
  low:    { dot: "var(--text-subtle)", label: "低" },
};

function getPriorityMeta(p: string) {
  return PRIORITY_META[p] || PRIORITY_META.medium;
}

interface TaskRowProps {
  task: Task;
  onToggle: (id: string) => void;
  onDelete: (task: Task) => void;
}

function TaskRow({ task, onToggle, onDelete }: TaskRowProps) {
  const done = task.status === "done";
  const pm = getPriorityMeta(task.priority);
  const dueLabel = taskDueLabel(task.due_date, task.status);

  return (
    <li className={`task ${done ? "is-done" : ""}`}>
      <button
        type="button"
        className={`task-check ${done ? "is-checked" : ""}`}
        onClick={() => onToggle(task.id)}
        aria-pressed={done}
        title={done ? "未完了に戻す" : "完了にする"}
      >
        {done && (
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m4 8 3 3 5-6"/>
          </svg>
        )}
      </button>

      <div className="task-main">
        <div className="task-title">{task.title}</div>
        {task.description && (
          <div className="task-sub">
            <span style={{ color: "var(--text-muted)", fontSize: "11.5px" }}>
              {task.description}
            </span>
          </div>
        )}
      </div>

      <div className="task-meta">
        <div className="task-priority" title={`優先度 ${pm.label}`}>
          <span className="prio-dot" style={{ background: pm.dot }} />
          <span className="prio-label">{pm.label}</span>
        </div>
        <div className="task-due">{dueLabel}</div>
      </div>

      <div className="task-actions">
        <button
          type="button"
          className="icon-btn icon-btn-soft task-delete"
          title="削除"
          onClick={() => onDelete(task)}
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

export default function TasksScreen({ confirm }: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"open" | "done" | "all">("open");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.tasks.list();
      setTasks(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = useMemo(() => {
    if (tab === "open") return tasks.filter((t) => t.status !== "done");
    if (tab === "done") return tasks.filter((t) => t.status === "done");
    return tasks;
  }, [tasks, tab]);

  const groups = useMemo(() => {
    const buckets: Record<DueGroup, Task[]> = {
      today: [], tomorrow: [], week: [], later: [],
    };
    for (const t of filtered) {
      const g = taskDueGroup(t.due_date);
      buckets[g].push(t);
    }
    return GROUP_ORDER.filter((g) => buckets[g.key].length > 0).map((g) => ({
      ...g,
      items: buckets[g.key],
    }));
  }, [filtered]);

  const counts = useMemo(() => ({
    open: tasks.filter((t) => t.status !== "done").length,
    done: tasks.filter((t) => t.status === "done").length,
    all: tasks.length,
  }), [tasks]);

  const onToggle = async (id: string) => {
    const task = tasks.find((t) => t.id === id);
    if (!task) return;
    const newStatus = task.status === "done" ? "pending" : "done";
    setTasks((ts) =>
      ts.map((t) => (t.id === id ? { ...t, status: newStatus } : t))
    );
    try {
      await api.tasks.update(id, { status: newStatus });
    } catch {
      setTasks((ts) =>
        ts.map((t) => (t.id === id ? { ...t, status: task.status } : t))
      );
    }
  };

  const onDelete = (task: Task) =>
    confirm.open({
      title: "タスクを削除しますか？",
      description: "このタスクは完全に削除されます。",
      details: [{ label: "タイトル", value: task.title }],
      warning: "この操作は取り消せません。",
      actionLabel: "削除する",
      destructive: true,
      onConfirm: async () => {
        try {
          await api.tasks.delete(task.id);
        } catch {
          // 削除が失敗しても UIから除去（楽観的更新）
        }
        setTasks((ts) => ts.filter((t) => t.id !== task.id));
      },
    });

  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">タスク</h1>
          <span className="head-sub">
            未完了 {counts.open} 件 · 完了 {counts.done} 件
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
              { key: "open", label: "未完了", count: counts.open },
              { key: "done", label: "完了",   count: counts.done },
              { key: "all",  label: "すべて", count: counts.all },
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
          {loading && (
            <div className="screen-loading">読み込み中…</div>
          )}
          {error && !loading && (
            <div className="screen-error">
              <div className="screen-error-text">{error}</div>
            </div>
          )}
          {!loading && !error && groups.length === 0 && (
            <div className="tasks-empty">
              <div className="tasks-empty-title">
                {tab === "open"
                  ? "未完了のタスクはありません"
                  : "該当するタスクはありません"}
              </div>
              <div className="tasks-empty-sub">
                チャットから「〜をタスクに追加して」と伝えて登録できます。
              </div>
            </div>
          )}
          {!loading && !error &&
            groups.map((g) => (
              <div className="task-group" key={g.key}>
                <div className="task-group-head">
                  <span className="task-group-label">{g.label}</span>
                  <span className="task-group-count">{g.items.length}</span>
                  <span className="task-group-rule" />
                </div>
                <ul className="task-list">
                  {g.items.map((t) => (
                    <TaskRow
                      key={t.id}
                      task={t}
                      onToggle={onToggle}
                      onDelete={onDelete}
                    />
                  ))}
                </ul>
              </div>
            ))}
        </div>
      </div>
    </section>
  );
}
