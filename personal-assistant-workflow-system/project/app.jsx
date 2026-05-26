// app.jsx — Personal Assistant (S01 Chat)
// Dark, Linear/Raycast-inspired desktop app shell.

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#7A8BFF",
  "density": "regular",
  "showTrafficLights": true,
  "monoTimestamps": true
}/*EDITMODE-END*/;

// ─── Icons (stroke-based, 16px, Linear/Raycast vibe) ─────────────────────────
const I = {
  chat: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2.5 6.5a3 3 0 0 1 3-3h5a3 3 0 0 1 3 3v2.5a3 3 0 0 1-3 3H7l-3 2v-2H5.5a3 3 0 0 1-3-3v-2.5Z"/>
    </svg>
  ),
  task: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2.5" y="2.5" width="11" height="11" rx="2"/>
      <path d="m5.5 8 2 2 3.5-4"/>
    </svg>
  ),
  bell: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 11V7a4 4 0 0 1 8 0v4"/>
      <path d="M2.5 11h11"/>
      <path d="M6.5 13.5a1.5 1.5 0 0 0 3 0"/>
    </svg>
  ),
  sun: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="2.5"/>
      <path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.3 3.3l1 1M11.7 11.7l1 1M3.3 12.7l1-1M11.7 4.3l1-1"/>
    </svg>
  ),
  note: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3.5 2.5h6l3 3v8a1 1 0 0 1-1 1h-8a1 1 0 0 1-1-1v-10a1 1 0 0 1 1-1Z"/>
      <path d="M9.5 2.5v3h3"/>
      <path d="M5.5 9h5M5.5 11.5h3"/>
    </svg>
  ),
  log: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="5.5"/>
      <path d="M8 5v3l2 1.5"/>
    </svg>
  ),
  cog: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="2"/>
      <path d="M13.2 9.2a5.5 5.5 0 0 0 0-2.4l1.3-1-1.3-2.3-1.6.5a5.5 5.5 0 0 0-2-1.2l-.3-1.7h-2.6l-.3 1.7a5.5 5.5 0 0 0-2 1.2l-1.6-.5L1.5 5.8l1.3 1a5.5 5.5 0 0 0 0 2.4l-1.3 1 1.3 2.3 1.6-.5a5.5 5.5 0 0 0 2 1.2l.3 1.7h2.6l.3-1.7a5.5 5.5 0 0 0 2-1.2l1.6.5 1.3-2.3-1.3-1Z"/>
    </svg>
  ),
  send: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="m3 8 10-5-3.5 12L8 9 3 8Z"/>
    </svg>
  ),
  mic: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <rect x="6" y="2.5" width="4" height="7" rx="2"/>
      <path d="M3.5 8a4.5 4.5 0 0 0 9 0"/>
      <path d="M8 12.5V14"/>
    </svg>
  ),
  check: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="m3.5 8.5 3 3 6-7"/>
    </svg>
  ),
  plus: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 3.5v9M3.5 8h9"/>
    </svg>
  ),
  search: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="7" cy="7" r="4.5"/>
      <path d="m10.5 10.5 3 3"/>
    </svg>
  ),
  command: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 5h6v6H5z"/>
      <path d="M5 5a1.5 1.5 0 1 1-1.5 1.5M11 5a1.5 1.5 0 1 0 1.5 1.5M5 11a1.5 1.5 0 1 0-1.5-1.5M11 11a1.5 1.5 0 1 1 1.5-1.5"/>
    </svg>
  ),
};

// ─── Sidebar ─────────────────────────────────────────────────────────────────
const NAV_GROUPS = [
  {
    label: null,
    items: [
      { id: "chat", name: "チャット", icon: I.chat, shortcut: "1", badge: null },
      { id: "tasks", name: "タスク", icon: I.task, shortcut: "2", badge: 3 },
      { id: "reminders", name: "リマインダー", icon: I.bell, shortcut: "3", badge: null },
      { id: "briefing", name: "ブリーフィング", icon: I.sun, shortcut: "4", badge: null },
    ],
  },
  {
    label: "アーカイブ",
    items: [
      { id: "notes", name: "メモ", icon: I.note, shortcut: "5", badge: null },
      { id: "log", name: "操作ログ", icon: I.log, shortcut: "6", badge: null },
    ],
  },
];

function Sidebar({ active, onSelect, showTrafficLights }) {
  return (
    <aside className="sidebar">
      <div className="sb-top">
        {showTrafficLights && (
          <div className="traffic">
            <span className="tl tl-r" />
            <span className="tl tl-y" />
            <span className="tl tl-g" />
          </div>
        )}
        <div className="brand">
          <div className="brand-mark">
            <svg viewBox="0 0 20 20" fill="none">
              <rect x="2" y="2" width="16" height="16" rx="4" fill="var(--accent)" fillOpacity=".18"/>
              <path d="M6 10.5 8.5 13l5.5-6" stroke="var(--accent)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="brand-text">
            <div className="brand-name">Atelier</div>
            <div className="brand-sub">Personal Assistant</div>
          </div>
        </div>
      </div>

      <button className="sb-search" type="button">
        <span className="sb-search-icon">{I.search}</span>
        <span className="sb-search-text">検索 / コマンド</span>
        <span className="kbd kbd-pill">
          <span className="kbd-glyph">{I.command}</span>K
        </span>
      </button>

      <nav className="sb-nav">
        {NAV_GROUPS.map((g, gi) => (
          <div className="sb-group" key={gi}>
            {g.label && <div className="sb-group-label">{g.label}</div>}
            <ul>
              {g.items.map((it) => (
                <li key={it.id}>
                  <button
                    type="button"
                    className={`sb-item${active === it.id ? " is-active" : ""}`}
                    onClick={() => onSelect(it.id)}
                  >
                    <span className="sb-ico">{it.icon}</span>
                    <span className="sb-name">{it.name}</span>
                    {it.badge != null && <span className="sb-badge">{it.badge}</span>}
                    <span className="kbd">{it.shortcut}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="sb-foot">
        <button
          type="button"
          className={`sb-item sb-item-sm${active === "settings" ? " is-active" : ""}`}
          onClick={() => onSelect("settings")}
        >
          <span className="sb-ico">{I.cog}</span>
          <span className="sb-name">設定</span>
          <span className="kbd">,</span>
        </button>
        <div className="sb-status">
          <span className="dot" /> 接続済 · gpt-5-mini
        </div>
      </div>
    </aside>
  );
}

// ─── Chat content (S01) ──────────────────────────────────────────────────────
const SEED_MESSAGES = [
  {
    role: "assistant",
    time: "09:58",
    text:
      "おはようございます。今日のブリーフィングを準備しました。\n直近のミーティングは 10:00 から「Aさん」、午後は 14:00 に歯医者です。未完了のタスクが 3 件あります。",
  },
  {
    role: "user",
    time: "09:59",
    text: "企画書のレビューを明日の15時に入れておいて",
  },
  {
    role: "assistant",
    time: "09:59",
    text: "了解しました。タスクとして追加しました。",
    confirm: {
      kind: "task-added",
      title: "企画書のレビュー",
      meta: "明日 15:00 · 優先度 中",
    },
  },
  {
    role: "user",
    time: "10:01",
    text: "あと、18時に薬を飲むリマインダーを毎日で。",
  },
  {
    role: "assistant",
    time: "10:01",
    text: "毎日 18:00 にリマインダーを設定しました。",
    confirm: {
      kind: "reminder-added",
      title: "薬を飲む",
      meta: "毎日 18:00 · 通知 ON",
    },
  },
  {
    role: "user",
    time: "10:04",
    text: "Aさんに今日の打ち合わせのお礼メールを下書きして、送って。",
  },
  {
    role: "assistant",
    time: "10:04",
    text:
      "以下の内容で下書きしました。送信前に確認をお願いします。",
    propose: {
      kind: "send-email",
      to: "a.tanaka@example.com",
      subject: "本日の打ち合わせのお礼",
      preview:
        "田中様\n\n本日はお時間をいただきありがとうございました。次回は来週水曜の14:00で調整いたします。",
    },
  },
];

function MessageBubble({ msg, monoTimestamps, onPropose }) {
  const isUser = msg.role === "user";
  return (
    <div className={`msg ${isUser ? "msg-user" : "msg-ai"}`}>
      <div className="msg-meta">
        <span className="msg-role">{isUser ? "あなた" : "Atelier"}</span>
        <span className={`msg-time${monoTimestamps ? " is-mono" : ""}`}>{msg.time}</span>
      </div>
      <div className="msg-body">
        {msg.text.split("\n").map((line, i) => (
          <p key={i}>{line}</p>
        ))}
        {msg.confirm && <ConfirmCard data={msg.confirm} />}
        {msg.propose && <ProposeCard data={msg.propose} onExecute={() => onPropose(msg.propose)} />}
      </div>
    </div>
  );
}

function ProposeCard({ data, onExecute }) {
  if (data.kind !== "send-email") return null;
  return (
    <div className="propose">
      <div className="propose-head">
        <span className="propose-tag">メール送信を提案</span>
        <span className="propose-tag-dot" />
        <span className="propose-tag-meta">外部送信あり</span>
      </div>
      <div className="propose-grid">
        <div className="propose-row">
          <div className="propose-label">宛先</div>
          <div className="propose-value is-mono">{data.to}</div>
        </div>
        <div className="propose-row">
          <div className="propose-label">件名</div>
          <div className="propose-value">{data.subject}</div>
        </div>
        <div className="propose-row">
          <div className="propose-label">本文</div>
          <div className="propose-value propose-preview">
            {data.preview.split("\n").map((l, i) => <div key={i}>{l || "\u00A0"}</div>)}
          </div>
        </div>
      </div>
      <div className="propose-actions">
        <button type="button" className="btn btn-quiet btn-sm">下書きを編集</button>
        <button type="button" className="btn btn-ghost btn-sm">破棄</button>
        <button type="button" className="btn btn-primary btn-sm" onClick={onExecute}>送信する…</button>
      </div>
    </div>
  );
}

function ConfirmCard({ data }) {
  const label =
    data.kind === "task-added"
      ? "タスクを追加しました"
      : data.kind === "reminder-added"
      ? "リマインダーを設定しました"
      : "完了";
  return (
    <div className="confirm">
      <div className="confirm-left">
        <span className="confirm-tick">{I.check}</span>
        <div className="confirm-text">
          <div className="confirm-label">{label}</div>
          <div className="confirm-title">{data.title}</div>
          <div className="confirm-meta">{data.meta}</div>
        </div>
      </div>
      <div className="confirm-actions">
        <button type="button" className="btn btn-ghost">取り消す</button>
        <button type="button" className="btn btn-quiet">開く ↗</button>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="msg msg-ai">
      <div className="msg-meta">
        <span className="msg-role">Atelier</span>
        <span className="msg-time is-mono">…</span>
      </div>
      <div className="typing">
        <span /><span /><span />
      </div>
    </div>
  );
}

function ChatScreen({ monoTimestamps, confirm }) {
  const [messages, setMessages] = React.useState(SEED_MESSAGES);
  const [draft, setDraft] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const scrollerRef = React.useRef(null);
  const taRef = React.useRef(null);

  React.useEffect(() => {
    const el = scrollerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, sending]);

  const autoResize = () => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 180) + "px";
  };

  const send = () => {
    const text = draft.trim();
    if (!text || sending) return;
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    const userMsg = { role: "user", time: `${hh}:${mm}`, text };
    setMessages((m) => [...m, userMsg]);
    setDraft("");
    setSending(true);
    setTimeout(() => {
      const aiMsg = {
        role: "assistant",
        time: `${hh}:${mm}`,
        text: "わかりました。承知しました。",
      };
      setMessages((m) => [...m, aiMsg]);
      setSending(false);
    }, 900);
    setTimeout(autoResize, 0);
  };

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">チャット</h1>
          <span className="head-sub">本日 · {new Date().toLocaleDateString("ja-JP", { month: "long", day: "numeric", weekday: "short" })}</span>
        </div>
        <div className="head-right">
          <button type="button" className="btn btn-ghost btn-sm">
            <span className="btn-ico">{I.plus}</span>新しい会話
          </button>
          <button type="button" className="icon-btn" title="検索">{I.search}</button>
        </div>
      </header>

      <div className="chat-scroll" ref={scrollerRef}>
        <div className="chat-inner">
          <div className="day-divider">
            <span>今日</span>
          </div>
          {messages.map((m, i) => (
            <MessageBubble
              key={i}
              msg={m}
              monoTimestamps={monoTimestamps}
              onPropose={(p) => {
                if (p.kind === "send-email") {
                  confirm.open({
                    title: "このメールを送信しますか？",
                    description: "外部の SMTP サーバに本文がそのまま送信されます。",
                    details: [
                      { label: "宛先",  value: p.to, mono: true },
                      { label: "件名",  value: p.subject },
                      { label: "本文",  value: p.preview },
                    ],
                    warning: "この操作は取り消せません。",
                    actionLabel: "送信する",
                    destructive: false,
                    onConfirm: () => {
                      const now = new Date();
                      const hh = String(now.getHours()).padStart(2, "0");
                      const mm = String(now.getMinutes()).padStart(2, "0");
                      setMessages((ms) => [
                        ...ms,
                        {
                          role: "assistant",
                          time: `${hh}:${mm}`,
                          text: "メールを送信しました。操作ログに記録しています。",
                          confirm: {
                            kind: "task-added",
                            title: p.subject,
                            meta: `${p.to} · ${hh}:${mm} 送信`,
                          },
                        },
                      ]);
                    },
                  });
                }
              }}
            />
          ))}
          {sending && <TypingIndicator />}
        </div>
      </div>

      <footer className="composer">
        <div className="composer-inner">
          <div className="composer-bar">
            <textarea
              ref={taRef}
              className="composer-input"
              rows={1}
              placeholder="メッセージを入力 — Enterで送信、Shift+Enterで改行"
              value={draft}
              onChange={(e) => { setDraft(e.target.value); autoResize(); }}
              onKeyDown={onKey}
            />
            <div className="composer-actions">
              <button type="button" className="icon-btn icon-btn-soft" title="音声入力（準備中）" disabled>{I.mic}</button>
              <button
                type="button"
                className={`send-btn${draft.trim() ? " is-ready" : ""}`}
                onClick={send}
                disabled={!draft.trim() || sending}
                title="送信 (Enter)"
              >
                {I.send}
              </button>
            </div>
          </div>
          <div className="composer-hint">
            <span className="hint-item"><span className="kbd">⏎</span>送信</span>
            <span className="hint-item"><span className="kbd">⇧⏎</span>改行</span>
            <span className="hint-item"><span className="kbd">/</span>コマンド</span>
            <span className="spacer" />
            <span className="hint-item muted">すべての操作はログに記録されます</span>
          </div>
        </div>
      </footer>
    </section>
  );
}

// ─── Empty placeholder for other screens (kept light — focus is S01) ─────────
function PlaceholderScreen({ title, sub }) {
  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">{title}</h1>
          <span className="head-sub">{sub}</span>
        </div>
      </header>
      <div className="placeholder">
        <div className="placeholder-card">
          <div className="placeholder-title">この画面は次のステップで作ります</div>
          <div className="placeholder-sub">
            現在は S01 チャット画面のみ実装しています。<br />
            サイドバーから「チャット」に戻れます。
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── App shell ───────────────────────────────────────────────────────────────
function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [active, setActive] = React.useState("chat");
  const confirm = useConfirm();

  // Apply density + accent as CSS vars
  const densityVars = {
    compact: { "--row-h": "28px", "--gap": "10px" },
    regular: { "--row-h": "32px", "--gap": "14px" },
    comfy:   { "--row-h": "36px", "--gap": "18px" },
  }[t.density] || {};

  return (
    <div className="app" style={{ "--accent": t.accent, ...densityVars }}>
      <Sidebar active={active} onSelect={setActive} showTrafficLights={t.showTrafficLights} />
      <main className="main">
        {active === "chat" && <ChatScreen monoTimestamps={t.monoTimestamps} confirm={confirm} />}
        {active === "tasks" && <TasksScreen confirm={confirm} />}
        {active === "reminders" && <RemindersScreen confirm={confirm} />}
        {active === "briefing" && <BriefingScreen />}
        {active === "notes" && <NotesScreen />}
        {active === "log" && <LogsScreen />}
        {active === "settings" && <SettingsScreen confirm={confirm} />}
      </main>

      <ConfirmModal {...confirm.props} />

      <TweaksPanel>
        <TweakSection label="外観" />
        <TweakColor
          label="アクセント"
          value={t.accent}
          options={["#7A8BFF", "#5E6AD2", "#A78BFA", "#22C58F", "#F59E0B", "#E5E7EB"]}
          onChange={(v) => setTweak("accent", v)}
        />
        <TweakRadio
          label="密度"
          value={t.density}
          options={["compact", "regular", "comfy"]}
          onChange={(v) => setTweak("density", v)}
        />
        <TweakSection label="装飾" />
        <TweakToggle
          label="トラフィックライト"
          value={t.showTrafficLights}
          onChange={(v) => setTweak("showTrafficLights", v)}
        />
        <TweakToggle
          label="タイムスタンプを等幅"
          value={t.monoTimestamps}
          onChange={(v) => setTweak("monoTimestamps", v)}
        />
        <TweakSection label="デモ" />
        <TweakButton
          label="確認ダイアログ (S08) を表示"
          onClick={() =>
            confirm.open({
              title: "このデータをリセットしますか？",
              description: "すべてのタスク・リマインダー・メモがローカルから削除されます。",
              details: [
                { label: "対象",     value: "tasks, reminders, notes, logs", mono: true },
                { label: "件数",     value: "248 件" },
                { label: "バックアップ", value: "~/atelier/backup-2026-05-24.json", mono: true },
              ],
              warning: "この操作は取り消せません。バックアップが作成されてから削除されます。",
              actionLabel: "リセットする",
              destructive: true,
              onConfirm: () => {},
            })
          }
        />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
