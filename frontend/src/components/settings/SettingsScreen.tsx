"use client";

import { useState } from "react";
import type { ConfirmHandle } from "@/types";

function SettingsSection({
  title,
  desc,
  danger,
  children,
}: {
  title: string;
  desc?: string;
  danger?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className={`st-section${danger ? " is-danger" : ""}`}>
      <div className="st-section-head">
        <h2 className="st-section-title">{title}</h2>
        {desc && <p className="st-section-desc">{desc}</p>}
      </div>
      <div className="st-section-body">{children}</div>
    </div>
  );
}

function SettingsRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="st-row">
      <div className="st-row-label">{label}</div>
      <div className="st-row-control">{children}</div>
    </div>
  );
}

function RadioGroup({
  name,
  value,
  options,
  onChange,
}: {
  name: string;
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (v: string) => void;
}) {
  return (
    <div className="st-radio-group">
      {options.map((o) => (
        <label
          key={o.value}
          className={`st-radio${value === o.value ? " is-active" : ""}`}
        >
          <input
            type="radio"
            name={name}
            value={o.value}
            checked={value === o.value}
            onChange={() => onChange(o.value)}
          />
          {o.label}
        </label>
      ))}
    </div>
  );
}

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="toggle">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span className="toggle-track">
        <span className="toggle-thumb" />
      </span>
    </label>
  );
}

interface Props {
  confirm: ConfirmHandle;
}

export default function SettingsScreen({ confirm }: Props) {
  const [llm, setLLM] = useState({
    provider: "openai",
    model: "gpt-4o-mini",
    apiKey: "",
    showKey: false,
  });
  const [persona, setPersona] = useState({
    tone: "polite",
    verbosity: "normal",
    emoji: false,
  });
  const [notify, setNotify] = useState({
    method: "terminal",
    briefingAM: "08:00",
    briefingPM: "21:00",
    sound: false,
  });

  const handleReset = () =>
    confirm.open({
      title: "すべてのデータをリセットしますか？",
      description:
        "タスク・リマインダー・メモ・操作ログがローカルから完全に削除されます。設定は維持されます。",
      details: [
        {
          label: "対象",
          value: "tasks, reminders, notes, logs",
          mono: true,
        },
        { label: "DB", value: "data/db/assistant.db", mono: true },
      ],
      warning: "この操作は取り消せません。バックアップを先に取ることを推奨します。",
      actionLabel: "リセットする",
      destructive: true,
      onConfirm: () => {},
    });

  return (
    <section className="screen">
      <header className="screen-head">
        <div className="head-left">
          <h1 className="head-title">設定</h1>
        </div>
      </header>

      <div className="settings-scroll">
        <div className="settings-inner">
          {/* LLM */}
          <SettingsSection
            title="LLM 設定"
            desc="使用する言語モデルの接続先を管理します。"
          >
            <SettingsRow label="プロバイダ">
              <select
                className="st-select"
                value={llm.provider}
                onChange={(e) =>
                  setLLM((s) => ({ ...s, provider: e.target.value }))
                }
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="local">ローカル (Ollama)</option>
              </select>
            </SettingsRow>
            <SettingsRow label="モデル名">
              <input
                className="st-input"
                value={llm.model}
                onChange={(e) =>
                  setLLM((s) => ({ ...s, model: e.target.value }))
                }
                placeholder="例: gpt-4o-mini"
              />
            </SettingsRow>
            <SettingsRow label="API キー">
              <div className="st-key-wrap">
                <input
                  className="st-input st-input-mono"
                  type={llm.showKey ? "text" : "password"}
                  value={llm.apiKey}
                  onChange={(e) =>
                    setLLM((s) => ({ ...s, apiKey: e.target.value }))
                  }
                  placeholder="sk-…"
                />
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() =>
                    setLLM((s) => ({ ...s, showKey: !s.showKey }))
                  }
                >
                  {llm.showKey ? "隠す" : "表示"}
                </button>
              </div>
            </SettingsRow>
          </SettingsSection>

          {/* Persona */}
          <SettingsSection
            title="口調設定"
            desc="Atelier の応答スタイルを調整します。persona.yaml に反映されます。"
          >
            <SettingsRow label="トーン">
              <RadioGroup
                name="tone"
                value={persona.tone}
                options={[
                  { value: "polite", label: "丁寧" },
                  { value: "casual", label: "カジュアル" },
                  { value: "terse",  label: "簡潔" },
                ]}
                onChange={(v) => setPersona((s) => ({ ...s, tone: v }))}
              />
            </SettingsRow>
            <SettingsRow label="冗長さ">
              <RadioGroup
                name="verbosity"
                value={persona.verbosity}
                options={[
                  { value: "brief",   label: "短め" },
                  { value: "normal",  label: "標準" },
                  { value: "verbose", label: "詳しめ" },
                ]}
                onChange={(v) => setPersona((s) => ({ ...s, verbosity: v }))}
              />
            </SettingsRow>
            <SettingsRow label="絵文字を使用">
              <Toggle
                checked={persona.emoji}
                onChange={(v) => setPersona((s) => ({ ...s, emoji: v }))}
              />
            </SettingsRow>
          </SettingsSection>

          {/* Notifications */}
          <SettingsSection
            title="通知設定"
            desc="リマインダーやブリーフィングの通知方法を設定します。"
          >
            <SettingsRow label="通知方式">
              <select
                className="st-select"
                value={notify.method}
                onChange={(e) =>
                  setNotify((s) => ({ ...s, method: e.target.value }))
                }
              >
                <option value="os">OS 通知</option>
                <option value="terminal">ターミナル</option>
                <option value="none">オフ</option>
              </select>
            </SettingsRow>
            <SettingsRow label="朝ブリーフィング">
              <input
                className="st-input st-input-mono st-input-sm"
                type="time"
                value={notify.briefingAM}
                onChange={(e) =>
                  setNotify((s) => ({ ...s, briefingAM: e.target.value }))
                }
              />
            </SettingsRow>
            <SettingsRow label="夜ブリーフィング">
              <input
                className="st-input st-input-mono st-input-sm"
                type="time"
                value={notify.briefingPM}
                onChange={(e) =>
                  setNotify((s) => ({ ...s, briefingPM: e.target.value }))
                }
              />
            </SettingsRow>
            <SettingsRow label="効果音">
              <Toggle
                checked={notify.sound}
                onChange={(v) => setNotify((s) => ({ ...s, sound: v }))}
              />
            </SettingsRow>
          </SettingsSection>

          {/* Storage */}
          <SettingsSection
            title="ストレージ"
            desc="データの保存先を確認できます。変更は設定ファイルから行ってください。"
          >
            <SettingsRow label="DB パス">
              <div className="st-value mono">data/db/assistant.db</div>
            </SettingsRow>
            <SettingsRow label="ログパス">
              <div className="st-value mono">data/logs/operations.jsonl</div>
            </SettingsRow>
          </SettingsSection>

          {/* Danger */}
          <SettingsSection title="危険な操作" danger>
            <div className="st-danger-row">
              <div className="st-danger-text">
                <div className="st-danger-title">データリセット</div>
                <div className="st-danger-desc">
                  すべてのタスク・リマインダー・メモ・ログを削除します。設定は維持されます。
                </div>
              </div>
              <button
                type="button"
                className="btn btn-danger btn-md"
                onClick={handleReset}
              >
                リセット
              </button>
            </div>
          </SettingsSection>
        </div>
      </div>
    </section>
  );
}
