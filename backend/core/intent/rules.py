from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class IntentType(str, Enum):
    CHAT = "chat"
    TASK_ADD = "task_add"
    TASK_LIST = "task_list"
    TASK_UPDATE = "task_update"
    REMINDER_ADD = "reminder_add"
    REMINDER_LIST = "reminder_list"
    MEMO_ADD = "memo_add"
    MEMO_LIST = "memo_list"
    SCHEDULE_CHECK = "schedule_check"
    BRIEFING = "briefing"
    MEMORY_PIN = "memory_pin"
    KNOWLEDGE_SEARCH = "knowledge_search"
    SCHEDULE_CHECK_CALENDAR = "schedule_check_calendar"
    HELP = "help"


@dataclass(frozen=True)
class IntentRule:
    intent: IntentType
    patterns: list[re.Pattern[str]]
    priority: int = 0


_RULES: list[IntentRule] = [
    IntentRule(
        IntentType.TASK_ADD,
        [re.compile(r"タスク.*(追加|登録|作成|入れ)", re.IGNORECASE),
         re.compile(r"(やること|TODO).*(追加|登録|作って)", re.IGNORECASE),
         re.compile(r"add\s+task", re.IGNORECASE)],
        priority=10,
    ),
    IntentRule(
        IntentType.TASK_LIST,
        [re.compile(r"タスク.*(一覧|リスト|確認|見せ|教え)", re.IGNORECASE),
         re.compile(r"(やること|TODO).*(一覧|確認|見せ|教え)", re.IGNORECASE),
         re.compile(r"(list|show)\s+tasks?", re.IGNORECASE)],
        priority=10,
    ),
    IntentRule(
        IntentType.TASK_UPDATE,
        [re.compile(r"タスク.*(完了|終わ|済み|キャンセル|更新|変更)", re.IGNORECASE),
         re.compile(r"(done|complete|finish)\s+task", re.IGNORECASE)],
        priority=10,
    ),
    IntentRule(
        IntentType.REMINDER_ADD,
        [re.compile(r"リマインダ.*(追加|登録|設定|セット)", re.IGNORECASE),
         re.compile(r"(思い出させ|忘れない|通知して|教えて).*(時|分|後|まで)", re.IGNORECASE),
         re.compile(r"remind\s+me", re.IGNORECASE)],
        priority=10,
    ),
    IntentRule(
        IntentType.REMINDER_LIST,
        [re.compile(r"リマインダ.*(一覧|リスト|確認|見せ)", re.IGNORECASE),
         re.compile(r"(list|show)\s+reminders?", re.IGNORECASE)],
        priority=10,
    ),
    IntentRule(
        IntentType.MEMO_ADD,
        [re.compile(r"メモ.*(追加|登録|作成|保存|書い)", re.IGNORECASE),
         re.compile(r"(覚えておいて|記録して|メモして)", re.IGNORECASE),
         re.compile(r"(save|add)\s+(memo|note)", re.IGNORECASE)],
        priority=10,
    ),
    IntentRule(
        IntentType.MEMO_LIST,
        [re.compile(r"メモ.*(一覧|リスト|確認|見せ)", re.IGNORECASE),
         re.compile(r"(list|show)\s+(memos?|notes?)", re.IGNORECASE)],
        priority=10,
    ),
    IntentRule(
        IntentType.SCHEDULE_CHECK,
        [re.compile(r"(予定|スケジュール).*(確認|教え|見せ|今日|明日)", re.IGNORECASE),
         re.compile(r"(today|tomorrow).*schedule", re.IGNORECASE)],
        priority=10,
    ),
    IntentRule(
        IntentType.BRIEFING,
        [re.compile(r"ブリーフィング", re.IGNORECASE),
         re.compile(r"(今日|朝|夜)の(まとめ|サマリ|報告)", re.IGNORECASE),
         re.compile(r"briefing", re.IGNORECASE)],
        priority=10,
    ),
    IntentRule(
        IntentType.MEMORY_PIN,
        [re.compile(r"覚えておいて", re.IGNORECASE),
         re.compile(r"(remember|pin)\s+this", re.IGNORECASE)],
        priority=5,
    ),
    IntentRule(
        IntentType.KNOWLEDGE_SEARCH,
        [re.compile(r"(メモ|記録|ノート).*(検索|探|見つけ|調べ)", re.IGNORECASE),
         re.compile(r"(検索|探|調べ).*(メモ|記録|ノート)", re.IGNORECASE),
         re.compile(r"〜?について.*(メモ|記録|書い).*?(あ|教え|見せ)", re.IGNORECASE),
         re.compile(r"(search|find|look\s*up).*(note|memo|record)", re.IGNORECASE)],
        priority=12,
    ),
    IntentRule(
        IntentType.SCHEDULE_CHECK_CALENDAR,
        [re.compile(r"(カレンダー|calendar).*(確認|教え|見せ|今日|明日|今週)", re.IGNORECASE),
         re.compile(r"(今日|明日|今週|来週)の(予定|スケジュール|イベント)", re.IGNORECASE),
         re.compile(r"(予定|スケジュール).*(カレンダー|google)", re.IGNORECASE)],
        priority=12,
    ),
    IntentRule(
        IntentType.HELP,
        [re.compile(r"^(ヘルプ|help|使い方|できること)$", re.IGNORECASE)],
        priority=5,
    ),
]


def get_rules() -> list[IntentRule]:
    return _RULES
