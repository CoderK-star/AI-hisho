// tasks.jsx — S02 Task list
//
// Linear-style list: tab (未完了/完了/すべて) + grouped rows (今日/明日/今週/後で)
// Hover reveals row actions. Delete opens S08 ConfirmModal.

const SEED_TASKS = [
  { id: "t1", title: "企画書のレビュー",        due: "today",     dueLabel: "今日 15:00",   priority: "high",  done: false, project: "Q3 計画" },
  { id: "t2", title: "経費精算の提出",          due: "today",     dueLabel: "今日",         priority: "med",   done: false, project: null },
  { id: "t3", title: "Aさんへのフォローアップ", due: "tomorrow",  dueLabel: "明日 10:00",   priority: "med",   done: false, project: "営業" },
  { id: "t4", title: "週報の下書き",            due: "tomorrow",  dueLabel: "明日",         priority: "low",   done: false, project: null },
  { id: "t5", title: "競合調査のまとめ",        due: "week",      dueLabel: "水曜",         priority: "med",   done: false, project: "リサーチ" },
  { id: "t6", title: "ライブラリ更新の確認",    due: "week",      dueLabel: "金曜",         priority: "low",   done: false, project: null },
  { id: "t7", title: "プロジェクト構成のメモ",  due: "later",     dueLabel: "期限なし",     priority: "low",   done: false, project: null },
  { id: "t8", title: "VPN 設定の更新",          due: "today",     dueLabel: "10:02 完了",   priority: "low",   done: true,  project: null },
  { id: "t9", title: "請求書の確認",            due: "today",     dueLabel: "昨日 完了",    priority: "med",   done: true,  project: "経理" },
];

const GROUP_ORDER = [
  { key: "today",    label: "今日" },
  { key: "tomorrow", label: "明日" },
  { key: "week",     label: "今週" },
  { key: "later",    label: "後で" },
];

const PRIORITY_META = {
  high: { dot: "var(--danger)", label: "高" },
  med:  { dot: "var(--warn)",   label: "中" },
  low:  { dot: "var(--text-subtle)", label: "低" },
};

function TaskRow({ task, onToggle, onDelete }) {
  return (
    <li className={`task ${task.done ? "is-done" : ""}`}>
      <button
        type="button"
        className={`task-check ${task.done ? "is-checked" : ""}`}
        onClick={() => onToggle(task.id)}
        aria-pressed={task.done}
        title={task.done ? "未完了に戻す" : "完了にする"}
      >
        {task.done && (
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m4 8 3 3 5-6" />
          </svg>
        )}
      </button>

      <div className="task-main">
        <div className="task-title">{task.title}</div>
        {task.project && (
          <div className="task-sub">
            <span className="task-project">{task.project}</span>
          </div>
        )}
      </div>

      <div className="task-meta">
        <div className="task-priority" title={`優先度 ${PRIORITY_META[task.priority].label}`}>
          <span className="prio-dot" style={{ background: PRIORITY_META[task.priority].dot }} />
          <span className="prio-label">{PRIORITY_META[task.priority].label}</span>
        </div>
        <div className="task-due">{task.dueLabel}</div>
      </div>

      <div className="task-actions">
        <button type="button" className="icon-btn icon-btn-soft" title="編集">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
            <path d="m3 13 7-7 2.5 2.5-7 7H3v-2.5Z" />
            <path d="m9.5 6.5 2.5 2.5" />
          </svg>
        </button>
        <button
          type="button"
          className="icon-btn icon-btn-soft task-delete"
          title="削除"
          onClick={() => onDelete(task)}
        >
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 4h10M6 4V2.5h4V4M5 4l.5 9a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1L11 4" />
          </svg>
        </button>
      </div>
    </li>
  );
}

function TasksScreen({ confirm }) {
  const [tasks, setTasks] = React.useState(SEED_TASKS);
  const [tab, setTab] = React.useState("open"); // open | done | all

  const filtered = React.useMemo(() => {
    if (tab === "open") return tasks.filter((t) => !t.done);
    if (tab === "done") return tasks.filter((t) => t.done);
    return tasks;
  }, [tasks, tab]);

  const groups = React.useMemo(() => {
    const buckets = Object.fromEntries(GROUP_ORDER.map((g) => [g.key, []]));
    for (const t of filtered) (buckets[t.due] || (buckets[t.due] = [])).push(t);
    return GROUP_ORDER.filter((g) => buckets[g.key].length > 0).map((g) => ({
      ...g,
      items: buckets[g.key],
    }));
  }, [filtered]);

  const counts = React.useMemo(
    () => ({
      open: tasks.filter((t) => !t.done).length,
      done: tasks.filter((t) => t.done).length,
      all: tasks.length,
    }),
    [tasks]
  );

  const onToggle = (id) =>
    setTasks((ts) => ts.map((t) => (t.id === id ? { ...t, done: !t.done } : t)));

  const onDelete = (task) =>
    confirm.open({
      title: "タスクを削除しますか？",
      description: "このタスクは完全に削除され、操作ログには記録が残ります。",
      details: [
        { label: "タイトル", value: task.title },
        { label: "締切",     value: task.dueLabel, mono: true },
        { label: "優先度",   value: PRIORITY_META[task.priority].label },
      ],
      warning: "この操作は取り消せません。",
      actionLabel: "削除する",
      destructive: true,
      onConfirm: () => setTasks((ts) => ts.filter((t) => t.id !== task.id)),
    });

  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">タスク</h1>
          <span className="head-sub">未完了 {counts.open} 件 · 完了 {counts.done} 件</span>
        </div>
        <div className="head-right">
          <button type="button" className="btn btn-ghost btn-sm">
            <span className="btn-ico">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8 3.5v9M3.5 8h9" />
              </svg>
            </span>
            新規タスク
          </button>
          <button type="button" className="icon-btn" title="フィルター">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2.5 4h11M4.5 8h7M6.5 12h3" />
            </svg>
          </button>
        </div>
      </header>

      <div className="tasks-toolbar">
        <div className="tabs">
          {[
            { key: "open", label: "未完了", count: counts.open },
            { key: "done", label: "完了",   count: counts.done },
            { key: "all",  label: "すべて", count: counts.all },
          ].map((tb) => (
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
        <div className="tasks-toolbar-right">
          <button type="button" className="btn btn-quiet btn-sm">
            並び替え: 締切順
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" style={{ width: 11, height: 11 }}>
              <path d="m4 6 4 4 4-4" />
            </svg>
          </button>
        </div>
      </div>

      <div className="tasks-scroll">
        <div className="tasks-inner">
          {groups.length === 0 ? (
            <div className="tasks-empty">
              <div className="tasks-empty-title">該当するタスクはありません</div>
              <div className="tasks-empty-sub">タブを切り替えるか、新しいタスクを追加してください。</div>
            </div>
          ) : (
            groups.map((g) => (
              <div className="task-group" key={g.key}>
                <div className="task-group-head">
                  <span className="task-group-label">{g.label}</span>
                  <span className="task-group-count">{g.items.length}</span>
                  <span className="task-group-rule" />
                </div>
                <ul className="task-list">
                  {g.items.map((t) => (
                    <TaskRow key={t.id} task={t} onToggle={onToggle} onDelete={onDelete} />
                  ))}
                </ul>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { TasksScreen });
