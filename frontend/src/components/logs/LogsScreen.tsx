"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { Icons } from "../icons";
import { api } from "@/lib/api";
import type { LogEntry } from "@/types";

const RESULT_META: Record<string, { label: string; cls: string }> = {
  success: { label: "成功",   cls: "is-ok" },
  failure: { label: "失敗",   cls: "is-err" },
  error:   { label: "失敗",   cls: "is-err" },
  pending: { label: "実行中", cls: "is-pending" },
};

function formatTimestamp(ts: string): string {
  return new Date(ts).toLocaleString("ja-JP", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function LogEntryRow({ log }: { log: LogEntry }) {
  const [open, setOpen] = useState(false);
  const res = RESULT_META[log.result] ?? RESULT_META.success;
  const hasExternal =
    (log.external_apis_called && log.external_apis_called.length > 0);
  const firstTool = log.tools_called[0] ?? "";
  const moreTool = log.tools_called.length > 1 ? " …" : "";

  return (
    <div className={`log-entry${open ? " is-open" : ""}`}>
      <button
        type="button"
        className="log-row"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <div className="log-time">{formatTimestamp(log.timestamp)}</div>
        <div className="log-intent">{log.intent}</div>
        <div className="log-tool">{firstTool}{moreTool}</div>
        {hasExternal && (
          <div className="log-ext-badge" title={(log.external_apis_called ?? []).join(", ")}>
            {Icons.externalLink}
            外部送信
          </div>
        )}
        {!hasExternal && <div />}
        <div className={`log-result ${res.cls}`}>{res.label}</div>
        <div className="log-chevron">{Icons.chevronDown}</div>
      </button>

      {open && (
        <div className="log-detail">
          {hasExternal && (
            <div className="log-detail-ext">
              {Icons.externalLink}
              <span>{(log.external_apis_called ?? []).join(", ")}</span>
            </div>
          )}
          {log.tools_called.length > 0 && (
            <div className="log-detail-tool">
              <span className="log-detail-label">ツール:</span>
              <span className="log-detail-value">{log.tools_called.join(", ")}</span>
            </div>
          )}
          {log.input_summary && (
            <pre className="log-detail-pre">{log.input_summary}</pre>
          )}
          {log.session_id && (
            <div className="log-detail-tool">
              <span className="log-detail-label">セッション:</span>
              <span className="log-detail-value">{log.session_id}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function LogsScreen() {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "external" | "internal">("all");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.logs.list({ limit: 100 });
      setEntries(data.entries);
      setTotal(data.count);
    } catch (e) {
      setError(e instanceof Error ? e.message : "読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = useMemo(() => {
    if (filter === "external")
      return entries.filter(
        (l) => l.external_apis_called && l.external_apis_called.length > 0
      );
    if (filter === "internal")
      return entries.filter(
        (l) => !l.external_apis_called || l.external_apis_called.length === 0
      );
    return entries;
  }, [entries, filter]);

  const extCount = entries.filter(
    (l) => l.external_apis_called && l.external_apis_called.length > 0
  ).length;
  const intCount = entries.length - extCount;

  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">操作ログ</h1>
          <span className="head-sub">{total} 件の記録</span>
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
              { key: "all",      label: "すべて",      count: entries.length },
              { key: "external", label: "外部送信あり", count: extCount },
              { key: "internal", label: "内部のみ",     count: intCount },
            ] as const
          ).map((tb) => (
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
          {loading && <div className="screen-loading">読み込み中…</div>}
          {error && !loading && (
            <div className="screen-error">
              <div className="screen-error-text">{error}</div>
            </div>
          )}
          {!loading && !error && filtered.length === 0 && (
            <div className="tasks-empty">
              <div className="tasks-empty-title">ログはありません</div>
            </div>
          )}
          {!loading && !error &&
            filtered.map((l) => (
              <LogEntryRow key={`${l.timestamp}-${l.intent}`} log={l} />
            ))}
        </div>
      </div>
    </section>
  );
}
