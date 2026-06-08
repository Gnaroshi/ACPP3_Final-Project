from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from rebootroute.config import load_config
from rebootroute.schemas import FeedbackEvent, OutcomeEvent, ProgressLog, ProgressStatus, to_plain_dict


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    cfg = load_config()
    path = db_path or cfg.database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS progress_logs (
                log_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                status TEXT NOT NULL,
                user_note TEXT,
                completed_at TEXT,
                points_awarded INTEGER NOT NULL DEFAULT 0,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_state (
                user_id TEXT PRIMARY KEY,
                reboot_points INTEGER NOT NULL DEFAULT 0,
                last_stage INTEGER,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback_events (
                event_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                mission_id TEXT,
                resource_id TEXT,
                recommended_stage INTEGER,
                burden_after INTEGER,
                appropriateness_rating INTEGER,
                risk_rating INTEGER,
                user_note TEXT,
                policy_version TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS outcome_events (
                outcome_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                outcome_type TEXT NOT NULL,
                outcome_status TEXT NOT NULL,
                mission_id TEXT,
                resource_id TEXT,
                readiness_rating INTEGER,
                burden_after INTEGER,
                result_note TEXT,
                operator_review_status TEXT,
                operator_note TEXT,
                evidence_url TEXT,
                policy_version TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def log_progress(progress: ProgressLog, db_path: Path | None = None) -> dict[str, Any]:
    init_db(db_path)
    payload = to_plain_dict(progress)
    points = progress.points_awarded if progress.status == ProgressStatus.completed else 0
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO progress_logs
            (log_id, user_id, mission_id, status, user_note, completed_at, points_awarded, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                progress.log_id,
                progress.user_id,
                progress.mission_id,
                progress.status.value if hasattr(progress.status, "value") else progress.status,
                progress.user_note,
                progress.completed_at.isoformat() if progress.completed_at else None,
                points,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        conn.execute(
            """
            INSERT INTO user_state (user_id, reboot_points)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                reboot_points = reboot_points + excluded.reboot_points,
                updated_at = CURRENT_TIMESTAMP
            """,
            (progress.user_id, points),
        )
        row = conn.execute("SELECT reboot_points FROM user_state WHERE user_id = ?", (progress.user_id,)).fetchone()
    return {"user_id": progress.user_id, "reboot_points": int(row["reboot_points"]) if row else points}


def log_feedback(event: FeedbackEvent, db_path: Path | None = None) -> dict[str, Any]:
    init_db(db_path)
    payload = to_plain_dict(event)
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO feedback_events
            (event_id, user_id, event_type, mission_id, resource_id, recommended_stage, burden_after,
             appropriateness_rating, risk_rating, user_note, policy_version, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.user_id,
                event.event_type.value if hasattr(event.event_type, "value") else event.event_type,
                event.mission_id,
                event.resource_id,
                event.recommended_stage,
                event.burden_after,
                event.appropriateness_rating,
                event.risk_rating,
                event.user_note,
                event.policy_version,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
    return {"event_id": event.event_id, "stored": True}


def log_outcome(event: OutcomeEvent, db_path: Path | None = None) -> dict[str, Any]:
    init_db(db_path)
    payload = to_plain_dict(event)
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO outcome_events
            (outcome_id, user_id, outcome_type, outcome_status, mission_id, resource_id, readiness_rating,
             burden_after, result_note, operator_review_status, operator_note, evidence_url, policy_version, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.outcome_id,
                event.user_id,
                event.outcome_type.value if hasattr(event.outcome_type, "value") else event.outcome_type,
                event.outcome_status.value if hasattr(event.outcome_status, "value") else event.outcome_status,
                event.mission_id,
                event.resource_id,
                event.readiness_rating,
                event.burden_after,
                event.result_note,
                event.operator_review_status,
                event.operator_note,
                event.evidence_url,
                event.policy_version,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
    return {"outcome_id": event.outcome_id, "stored": True}


def get_feedback_df(user_id: str | None = None, db_path: Path | None = None) -> pd.DataFrame:
    init_db(db_path)
    query = "SELECT * FROM feedback_events"
    params: tuple[Any, ...] = ()
    if user_id:
        query += " WHERE user_id = ?"
        params = (user_id,)
    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_outcomes_df(user_id: str | None = None, db_path: Path | None = None) -> pd.DataFrame:
    init_db(db_path)
    query = "SELECT * FROM outcome_events"
    params: tuple[Any, ...] = ()
    if user_id:
        query += " WHERE user_id = ?"
        params = (user_id,)
    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_progress_df(user_id: str | None = None, db_path: Path | None = None) -> pd.DataFrame:
    init_db(db_path)
    query = "SELECT * FROM progress_logs"
    params: tuple[Any, ...] = ()
    if user_id:
        query += " WHERE user_id = ?"
        params = (user_id,)
    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_reboot_points(user_id: str, db_path: Path | None = None) -> int:
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT reboot_points FROM user_state WHERE user_id = ?", (user_id,)).fetchone()
    return int(row["reboot_points"]) if row else 0
