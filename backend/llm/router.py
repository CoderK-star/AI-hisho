from __future__ import annotations

import logging
from enum import Enum

from backend.core.intent.rules import IntentType

logger = logging.getLogger(__name__)


class RouteTarget(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    RULE_BASED = "rule_based"
    HITL = "hitl"


_ROUTE_TABLE: dict[IntentType, RouteTarget] = {
    IntentType.CHAT: RouteTarget.LOCAL,
    IntentType.TASK_ADD: RouteTarget.LOCAL,
    IntentType.TASK_LIST: RouteTarget.RULE_BASED,
    IntentType.TASK_UPDATE: RouteTarget.LOCAL,
    IntentType.REMINDER_ADD: RouteTarget.RULE_BASED,
    IntentType.REMINDER_LIST: RouteTarget.RULE_BASED,
    IntentType.MEMO_ADD: RouteTarget.LOCAL,
    IntentType.MEMO_LIST: RouteTarget.RULE_BASED,
    IntentType.SCHEDULE_CHECK: RouteTarget.RULE_BASED,
    IntentType.BRIEFING: RouteTarget.LOCAL,
    IntentType.MEMORY_PIN: RouteTarget.LOCAL,
    IntentType.KNOWLEDGE_SEARCH: RouteTarget.LOCAL,
    IntentType.SCHEDULE_CHECK_CALENDAR: RouteTarget.RULE_BASED,
    IntentType.HELP: RouteTarget.RULE_BASED,
}


def route(intent: IntentType) -> RouteTarget:
    target = _ROUTE_TABLE.get(intent, RouteTarget.LOCAL)
    logger.debug("Routing intent=%s -> %s", intent, target)
    return target
