// reminders.jsx — S03 Reminder list
//
// Similar structure to Tasks, but with:
// - Enable/disable toggle (pause, not delete)
// - Repeat badge (毎日 / 毎週 / 1回)
// - Fire time prominent

const SEED_REMINDERS = [
  { id: "r1", title: "薬を飲む",             time: "18:00", repeat: "毎日",   enabled: true,  nextFire: "今日 18:00" },
  { id: "r2", title: "ゴミ出し",             time: "07:30", repeat: "毎週火", enabled: true,  nextFire: "火曜 07:30" },
  { id: "r3", title: "週報を書く",           time: "17:00", repeat: "毎週金", enabled: true,  nextFire: "金曜 17:00" },
  { id: "r4", title: "歯医者の予約確認",     time: "09:00", repeat: "1回",    enabled: true,  nextFire: "明日 09:00" },
  { id: "r5", title: "サブスク更新確認",     time: "10:00", repeat: "毎月1日", enabled: true,  nextFire: "6/1 10:00" },
  { id: "r6", title: "ストレッチ",           time: "12:00", repeat: "毎日",   enabled: false, nextFire: "一時停止中" },
  { id: "r7", title: "プロテイン",           time: "07:00", repeat: "毎日",   enabled: false, nextFire: "一時停止中" },
];

const REPEAT_COLORS = {
  "毎日":   "var(--accent)",
  "毎週火": "var(--warn)",
  "毎週金": "var(--warn)",
  "1回":    "var(--text-muted)",
  "毎月1日": "#22C58F",
};

function ReminderRow({ rem, onToggle, onDelete }) {
  return (
    <li className={`rem ${!rem.enabled ? "is-paused" : ""}`}>
      <div className="rem-time-col">
        <div className="rem-time">{rem.time}</div>
      </div>

      <div className="rem-main">
        <div className="rem-title">{rem.title}</div>
        <div className="rem-sub">
          <span
            className="rem-repeat"
            style={{ "--rep-color": REPEAT_COLORS[rem.repeat] || "var(--text-muted)" }}
          >
            {rem.repeat}
          </span>
          <span className="rem-next">次回: {rem.nextFire}</span>
        </div>
      </div>

      <div className="rem-controls">
        <label className="toggle" title={rem.enabled ? "一時停止" : "有効にする"}>
          <input
            type="checkbox"
            checked={rem.enabled}
            onChange={() => onToggle(rem.id)}
          />
          <span className="toggle-track">
            <span className="toggle-thumb" />
          </span>
        </label>
      </div>

      <div className="rem-actions">
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
          onClick={() => onDelete(rem)}
        >
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 4h10M6 4V2.5h4V4M5 4l.5 9a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1L11 4" />
          </svg>
        </button>
      </div>
    </li>
  );
}

function RemindersScreen({ confirm }) {
  const [reminders, setReminders] = React.useState(SEED_REMINDERS);
  const [tab, setTab] = React.useState("active"); // active | paused | all

  const filtered = React.useMemo(() => {
    if (tab === "active") return reminders.filter((r) => r.enabled);
    if (tab === "paused") return reminders.filter((r) => !r.enabled);
    return reminders;
  }, [reminders, tab]);

  const counts = React.useMemo(() => ({
    active: reminders.filter((r) => r.enabled).length,
    paused: reminders.filter((r) => !r.enabled).length,
    all: reminders.length,
  }), [reminders]);

  const onToggle = (id) =>
    setReminders((rs) =>
      rs.map((r) =>
        r.id === id
          ? {
              ...r,
              enabled: !r.enabled,
              nextFire: !r.enabled ? "再開済" : "一時停止中",
            }
          : r
      )
    );

  const onDelete = (rem) =>
    confirm.open({
      title: "リマインダーを削除しますか？",
      description: "このリマインダーは完全に削除されます。一時停止する場合はトグルをオフにしてください。",
      details: [
        { label: "タイトル", value: rem.title },
        { label: "時刻",     value: rem.time, mono: true },
        { label: "繰り返し", value: rem.repeat },
      ],
      warning: "削除は取り消せません。",
      actionLabel: "削除する",
      destructive: true,
      onConfirm: () => setReminders((rs) => rs.filter((r) => r.id !== rem.id)),
    });

  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">リマインダー</h1>
          <span className="head-sub">有効 {counts.active} 件 · 停止 {counts.paused} 件</span>
        </div>
        <div className="head-right">
          <button type="button" className="btn btn-ghost btn-sm">
            <span className="btn-ico">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M8 3.5v9M3.5 8h9" /></svg>
            </span>
            新規
          </button>
        </div>
      </header>

      <div className="tasks-toolbar">
        <div className="tabs">
          {[
            { key: "active", label: "有効",   count: counts.active },
            { key: "paused", label: "停止中", count: counts.paused },
            { key: "all",    label: "すべて", count: counts.all },
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
      </div>

      <div className="tasks-scroll">
        <div className="tasks-inner">
          {filtered.length === 0 ? (
            <div className="tasks-empty">
              <div className="tasks-empty-title">該当するリマインダーはありません</div>
              <div className="tasks-empty-sub">チャットから「〜をリマインドして」と伝えるか、新規ボタンで追加できます。</div>
            </div>
          ) : (
            <ul className="rem-list">
              {filtered.map((r) => (
                <ReminderRow key={r.id} rem={r} onToggle={onToggle} onDelete={onDelete} />
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { RemindersScreen });
