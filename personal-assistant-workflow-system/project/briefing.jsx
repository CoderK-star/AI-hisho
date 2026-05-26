// briefing.jsx — S04 Briefing screen
//
// Card-based sections: greeting, schedule, tasks, reminders
// Read-only daily summary — mirrors what the AI says in chat S01

function BriefingScreen() {
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

  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">ブリーフィング</h1>
          <span className="head-sub">{dateStr}</span>
        </div>
        <div className="head-right">
          <button type="button" className="btn btn-ghost btn-sm" title="読み上げ（準備中）" disabled>
            <span className="btn-ico">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 5.5h2l3-2.5v10l-3-2.5H3a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1Z" />
                <path d="M10.5 5a4 4 0 0 1 0 6M12.5 3.5a6.5 6.5 0 0 1 0 9" />
              </svg>
            </span>
            読み上げ
          </button>
        </div>
      </header>

      <div className="brief-scroll">
        <div className="brief-inner">
          {/* ─ Greeting ─ */}
          <div className="brief-hero">
            <div className="brief-greeting">{greeting}</div>
            <div className="brief-date">{dateStr}</div>
            <div className="brief-time">{timeStr}</div>
          </div>

          <div className="brief-grid">
            {/* ─ Schedule ─ */}
            <BriefCard
              title="今日の予定"
              count={3}
              icon={
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="3" width="12" height="11" rx="2" />
                  <path d="M5 1.5v3M11 1.5v3M2 7.5h12" />
                </svg>
              }
            >
              <BriefScheduleItem time="10:00" label="ミーティング（Aさん）" accent={false} />
              <BriefScheduleItem time="14:00" label="歯医者" accent={false} />
              <BriefScheduleItem time="16:30" label="デザインレビュー" accent={false} />
            </BriefCard>

            {/* ─ Tasks ─ */}
            <BriefCard
              title="未完了タスク"
              count={3}
              icon={
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2.5" y="2.5" width="11" height="11" rx="2" />
                  <path d="m5.5 8 2 2 3.5-4" />
                </svg>
              }
            >
              <BriefTaskItem title="企画書のレビュー" due="今日 15:00" priority="high" />
              <BriefTaskItem title="経費精算の提出" due="今日" priority="med" />
              <BriefTaskItem title="Aさんへのフォローアップ" due="明日 10:00" priority="med" />
            </BriefCard>

            {/* ─ Reminders ─ */}
            <BriefCard
              title="今日のリマインダー"
              count={2}
              icon={
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 11V7a4 4 0 0 1 8 0v4" />
                  <path d="M2.5 11h11" />
                  <path d="M6.5 13.5a1.5 1.5 0 0 0 3 0" />
                </svg>
              }
            >
              <BriefReminderItem time="12:00" label="ストレッチ" paused={true} />
              <BriefReminderItem time="18:00" label="薬を飲む" paused={false} />
            </BriefCard>

            {/* ─ Weather placeholder ─ */}
            <BriefCard
              title="天気"
              count={null}
              icon={
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="6" cy="6" r="2.5" />
                  <path d="M6 1.5v1M6 9.5v1M1.5 6h1M9.5 6h1M3 3l.7.7M8.3 8.3l.7.7M3 9l.7-.7M8.3 3.7l.7-.7" />
                  <path d="M9 10a3 3 0 0 1 5 2.2 2 2 0 0 1-.5 3.8H7a2.5 2.5 0 0 1 2-5Z" />
                </svg>
              }
            >
              <div className="brief-weather">
                <div className="brief-weather-temp">24°C</div>
                <div className="brief-weather-desc">晴れ時々くもり</div>
                <div className="brief-weather-range">
                  <span>最高 28°C</span>
                  <span className="brief-sep">·</span>
                  <span>最低 18°C</span>
                </div>
              </div>
            </BriefCard>
          </div>
        </div>
      </div>
    </section>
  );
}

function BriefCard({ title, count, icon, children }) {
  return (
    <div className="brief-card">
      <div className="brief-card-head">
        <div className="brief-card-icon">{icon}</div>
        <div className="brief-card-title">{title}</div>
        {count != null && <div className="brief-card-count">{count}</div>}
      </div>
      <div className="brief-card-body">{children}</div>
    </div>
  );
}

function BriefScheduleItem({ time, label }) {
  return (
    <div className="brief-row">
      <div className="brief-row-time">{time}</div>
      <div className="brief-row-label">{label}</div>
    </div>
  );
}

function BriefTaskItem({ title, due, priority }) {
  const dotColor =
    priority === "high" ? "var(--danger)" : priority === "med" ? "var(--warn)" : "var(--text-subtle)";
  return (
    <div className="brief-row">
      <span className="prio-dot" style={{ background: dotColor }} />
      <div className="brief-row-label">{title}</div>
      <div className="brief-row-due">{due}</div>
    </div>
  );
}

function BriefReminderItem({ time, label, paused }) {
  return (
    <div className={`brief-row${paused ? " is-paused" : ""}`}>
      <div className="brief-row-time">{time}</div>
      <div className="brief-row-label">{label}</div>
      {paused && <div className="brief-row-badge">停止中</div>}
    </div>
  );
}

Object.assign(window, { BriefingScreen });
