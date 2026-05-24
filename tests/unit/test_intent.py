from backend.core.intent.classifier import classify
from backend.core.intent.rules import IntentType


def test_task_add_ja():
    result = classify("タスクを追加して")
    assert result.intent == IntentType.TASK_ADD


def test_task_list_ja():
    result = classify("タスクの一覧を見せて")
    assert result.intent == IntentType.TASK_LIST


def test_reminder_add_ja():
    result = classify("リマインダーを設定して")
    assert result.intent == IntentType.REMINDER_ADD


def test_memo_add_ja():
    result = classify("メモを保存して")
    assert result.intent == IntentType.MEMO_ADD


def test_briefing():
    result = classify("ブリーフィング")
    assert result.intent == IntentType.BRIEFING


def test_chat_fallback():
    result = classify("こんにちは")
    assert result.intent == IntentType.CHAT


def test_task_add_en():
    result = classify("add task buy groceries")
    assert result.intent == IntentType.TASK_ADD


def test_help():
    result = classify("ヘルプ")
    assert result.intent == IntentType.HELP
