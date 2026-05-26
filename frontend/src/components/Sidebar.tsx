"use client";

import { Icons } from "./icons";

export type ScreenId =
  | "chat"
  | "tasks"
  | "reminders"
  | "briefing"
  | "notes"
  | "log"
  | "settings";

const NAV_GROUPS: Array<{
  label: string | null;
  items: Array<{
    id: ScreenId;
    name: string;
    icon: React.ReactNode;
    shortcut: string;
    badge?: number | null;
  }>;
}> = [
  {
    label: null,
    items: [
      { id: "chat",      name: "チャット",       icon: Icons.chat,  shortcut: "1" },
      { id: "tasks",     name: "タスク",         icon: Icons.task,  shortcut: "2" },
      { id: "reminders", name: "リマインダー",   icon: Icons.bell,  shortcut: "3" },
      { id: "briefing",  name: "ブリーフィング", icon: Icons.sun,   shortcut: "4" },
    ],
  },
  {
    label: "アーカイブ",
    items: [
      { id: "notes", name: "メモ",     icon: Icons.note, shortcut: "5" },
      { id: "log",   name: "操作ログ", icon: Icons.log,  shortcut: "6" },
    ],
  },
];

interface Props {
  active: ScreenId;
  onSelect: (id: ScreenId) => void;
}

export default function Sidebar({ active, onSelect }: Props) {
  return (
    <aside className="sidebar">
      <div className="sb-top">
        <div className="traffic">
          <span className="tl tl-r" />
          <span className="tl tl-y" />
          <span className="tl tl-g" />
        </div>
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
        <span className="sb-search-icon">{Icons.search}</span>
        <span className="sb-search-text">検索 / コマンド</span>
        <span className="kbd kbd-pill">
          <span className="kbd-glyph">{Icons.command}</span>K
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
                    {it.badge != null && (
                      <span className="sb-badge">{it.badge}</span>
                    )}
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
          <span className="sb-ico">{Icons.cog}</span>
          <span className="sb-name">設定</span>
          <span className="kbd">,</span>
        </button>
        <div className="sb-status">
          <span className="dot" />
          接続済
        </div>
      </div>
    </aside>
  );
}
