"""Candidate selection for the existing board-locked Kanban dispatcher.

Selection does not claim, promote, reclaim, or spawn tasks; the dispatcher remains
responsible for those transitions and their concurrency/dependency gates.
"""
from __future__ import annotations

import re
import sqlite3
from typing import Optional


def validate_task_id(task_id: Optional[str]) -> None:
    if task_id is not None and not re.fullmatch(r"t_[A-Za-z0-9_-]{1,128}", task_id):
        raise ValueError("invalid dispatch task_id")


def lane_rows(conn: sqlite3.Connection, status: str, task_id: Optional[str] = None) -> list[sqlite3.Row]:
    """Unclaimed rows of one lane in dispatch order."""
    return conn.execute(
        "SELECT id, assignee FROM tasks "
        "WHERE status = ? AND claim_lock IS NULL "
        "AND (? IS NULL OR id = ?) ORDER BY priority DESC, created_at ASC",
        (status, task_id, task_id)
    ).fetchall()


def resolve_default_assignee(default_assignee: Optional[str]) -> Optional[str]:
    """``kanban.default_assignee`` when it names a real profile this home may
    claim (``kanban.dispatch_profiles`` gated, same predicate as the spawn
    gate). Otherwise ``None`` so an unassigned shared-board card is never
    written to. When the profiles module isn't importable trust the
    operator's config: the downstream check still buckets a missing profile
    as nonspawnable."""
    from hermes_cli import kanban_db_dispatch as dispatcher

    name = (default_assignee or "").strip() or None
    if name:
        profile_exists = dispatcher._profile_exists_fn()
        if profile_exists is not None and not profile_exists(name):
            return None
    return name
