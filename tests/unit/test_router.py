from backend.core.intent.rules import IntentType
from backend.llm.router import RouteTarget, route


def test_chat_routes_local():
    assert route(IntentType.CHAT) == RouteTarget.LOCAL


def test_task_list_routes_rule_based():
    assert route(IntentType.TASK_LIST) == RouteTarget.RULE_BASED


def test_reminder_add_routes_rule_based():
    assert route(IntentType.REMINDER_ADD) == RouteTarget.RULE_BASED


def test_briefing_routes_local():
    assert route(IntentType.BRIEFING) == RouteTarget.LOCAL
