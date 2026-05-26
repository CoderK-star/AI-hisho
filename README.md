# AI秘書 — Personal Assistant Workflow System

単一ユーザ向けの呼び出し型AI秘書システム。

- **受動モード中心**: 普段は待機、呼び出された時だけ起動
- **Human-in-the-loop**: 高リスク操作は必ずユーザ確認を挟む
- **ローカルファースト**: 個人情報はできる限りローカル処理
- **キャラクター性は出力整形層のみ**: 推論層に人格プロンプトを混ぜない

---

## 必要環境

- Python 3.10+
- [Ollama](https://ollama.com/) (ローカルLLM使用時)

オプション機能:
- RAG: `pip install -e ".[rag]"` — qdrant-client + fastembed
- カレンダー連携: `pip install -e ".[calendar]"` — Google Calendar API
- 音声入出力 (STT/TTS): `pip install -e ".[voice]"` — faster-whisper + sounddevice
- STT のみ: `pip install -e ".[stt]"` — faster-whisper
- ウェイクワード常駐: `pip install -e ".[wakeword]"` — openwakeword + sounddevice

仮想環境の使用を推奨します（例: `python -m venv .venv`）。
.\venv\Scripts\activate  # Windows
---

## セットアップ

```bash
# 依存インストール（基本）
pip install -e ".[dev]"

# RAG を使う場合
pip install -e ".[dev,rag]"

# Google Calendar 連携を使う場合
pip install -e ".[dev,calendar]"

# 音声入出力 (STT/TTS) を使う場合
pip install -e ".[dev,voice]"

# ウェイクワード常駐を使う場合
pip install -e ".[dev,voice,wakeword]"

# 環境変数の設定
cp .env.example .env
# .env を編集して OPENAI_API_KEY や OLLAMA_MODEL などを設定

# サーバー起動
uvicorn backend.main:app --reload --port 8000
```

`.env` を設定しない場合、LLMはMockプロバイダで動作します（テスト・動作確認用）。

---

## API

ベースURL: `http://localhost:8000`

### ヘルスチェック

```
GET /health
→ {"status": "ok"}
```

### チャット

```
POST /api/chat
{
  "message": "タスクの一覧を見せて",
  "session_id": "任意のセッションID（省略可）"
}

→ {
  "reply": "...",
  "intent": "task_list",
  "session_id": "...",
  "tools_called": ["internal.tasks.list"]
}
```

チャットは Intent を自動判定し、ルールベースで処理先を振り分けます。

| 入力例 | Intent | 処理先 |
|---|---|---|
| 「タスクを追加して」 | `task_add` | ローカルLLM |
| 「タスクの一覧を見せて」 | `task_list` | ルールベース |
| 「ブリーフィング」 | `briefing` | ローカルLLM |
| 「今日の予定をカレンダーで確認して」 | `schedule_check_calendar` | ローカルLLM |
| 「メモを検索して」 | `knowledge_search` | ローカルLLM + RAG |
| 「こんにちは」 | `chat` | ローカルLLM |

### タスク

```
POST   /api/tasks              # タスク作成
GET    /api/tasks?status=todo  # タスク一覧 (status: todo|in_progress|done|cancelled)
PATCH  /api/tasks/{id}         # タスク更新
```

**タスク作成リクエスト:**
```json
{
  "title": "週次レポート作成",
  "description": "任意",
  "priority": "high",
  "due_date": "2026-06-01T18:00:00"
}
```

### リマインダー

```
POST  /api/reminders                       # リマインダー作成
GET   /api/reminders?include_fired=false   # リマインダー一覧
```

**リマインダー作成リクエスト:**
```json
{
  "message": "ミーティングの準備",
  "remind_at": "2026-05-25T09:30:00"
}
```

リマインダーはサーバー起動中、1分毎に期限チェックを行い、通知を送信します。

### メモ

```
POST  /api/memos        # メモ作成（RAG有効時は自動インデックス）
GET   /api/memos        # メモ一覧
GET   /api/memos/{id}   # メモ詳細
```

### ナレッジ検索 (RAG)

RAG が有効な場合のみ利用可能（`config/settings.yaml` の `rag.enabled: true`）。

```
GET /api/search?q=プロジェクトX&limit=5
→ {
  "query": "プロジェクトX",
  "count": 2,
  "results": [
    {"score": 0.92, "type": "memo", "doc_id": "...", "text": "..."},
    ...
  ]
}
```

チャットで「メモを検索して」と入力すると、RAG 検索結果をコンテキストとして LLM が回答を生成します。

### カレンダー (Google Calendar)

カレンダー連携が有効な場合のみ利用可能（`config/settings.yaml` の `calendar.enabled: true`）。

```
GET /api/calendar/events?days=7   # 今後 N 日分のイベント取得
GET /api/calendar/health          # 認証状態の確認
```

**初回認証手順:**
1. Google Cloud Console で OAuth2 クライアント ID を作成
2. `credentials.json` を `data/calendar_credentials.json` に配置
3. サーバー起動後、`/api/calendar/health` にアクセスしてブラウザ認証を完了

### 音声 API (Phase 4)

音声 API は `pip install -e '.[voice]'` 後に利用可能です。

```
POST /api/voice/transcribe
  Content-Type: multipart/form-data
  file: <音声ファイル (wav/mp3/m4a/ogg)>
→ {"text": "認識されたテキスト", "filename": "..."}

POST /api/voice/chat
  Content-Type: multipart/form-data
  file: <音声ファイル>
  session_id: <省略可>
→ {"reply": "...", "intent": "...", "session_id": "...", "tools_called": [...]}

POST /api/voice/speak
  Content-Type: multipart/form-data
  text: <読み上げるテキスト>
→ audio/wav バイナリ

POST /api/voice/chat-spoken
  Content-Type: multipart/form-data
  file: <音声ファイル>
  session_id: <省略可>
→ audio/wav バイナリ (ヘッダに X-Reply-Text, X-Session-Id)
```

**STT 設定 (`config/settings.yaml`):**
```yaml
stt:
  enabled: true
  model: base       # tiny | base | small | medium | large
  language: ja      # ja | auto
  device: cpu       # cpu | cuda

tts:
  enabled: true
  provider: voicevox  # voicevox | openai | mock
  voicevox:
    url: http://localhost:50021
    speaker_id: 1
```

**ウェイクワード常駐 (`pip install -e '.[wakeword]'` 後):**
```yaml
voice:
  notification_speech: true   # リマインダー通知を音声読み上げ
  wakeword:
    enabled: true
    keyword: hey_assistant    # openwakeword のキーワード識別子
    sensitivity: 0.5
```

ウェイクワード検出 → STT → チャット → TTS の一連の流れがサーバー起動中バックグラウンドで動作します。

### 操作ログ GUI

```
GET /api/logs               # 操作ログ一覧 (JSON)
GET /api/logs?intent=chat   # Intent でフィルタ
GET /api/logs/view          # ブラウザ GUI ビューア
```

ブラウザで `http://localhost:8000/api/logs/view` を開くと、Intent・Route・サマリをフィルタ・ページングできるログビューアが表示されます。

---

## 設定

### `config/settings.yaml`

```yaml
llm:
  default_provider: ollama       # ollama | openai
  local_fallback: notify         # cloud | fail | notify
  allow_cloud_escalation: false

notification:
  method: terminal               # terminal | os

scheduler:
  briefing:
    enabled: true
    morning: "08:00"
    evening: "21:00"
    timezone: "Asia/Tokyo"

rag:
  enabled: false                 # pip install -e '.[rag]' 後に true へ
  mode: local                    # local | server
  local_path: data/rag
  collection: personal_assistant
  embedding_model: intfloat/multilingual-e5-small
  top_k: 5

calendar:
  enabled: false                 # pip install -e '.[calendar]' 後に true へ
  credentials_path: data/calendar_credentials.json
  token_path: data/calendar_token.json
```

`local_fallback`:
- `notify` (デフォルト): ローカルLLM失敗時にエラーメッセージを返す
- `cloud`: 自動でクラウドAPIに切り替え（`allow_cloud_escalation: true` 必須）
- `fail`: エラーをそのまま返す

### `config/persona.yaml`

口調・出力スタイルのみ定義します。推論には一切影響しません。

```yaml
style:
  tone: polite
  suffix: "です・ます"
```

### 環境変数 (`.env`)

```
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
NOTIFICATION_METHOD=terminal
DATABASE_URL=sqlite+aiosqlite:///./data/db/assistant.db
QDRANT_URL=http://localhost:6333   # RAG サーバーモード使用時のみ
```

---

## アーキテクチャ

```
入力テキスト
    ↓
[1] Intent 分類 (ルールベース正規表現)
    ↓
[2] Context Engine (Intent に応じた最小コンテキストロード)
    ↓
[3] Memory Engine (会話履歴参照)
    ↓
[4] Workflow Engine (内部ツール / 外部アダプタ実行)
    ├─→ internal/   DB直結・ネットワーク不要 (tasks, reminders, memos)
    ├─→ rag/        ベクトル検索 (qdrant-client + fastembed)
    └─→ adapters/   外部API (Google Calendar など)
    ↓
[5] LLM Router (ルールベース振り分け)
    ├─→ ローカルLLM (Ollama)     軽量処理・プライバシー優先
    ├─→ クラウドAPI (OpenAI)     複雑な推論・長文処理
    └─→ ルールベース実行         リスト表示など LLM 不要な処理
    ↓
[6] 出力整形 (persona.yaml による口調付与)
    ↓
応答テキスト / 操作ログ
```

**設計上の制約:**
- LLM Router の判断にLLMを使わない（ルールベースを維持）
- `persona.yaml` の内容を推論プロンプトに混ぜない
- 内部ツール (`internal/`) と外部アダプタ (`adapters/`) を分離する

---

## テスト

```bash
# 全テスト
pytest

# ユニットテストのみ
pytest tests/unit/ -v

# 統合テストのみ
pytest tests/integration/ -v

# カバレッジ付き
pytest --cov=backend tests/
```

RAG テスト (`tests/unit/test_rag_engine.py`) は `qdrant-client[fastembed]` がインストールされていない場合は自動スキップされます。

---

## 操作ログ

すべての操作は `data/logs/operations.jsonl` に追記されます（削除・上書き不可）。  
`http://localhost:8000/api/logs/view` でブラウザから確認できます。

```jsonc
{
  "timestamp": "2026-05-24T10:00:00+09:00",
  "session_id": "...",
  "intent": "task_add",
  "input_summary": "タスクを追加",
  "llm_route": "local",
  "cloud_escalated": false,
  "tools_called": ["internal.tasks.add"],
  "external_apis_called": [],
  "result": "success",
  "requires_confirmation": false
}
```

---

## ロードマップ

| フェーズ | 内容 | 状態 |
|---|---|---|
| Phase 1 | チャット / タスク / リマインダー / メモ / ブリーフィング | ✅ 完了 |
| Phase 2 | RAG / Google Calendar 連携 / 操作ログ GUI | ✅ 完了 |
| Phase 3 | メール要約 / 外部アダプタ拡充 / Memory 重要度判定の改良 | ✅ 完了 |
| Phase 4 | 音声常駐 / ウェイクワード / 通知音声割り込み (オプション) | ✅ 完了 |
| Phase 5 | スマートホーム連携 / GUI 整備 / OSS 化準備 | 未着手 |
