// notes.jsx — S05 Notes list + detail
//
// Left: list with search + titles/dates/preview
// Right: detail pane with editable title + body (plain text, Markdown-ish display)
// Auto-save simulated

const SEED_NOTES = [
  {
    id: "n1",
    title: "Q3 計画のアイデア",
    body: "## 方針\n\n- 新規機能は3つまでに絞る\n- パフォーマンス改善を優先\n- ユーザーインタビューを月2回\n\n## スケジュール\n\n6月: 設計フェーズ\n7月: 実装フェーズ\n8月: テスト・リリース",
    created: "2026-05-22 14:30",
    updated: "2026-05-24 09:15",
  },
  {
    id: "n2",
    title: "ミーティングメモ — Aさん",
    body: "参加者: 自分、Aさん\n\n- 企画書は来週までにレビュー\n- 予算は前期比 +10% で調整\n- 次回: 来週水曜 14:00",
    created: "2026-05-24 10:30",
    updated: "2026-05-24 10:30",
  },
  {
    id: "n3",
    title: "読みたい本リスト",
    body: "- 思考の整理学\n- エンジニアリング組織論への招待\n- Team Topologies\n- Designing Data-Intensive Applications",
    created: "2026-05-20 08:00",
    updated: "2026-05-23 19:40",
  },
  {
    id: "n4",
    title: "競合調査メモ",
    body: "## A社\n\n- 価格帯: 月額 ¥2,000\n- 特徴: カレンダー連携が強い\n\n## B社\n\n- 価格帯: 月額 ¥1,500\n- 特徴: AI チャットが中心",
    created: "2026-05-18 16:20",
    updated: "2026-05-21 11:00",
  },
  {
    id: "n5",
    title: "VPN 設定手順",
    body: "1. WireGuard をインストール\n2. 設定ファイルを /etc/wireguard/ に配置\n3. sudo wg-quick up wg0\n4. 接続確認: curl ifconfig.me",
    created: "2026-05-15 09:00",
    updated: "2026-05-15 09:00",
  },
];

function simpleMarkdown(text) {
  // Very lightweight: headings, bold, list items, line breaks
  return text.split("\n").map((line, i) => {
    if (/^## /.test(line)) {
      return <h3 className="md-h3" key={i}>{line.replace(/^## /, "")}</h3>;
    }
    if (/^# /.test(line)) {
      return <h2 className="md-h2" key={i}>{line.replace(/^# /, "")}</h2>;
    }
    if (/^- /.test(line)) {
      return <div className="md-li" key={i}><span className="md-bullet">–</span>{line.replace(/^- /, "")}</div>;
    }
    if (/^\d+\. /.test(line)) {
      const num = line.match(/^(\d+)\./)[1];
      return <div className="md-li md-ol" key={i}><span className="md-num">{num}.</span>{line.replace(/^\d+\. /, "")}</div>;
    }
    if (line.trim() === "") {
      return <div className="md-spacer" key={i} />;
    }
    return <p className="md-p" key={i}>{line}</p>;
  });
}

function NotesScreen() {
  const [notes, setNotes] = React.useState(SEED_NOTES);
  const [activeId, setActiveId] = React.useState(SEED_NOTES[0].id);
  const [search, setSearch] = React.useState("");
  const [editing, setEditing] = React.useState(false);

  const filtered = React.useMemo(() => {
    if (!search.trim()) return notes;
    const q = search.toLowerCase();
    return notes.filter(
      (n) => n.title.toLowerCase().includes(q) || n.body.toLowerCase().includes(q)
    );
  }, [notes, search]);

  const active = notes.find((n) => n.id === activeId) || filtered[0] || null;

  const updateNote = (id, patch) =>
    setNotes((ns) =>
      ns.map((n) =>
        n.id === id
          ? { ...n, ...patch, updated: new Date().toLocaleString("ja-JP", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).replace(/\//g, "-") }
          : n
      )
    );

  const addNote = () => {
    const now = new Date().toLocaleString("ja-JP", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).replace(/\//g, "-");
    const n = { id: "n" + Date.now(), title: "無題のメモ", body: "", created: now, updated: now };
    setNotes((ns) => [n, ...ns]);
    setActiveId(n.id);
    setEditing(true);
  };

  return (
    <section className="screen notes-screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">メモ</h1>
          <span className="head-sub">{notes.length} 件</span>
        </div>
        <div className="head-right">
          <button type="button" className="btn btn-ghost btn-sm" onClick={addNote}>
            <span className="btn-ico">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M8 3.5v9M3.5 8h9" /></svg>
            </span>
            新規メモ
          </button>
        </div>
      </header>

      <div className="notes-body">
        {/* ─ List pane ─ */}
        <div className="notes-list-pane">
          <div className="notes-search-wrap">
            <span className="notes-search-icon">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"><circle cx="7" cy="7" r="4.5" /><path d="m10.5 10.5 3 3" /></svg>
            </span>
            <input
              className="notes-search"
              type="text"
              placeholder="メモを検索…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <ul className="notes-list">
            {filtered.map((n) => (
              <li key={n.id}>
                <button
                  type="button"
                  className={`notes-item${active && active.id === n.id ? " is-active" : ""}`}
                  onClick={() => { setActiveId(n.id); setEditing(false); }}
                >
                  <div className="notes-item-title">{n.title}</div>
                  <div className="notes-item-meta">
                    <span className="notes-item-date">{n.updated}</span>
                    <span className="notes-item-preview">
                      {n.body.replace(/^#+\s*/gm, "").replace(/\n/g, " ").slice(0, 60)}
                    </span>
                  </div>
                </button>
              </li>
            ))}
            {filtered.length === 0 && (
              <div className="notes-empty">一致するメモはありません</div>
            )}
          </ul>
        </div>

        {/* ─ Detail pane ─ */}
        <div className="notes-detail-pane">
          {active ? (
            <>
              <div className="notes-detail-head">
                {editing ? (
                  <input
                    className="notes-title-input"
                    value={active.title}
                    onChange={(e) => updateNote(active.id, { title: e.target.value })}
                    autoFocus
                  />
                ) : (
                  <h2
                    className="notes-detail-title"
                    onClick={() => setEditing(true)}
                    title="クリックして編集"
                  >
                    {active.title}
                  </h2>
                )}
                <div className="notes-detail-meta">
                  <span>作成 {active.created}</span>
                  <span className="brief-sep">·</span>
                  <span>更新 {active.updated}</span>
                </div>
                <div className="notes-detail-actions">
                  <button
                    type="button"
                    className={`btn btn-ghost btn-sm${editing ? " is-active-btn" : ""}`}
                    onClick={() => setEditing(!editing)}
                  >
                    {editing ? "プレビュー" : "編集"}
                  </button>
                </div>
              </div>
              <div className="notes-detail-body">
                {editing ? (
                  <textarea
                    className="notes-editor"
                    value={active.body}
                    onChange={(e) => updateNote(active.id, { body: e.target.value })}
                    placeholder="Markdown で記述…"
                  />
                ) : (
                  <div className="notes-rendered">
                    {simpleMarkdown(active.body)}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="notes-no-sel">
              <div className="notes-no-sel-text">メモを選択してください</div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { NotesScreen });
