"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { Icons } from "../icons";
import { api } from "@/lib/api";
import type { Memo } from "@/types";

function simpleMarkdown(text: string): React.ReactNode[] {
  return text.split("\n").map((line, i) => {
    if (/^## /.test(line))
      return <h3 className="md-h3" key={i}>{line.replace(/^## /, "")}</h3>;
    if (/^# /.test(line))
      return <h2 className="md-h2" key={i}>{line.replace(/^# /, "")}</h2>;
    if (/^- /.test(line))
      return (
        <div className="md-li" key={i}>
          <span className="md-bullet">–</span>
          {line.replace(/^- /, "")}
        </div>
      );
    if (/^\d+\. /.test(line)) {
      const num = line.match(/^(\d+)\./)?.[1] ?? "1";
      return (
        <div className="md-li md-ol" key={i}>
          <span className="md-num">{num}.</span>
          {line.replace(/^\d+\. /, "")}
        </div>
      );
    }
    if (line.trim() === "") return <div className="md-spacer" key={i} />;
    return <p className="md-p" key={i}>{line}</p>;
  });
}

export default function NotesScreen() {
  const [memos, setMemos] = useState<Memo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [localEdits, setLocalEdits] = useState<Record<string, { title: string; content: string }>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.memos.list(50);
      setMemos(data);
      if (!activeId && data.length > 0) setActiveId(data[0].id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  }, [activeId]);

  useEffect(() => { load(); }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const filtered = useMemo(() => {
    if (!search.trim()) return memos;
    const q = search.toLowerCase();
    return memos.filter(
      (n) =>
        n.title.toLowerCase().includes(q) ||
        n.content.toLowerCase().includes(q)
    );
  }, [memos, search]);

  const active = memos.find((n) => n.id === activeId) || filtered[0] || null;
  const edit = active ? localEdits[active.id] : undefined;
  const displayTitle = edit?.title ?? active?.title ?? "";
  const displayContent = edit?.content ?? active?.content ?? "";

  const patchLocal = (id: string, patch: Partial<{ title: string; content: string }>) => {
    const base = localEdits[id] ?? { title: active?.title ?? "", content: active?.content ?? "" };
    setLocalEdits((prev) => ({ ...prev, [id]: { ...base, ...patch } }));
  };

  const addMemo = async () => {
    const now = new Date().toISOString();
    try {
      const m = await api.memos.create({ title: "無題のメモ", content: "" });
      setMemos((ms) => [m, ...ms]);
      setActiveId(m.id);
      setEditing(true);
    } catch {
      const fake: Memo = {
        id: "local-" + Date.now(),
        title: "無題のメモ",
        content: "",
        created_at: now,
        updated_at: now,
      };
      setMemos((ms) => [fake, ...ms]);
      setActiveId(fake.id);
      setEditing(true);
    }
  };

  const saveEdits = async () => {
    if (!active || !edit) return;
    setSaving(true);
    try {
      const isLocal = active.id.startsWith("local-");
      if (isLocal) {
        // まだ DB に存在しない仮メモ → 新規作成
        const created = await api.memos.create({ title: edit.title, content: edit.content });
        setMemos((ms) => ms.map((m) => (m.id === active.id ? created : m)));
        setActiveId(created.id);
      } else {
        // 既存メモ → 更新
        const updated = await api.memos.update(active.id, { title: edit.title, content: edit.content });
        setMemos((ms) => ms.map((m) => (m.id === active.id ? updated : m)));
      }
      setLocalEdits((prev) => {
        const next = { ...prev };
        delete next[active.id];
        return next;
      });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleString("ja-JP", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <section className="screen notes-screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">メモ</h1>
          <span className="head-sub">{memos.length} 件</span>
        </div>
        <div className="head-right">
          <button type="button" className="btn btn-ghost btn-sm" onClick={addMemo}>
            <span className="btn-ico">{Icons.plus}</span>
            新規メモ
          </button>
        </div>
      </header>

      <div className="notes-body">
        {/* List pane */}
        <div className="notes-list-pane">
          <div className="notes-search-wrap">
            <span className="notes-search-icon">{Icons.search}</span>
            <input
              className="notes-search"
              type="text"
              placeholder="メモを検索…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          {loading ? (
            <div style={{ padding: "20px 14px", textAlign: "center", fontSize: 12, color: "var(--text-muted)" }}>
              読み込み中…
            </div>
          ) : error ? (
            <div style={{ padding: "20px 14px", textAlign: "center", fontSize: 12, color: "var(--danger)" }}>
              {error}
            </div>
          ) : (
            <ul className="notes-list">
              {filtered.map((n) => (
                <li key={n.id}>
                  <button
                    type="button"
                    className={`notes-item${active && active.id === n.id ? " is-active" : ""}`}
                    onClick={() => { setActiveId(n.id); setEditing(false); }}
                  >
                    <div className="notes-item-title">
                      {localEdits[n.id]?.title ?? n.title}
                    </div>
                    <div className="notes-item-meta">
                      <span className="notes-item-date">{formatDate(n.updated_at)}</span>
                      <span className="notes-item-preview">
                        {(localEdits[n.id]?.content ?? n.content)
                          .replace(/^#+\s*/gm, "")
                          .replace(/\n/g, " ")
                          .slice(0, 60)}
                      </span>
                    </div>
                  </button>
                </li>
              ))}
              {filtered.length === 0 && (
                <div className="notes-empty">一致するメモはありません</div>
              )}
            </ul>
          )}
        </div>

        {/* Detail pane */}
        <div className="notes-detail-pane">
          {active ? (
            <>
              <div className="notes-detail-head">
                {editing ? (
                  <input
                    className="notes-title-input"
                    value={displayTitle}
                    onChange={(e) => active && patchLocal(active.id, { title: e.target.value })}
                    autoFocus
                    placeholder="タイトル"
                  />
                ) : (
                  <h2
                    className="notes-detail-title"
                    onClick={() => setEditing(true)}
                    title="クリックして編集"
                  >
                    {displayTitle || "無題のメモ"}
                  </h2>
                )}
                <div className="notes-detail-meta">
                  <span>作成 {formatDate(active.created_at)}</span>
                  <span style={{ color: "var(--text-subtle)" }}>·</span>
                  <span>更新 {formatDate(active.updated_at)}</span>
                </div>
                <div className="notes-detail-actions" style={{ display: "flex", gap: 6 }}>
                  <button
                    type="button"
                    className={`btn btn-ghost btn-sm${editing ? " is-active-btn" : ""}`}
                    onClick={() => setEditing(!editing)}
                  >
                    {editing ? "プレビュー" : "編集"}
                  </button>
                  {editing && edit && (
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={saveEdits}
                      disabled={saving}
                    >
                      {saving ? "保存中…" : "保存"}
                    </button>
                  )}
                </div>
              </div>
              <div className="notes-detail-body">
                {editing ? (
                  <textarea
                    className="notes-editor"
                    value={displayContent}
                    onChange={(e) =>
                      active && patchLocal(active.id, { content: e.target.value })
                    }
                    placeholder="Markdown で記述…"
                  />
                ) : (
                  <div className="notes-rendered">
                    {simpleMarkdown(displayContent)}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="notes-no-sel">
              <div className="notes-no-sel-text">
                {loading ? "読み込み中…" : "メモを選択してください"}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
