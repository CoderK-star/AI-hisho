"""ルールベースの記憶重要度スコアリング。

スコア構成 (0.0〜1.0):
  base          : source に応じた基底スコア
                    user_pinned  = 1.0（ユーザが明示的にピン留め）
                    auto_summary = 0.5
  recency_bonus : 作成から7日以内は +0.2、7〜30日は線形に減衰 (+0.2→0)
  staleness     : auto_summary が30日超経過した場合のペナルティ (-0.01/日、上限 -0.3)

例 (auto_summary の典型的な推移):
  day  0: 0.5 + 0.20 = 0.70
  day  7: 0.5 + 0.00 = 0.50
  day 30: 0.5 + 0.00 = 0.50
  day 50: 0.5 - 0.20 = 0.30  ← アーカイブ閾値
  day 60: 0.5 - 0.30 = 0.20  ← アーカイブ対象
"""
from __future__ import annotations

from datetime import datetime


def compute_importance_score(
    source: str,
    created_at: datetime,
    access_count: int,
    last_accessed_at: datetime | None,
    now: datetime | None = None,
) -> float:
    """記憶エントリの重要度スコアを計算する。

    Args:
        source: "user_pinned" | "auto_summary"
        created_at: 作成日時
        access_count: これまでのアクセス回数
        last_accessed_at: 最終アクセス日時（未アクセスなら None）
        now: 現在時刻（テスト用に注入可能、省略時は datetime.now()）

    Returns:
        0.0〜1.0 のスコア（値が大きいほど重要）
    """
    if now is None:
        now = datetime.now()

    # 基底スコア
    base = 1.0 if source == "user_pinned" else 0.5

    days_since_created = max(0, (now - created_at).days)

    # 新鮮さボーナス: 7日以内 +0.2、7〜30日で線形減衰
    if days_since_created <= 7:
        recency_bonus = 0.2
    elif days_since_created <= 30:
        recency_bonus = 0.2 * (1.0 - (days_since_created - 7) / 23.0)
    else:
        recency_bonus = 0.0

    # アクセス頻度ボーナス: +0.05/回、上限 +0.2
    access_bonus = min(0.2, access_count * 0.05)

    # 陳腐化ペナルティ: auto_summary が30日超で -0.01/日、上限 -0.3
    staleness_penalty = 0.0
    if source == "auto_summary" and days_since_created > 30:
        staleness_penalty = min(0.3, (days_since_created - 30) * 0.01)

    total = base + recency_bonus + access_bonus - staleness_penalty
    return round(min(1.0, max(0.0, total)), 4)


def initial_score(source: str) -> float:
    """作成直後の初期スコア（作成日時 = now として計算）。"""
    return compute_importance_score(
        source=source,
        created_at=datetime.now(),
        access_count=0,
        last_accessed_at=None,
    )
