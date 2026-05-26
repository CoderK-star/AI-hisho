// logs.jsx — S06 Operation log
//
// Chronological list (newest first). Each entry:
// - Timestamp / intent / tool / external API badge / result
// - Expandable detail row
// Read-only (append-only log UI expression)

const SEED_LOGS = [
  {
    id: "l1",
    time: "2026-05-24 10:04",
    intent: "メール送信",
    tool: "external.smtp.send",
    external: true,
    externalTarget: "SMTP → a.tanaka@example.com",
    result: "success",
    detail: "件名: 本日の打ち合わせのお礼\n宛先: a.tanaka@example.com\n本文: 田中様 — 本日はお時間をいただき…（省略）\nMessage-ID: <abc123@atelier.local>",
  },
  {
    id: "l2",
    time: "2026-05-24 10:02",
    intent: "タスク追加",
    tool: "internal.tasks.add",
    external: false,
    externalTarget: null,
    result: "success",
    detail: "title: 企画書のレビュー\ndue: 2026-05-25T15:00\npriority: medium\nsource: chat (user request)",
  },
  {
    id: "l3",
    time: "2026-05-24 10:01",
    intent: "リマインダー設定",
    tool: "internal.reminders.add",
    external: false,
    externalTarget: null,
    result: "success",
    detail: "title: 薬を飲む\ntime: 18:00\nrepeat: daily\nnotify: true",
  },
  {
    id: "l4",
    time: "2026-05-24 09:58",
    intent: "ブリーフィング生成",
    tool: "internal.tasks.list, internal.reminders.list, external.calendar.fetch",
    external: true,
    externalTarget: "OpenAI API (gpt-5-mini)",
    result: "success",
    detail: "tasks: 3 件取得\nreminders: 2 件取得\ncalendar: Google Calendar API → 3 件取得\nLLM tokens: 1,240 input / 380 output\nlatency: 820ms",
  },
  {
    id: "l5",
    time: "2026-05-24 09:55",
    intent: "起動・初期化",
    tool: "internal.system.init",
    external: false,
    externalTarget: null,
    result: "success",
    detail: "version: 0.4.2\ndb: ~/.atelier/data.sqlite (12.4 MB)\nLLM provider: openai\nmodel: gpt-5-mini",
  },
  {
    id: "l6",
    time: "2026-05-23 22:00",
    intent: "夜ブリーフィング生成",
    tool: "internal.tasks.list, external.llm.generate",
    external: true,
    externalTarget: "OpenAI API (gpt-5-mini)",
    result: "success",
    detail: "summary: 本日の完了タスク2件、明日の予定3件\nLLM tokens: 980 input / 290 output",
  },
  {
    id: "l7",
    time: "2026-05-23 18:00",
    intent: "リマインダー発火",
    tool: "internal.reminders.fire",
    external: false,
    externalTarget: null,
    result: "success",
    detail: "reminder: 薬を飲む\nnotification: OS notification sent\nack: user dismissed at 18:02",
  },
  {
    id: "l8",
    time: "2026-05-23 14:20",
    intent: "メモ作成",
    tool: "internal.notes.create",
    external: false,
    externalTarget: null,
    result: "success",
    detail: "title: 競合調査メモ\nbody: 380 chars\nsource: chat (user request)",
  },
];

const RESULT_META = {
  success: { label: "成功", cls: "is-ok" },
  failure: { label: "失敗", cls: "is-err" },
  pending: { label: "実行中", cls: "is-pending" },
};

function LogEntry({ log }) {
  const [open, setOpen] = React.useState(false);
  const res = RESULT_META[log.result] || RESULT_META.success;

  return (
    <div className={`log-entry${open ? " is-open" : ""}`}>
      <button
        type="button"
        className="log-row"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <div className="log-time">{log.time}</div>
        <div className="log-intent">{log.intent}</div>
        <div className="log-tool">{log.tool.split(",")[0].trim()}{log.tool.includes(",") ? " …" : ""}</div>
        {log.external && (
          <div className="log-ext-badge" title={log.externalTarget}>
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6 10 14 2M14 2h-5M14 2v5" />
              <path d="M12 9v4a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h4" />
            </svg>
            外部送信
          </div>
        )}
        <div className={`log-result ${res.cls}`}>{res.label}</div>
        <div className="log-chevron">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
            <path d="m5 6 3 3 3-3" />
          </svg>
        </div>
      </button>

      {open && (
        <div className="log-detail">
          {log.external && (
            <div className="log-detail-ext">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M6 10 14 2M14 2h-5M14 2v5" />
                <path d="M12 9v4a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h4" />
              </svg>
              <span>{log.externalTarget}</span>
            </div>
          )}
          <div className="log-detail-tool">
            <span className="log-detail-label">ツール:</span>
            <span className="log-detail-value">{log.tool}</span>
          </div>
          <pre className="log-detail-pre">{log.detail}</pre>
        </div>
      )}
    </div>
  );
}

function LogsScreen() {
  const [filter, setFilter] = React.useState("all"); // all | external | internal

  const filtered = React.useMemo(() => {
    if (filter === "external") return SEED_LOGS.filter((l) => l.external);
    if (filter === "internal") return SEED_LOGS.filter((l) => !l.external);
    return SEED_LOGS;
  }, [filter]);

  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">操作ログ</h1>
          <span className="head-sub">{SEED_LOGS.length} 件の記録</span>
        </div>
      </header>

      <div className="tasks-toolbar">
        <div className="tabs">
          {[
            { key: "all", label: "すべて", count: SEED_LOGS.length },
            { key: "external", label: "外部送信あり", count: SEED_LOGS.filter((l) => l.external).length },
            { key: "internal", label: "内部のみ", count: SEED_LOGS.filter((l) => !l.external).length },
          ].map((tb) => (
            <button
              key={tb.key}
              type="button"
              className={`tab ${filter === tb.key ? "is-active" : ""}`}
              onClick={() => setFilter(tb.key)}
            >
              {tb.label}
              <span className="tab-count">{tb.count}</span>
            </button>
          ))}
        </div>
        <div className="tasks-toolbar-right">
          <div className="log-readonly-badge">追記専用 · 編集不可</div>
        </div>
      </div>

      <div className="tasks-scroll">
        <div className="tasks-inner">
          {filtered.map((l) => (
            <LogEntry key={l.id} log={l} />
          ))}
          {filtered.length === 0 && (
            <div className="tasks-empty">
              <div className="tasks-empty-title">該当するログはありません</div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { LogsScreen });
