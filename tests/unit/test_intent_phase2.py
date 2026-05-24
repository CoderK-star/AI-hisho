from backend.core.intent.classifier import classify
from backend.core.intent.rules import IntentType


def test_knowledge_search_ja():
    assert classify("メモを検索して").intent == IntentType.KNOWLEDGE_SEARCH


def test_knowledge_search_ja2():
    assert classify("記録を探して").intent == IntentType.KNOWLEDGE_SEARCH


def test_schedule_check_calendar_ja():
    assert classify("今日の予定をカレンダーで確認して").intent == IntentType.SCHEDULE_CHECK_CALENDAR


def test_schedule_check_calendar_ja2():
    assert classify("今週のスケジュールを見せて").intent == IntentType.SCHEDULE_CHECK_CALENDAR


def test_knowledge_search_priority_over_memo_list():
    # "メモを検索" は memo_list より knowledge_search が優先（priority 12 > 10）
    result = classify("メモを検索してください")
    assert result.intent == IntentType.KNOWLEDGE_SEARCH
