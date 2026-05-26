"""Memory 重要度スコアリングのユニットテスト。"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from backend.core.memory.scorer import compute_importance_score, initial_score


def _days_ago(n: int) -> datetime:
    return datetime.now() - timedelta(days=n)


# ── initial_score ────────────────────────────────────────────────────────────

def test_initial_score_user_pinned():
    score = initial_score("user_pinned")
    assert score == 1.0


def test_initial_score_auto_summary():
    score = initial_score("auto_summary")
    # 作成直後: base(0.5) + recency(0.2) = 0.7
    assert score == pytest.approx(0.7, abs=0.01)


# ── user_pinned は常に 1.0 ────────────────────────────────────────────────────

def test_user_pinned_stays_high_when_old():
    score = compute_importance_score(
        source="user_pinned",
        created_at=_days_ago(365),
        access_count=0,
        last_accessed_at=None,
    )
    assert score == 1.0


# ── recency_bonus の減衰 ─────────────────────────────────────────────────────

def test_recency_bonus_within_7_days():
    score = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(3),
        access_count=0,
        last_accessed_at=None,
    )
    # base(0.5) + recency(0.2) = 0.7
    assert score == pytest.approx(0.7, abs=0.01)


def test_recency_bonus_at_day_7():
    score = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(7),
        access_count=0,
        last_accessed_at=None,
    )
    assert score == pytest.approx(0.7, abs=0.01)


def test_recency_bonus_decays_after_7_days():
    score_7 = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(7),
        access_count=0,
        last_accessed_at=None,
    )
    score_20 = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(20),
        access_count=0,
        last_accessed_at=None,
    )
    assert score_20 < score_7


def test_recency_bonus_gone_at_day_30():
    score = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(30),
        access_count=0,
        last_accessed_at=None,
    )
    # base(0.5) + recency(0) = 0.5
    assert score == pytest.approx(0.5, abs=0.01)


# ── staleness_penalty ────────────────────────────────────────────────────────

def test_staleness_starts_at_day_31():
    score_30 = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(30),
        access_count=0,
        last_accessed_at=None,
    )
    score_31 = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(31),
        access_count=0,
        last_accessed_at=None,
    )
    assert score_31 < score_30


def test_staleness_reaches_archive_threshold():
    # day 50: base(0.5) - staleness(0.20) = 0.30
    score = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(50),
        access_count=0,
        last_accessed_at=None,
    )
    assert score == pytest.approx(0.3, abs=0.01)


def test_staleness_capped_at_0_3():
    # day 100: staleness = min(0.3, 0.7) = 0.3 → score = 0.2
    score = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(100),
        access_count=0,
        last_accessed_at=None,
    )
    assert score == pytest.approx(0.2, abs=0.01)


# ── access_bonus ─────────────────────────────────────────────────────────────

def test_access_bonus_increases_score():
    base_score = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(40),
        access_count=0,
        last_accessed_at=None,
    )
    accessed_score = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(40),
        access_count=4,
        last_accessed_at=None,
    )
    assert accessed_score > base_score
    assert accessed_score == pytest.approx(base_score + 0.2, abs=0.01)


def test_access_bonus_capped_at_0_2():
    score_4 = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(40),
        access_count=4,
        last_accessed_at=None,
    )
    score_10 = compute_importance_score(
        source="auto_summary",
        created_at=_days_ago(40),
        access_count=10,
        last_accessed_at=None,
    )
    assert score_4 == score_10


# ── スコアは常に 0.0〜1.0 の範囲 ─────────────────────────────────────────────

@pytest.mark.parametrize("days,access_count,source", [
    (0, 0, "auto_summary"),
    (0, 10, "user_pinned"),
    (365, 0, "auto_summary"),
    (365, 100, "auto_summary"),
    (365, 0, "user_pinned"),
])
def test_score_range(days, access_count, source):
    score = compute_importance_score(
        source=source,
        created_at=_days_ago(days),
        access_count=access_count,
        last_accessed_at=None,
    )
    assert 0.0 <= score <= 1.0
