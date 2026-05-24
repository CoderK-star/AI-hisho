from __future__ import annotations

from dataclasses import dataclass

from backend.core.intent.rules import IntentType, get_rules


@dataclass(frozen=True)
class ClassificationResult:
    intent: IntentType
    confidence: float
    matched_pattern: str | None = None


def classify(text: str) -> ClassificationResult:
    best: ClassificationResult | None = None
    best_priority = -1

    for rule in get_rules():
        for pattern in rule.patterns:
            m = pattern.search(text)
            if m and rule.priority >= best_priority:
                best = ClassificationResult(
                    intent=rule.intent,
                    confidence=0.9,
                    matched_pattern=pattern.pattern,
                )
                best_priority = rule.priority

    if best is not None:
        return best

    return ClassificationResult(intent=IntentType.CHAT, confidence=0.5)
