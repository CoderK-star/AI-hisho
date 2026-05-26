"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Icons } from "../icons";
import { api } from "@/lib/api";
import type { ChatMessage, ConfirmHandle } from "@/types";

function nowHHMM(): string {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function ConfirmCard({ data }: { data: NonNullable<ChatMessage["confirmCard"]> }) {
  const label =
    data.kind === "task-added"
      ? "タスクを追加しました"
      : data.kind === "reminder-added"
      ? "リマインダーを設定しました"
      : "メモを作成しました";
  return (
    <div className="confirm">
      <div className="confirm-left">
        <span className="confirm-tick">{Icons.check}</span>
        <div className="confirm-text">
          <div className="confirm-label">{label}</div>
          <div className="confirm-title">{data.title}</div>
          {data.meta && <div className="confirm-meta">{data.meta}</div>}
        </div>
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

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`msg ${isUser ? "msg-user" : "msg-ai"}`}>
      <div className="msg-meta">
        <span className="msg-role">{isUser ? "あなた" : "Atelier"}</span>
        <span className="msg-time is-mono">{msg.time}</span>
      </div>
      <div className="msg-body">
        {msg.text.split("\n").map((line, i) => (
          <p key={i}>{line}</p>
        ))}
        {msg.confirmCard && <ConfirmCard data={msg.confirmCard} />}
      </div>
    </div>
  );
}

function inferConfirmCard(
  tools: string[],
  reply: string
): ChatMessage["confirmCard"] | undefined {
  if (tools.includes("internal.tasks.add")) {
    const titleMatch = reply.match(/「(.+?)」/);
    return {
      kind: "task-added",
      title: titleMatch ? titleMatch[1] : "タスク",
      meta: "",
    };
  }
  if (tools.includes("internal.reminders.add")) {
    const titleMatch = reply.match(/「(.+?)」/);
    return {
      kind: "reminder-added",
      title: titleMatch ? titleMatch[1] : "リマインダー",
      meta: "",
    };
  }
  if (tools.includes("internal.notes.create") || tools.includes("internal.memos.add")) {
    return {
      kind: "memo-created",
      title: "メモ",
      meta: "",
    };
  }
  return undefined;
}

interface Props {
  confirm: ConfirmHandle;
}

export default function ChatScreen({ confirm: _confirm }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const scrollerRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    const el = scrollerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, sending]);

  const autoResize = useCallback(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 180) + "px";
  }, []);

  const send = useCallback(async () => {
    const text = draft.trim();
    if (!text || sending) return;

    const time = nowHHMM();
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      time,
      text,
    };
    setMessages((m) => [...m, userMsg]);
    setDraft("");
    setSending(true);
    setError(null);
    setTimeout(autoResize, 0);

    try {
      const res = await api.chat.send(text, sessionId);
      setSessionId(res.session_id);
      const aiMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        time: nowHHMM(),
        text: res.reply,
        toolsCalled: res.tools_called,
        confirmCard: inferConfirmCard(res.tools_called, res.reply),
      };
      setMessages((m) => [...m, aiMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "エラーが発生しました");
    } finally {
      setSending(false);
    }
  }, [draft, sending, sessionId, autoResize]);

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const dateLabel = new Date().toLocaleDateString("ja-JP", {
    month: "long",
    day: "numeric",
    weekday: "short",
  });

  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">チャット</h1>
          <span className="head-sub">本日 · {dateLabel}</span>
        </div>
        <div className="head-right">
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => {
              setMessages([]);
              setSessionId(undefined);
              setError(null);
            }}
          >
            <span className="btn-ico">{Icons.plus}</span>
            新しい会話
          </button>
        </div>
      </header>

      <div className="chat-scroll" ref={scrollerRef}>
        <div className="chat-inner">
          {messages.length === 0 && (
            <div className="day-divider"><span>会話を開始してください</span></div>
          )}
          {messages.length > 0 && (
            <div className="day-divider"><span>今日</span></div>
          )}
          {messages.map((m) => (
            <MessageBubble key={m.id} msg={m} />
          ))}
          {sending && <TypingIndicator />}
          {error && (
            <div className="msg msg-ai">
              <div className="msg-meta">
                <span className="msg-role" style={{ color: "var(--danger)" }}>エラー</span>
              </div>
              <div className="msg-body">
                <p style={{ color: "var(--danger)" }}>{error}</p>
              </div>
            </div>
          )}
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
              onChange={(e) => {
                setDraft(e.target.value);
                autoResize();
              }}
              onKeyDown={onKey}
            />
            <div className="composer-actions">
              <button
                type="button"
                className="icon-btn icon-btn-soft"
                title="音声入力（準備中）"
                disabled
              >
                {Icons.mic}
              </button>
              <button
                type="button"
                className={`send-btn${draft.trim() ? " is-ready" : ""}`}
                onClick={send}
                disabled={!draft.trim() || sending}
                title="送信 (Enter)"
              >
                {Icons.send}
              </button>
            </div>
          </div>
          <div className="composer-hint">
            <span className="hint-item">
              <span className="kbd">⏎</span>送信
            </span>
            <span className="hint-item">
              <span className="kbd">⇧⏎</span>改行
            </span>
            <span className="spacer" />
            <span className="hint-item muted">すべての操作はログに記録されます</span>
          </div>
        </div>
      </footer>
    </section>
  );
}
