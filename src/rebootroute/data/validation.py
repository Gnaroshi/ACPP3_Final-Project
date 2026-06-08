from __future__ import annotations

import json
from typing import Callable

import pandas as pd

from rebootroute.config import ensure_directories, load_config
from rebootroute.data.mock_data import ensure_mock_data

try:
    import pandera.pandas as pa
    from pandera.pandas import Check, Column, DataFrameSchema
except Exception:  # pragma: no cover - compatibility with older/missing pandera.
    try:
        import pandera as pa
        from pandera import Check, Column, DataFrameSchema
    except Exception:
        pa = None
        Check = None
        Column = None
        DataFrameSchema = None


def parse_list(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value)]


def _manual_validate(df: pd.DataFrame, required: dict[str, Callable[[pd.Series], pd.Series]], name: str) -> pd.DataFrame:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    for column, predicate in required.items():
        invalid = ~predicate(df[column])
        if invalid.any():
            bad_rows = invalid[invalid].index.tolist()[:5]
            raise ValueError(f"{name}.{column} failed validation at rows {bad_rows}")
    return df


def _in_values(values: set[str]) -> Callable[[pd.Series], pd.Series]:
    return lambda s: s.astype(str).isin(values)


def _validate_resource_provenance(df: pd.DataFrame) -> pd.DataFrame:
    required = {
        "source_url",
        "detail_url",
        "source_kind",
        "source_checked_at",
        "official_title",
        "official_summary",
        "crawl_status",
        "derived_reason",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"resources missing provenance columns: {missing}")

    url_invalid = ~df["source_url"].astype(str).str.startswith("https://")
    detail_invalid = ~df["detail_url"].astype(str).str.startswith("https://")
    checked_invalid = df["source_checked_at"].astype(str).str.strip().eq("")
    source_kind_invalid = ~df["source_kind"].astype(str).isin({"open_api", "html_scrape", "fallback_seed", "manual_verified"})
    crawl_status_invalid = ~df["crawl_status"].astype(str).isin({"ok", "fallback_seed", "partial", "failed"})
    official_resource_invalid = df["resource_type"].astype(str).eq("mini_project")
    rebootroute_source_invalid = df["source_name"].astype(str).str.contains("RebootRoute", case=False, na=False)

    suspicious_pattern = r"入口|公式|curated|example\.com|RebootRoute official"
    visible_columns = ["name", "description", "source_name", "official_title", "official_summary"]
    suspicious = pd.Series(False, index=df.index)
    for column in visible_columns:
        suspicious = suspicious | df[column].astype(str).str.contains(suspicious_pattern, case=False, regex=True, na=False)

    checks = {
        "source_url": url_invalid,
        "detail_url": detail_invalid,
        "source_checked_at": checked_invalid,
        "source_kind": source_kind_invalid,
        "crawl_status": crawl_status_invalid,
        "official_resource_type": official_resource_invalid,
        "source_name": rebootroute_source_invalid,
        "visible_text": suspicious,
    }
    for name, invalid in checks.items():
        if invalid.any():
            bad_rows = invalid[invalid].index.tolist()[:5]
            raise ValueError(f"resources.{name} provenance validation failed at rows {bad_rows}")
    return df


def validate_profiles(df: pd.DataFrame) -> pd.DataFrame:
    if pa is not None:
        schema = DataFrameSchema(
            {
                "user_id": Column(str, nullable=False),
                "age": Column(int, Check.in_range(19, 39)),
                "district": Column(str),
                "free_text": Column(str, nullable=True),
                "future_anxiety": Column(int, Check.in_range(1, 5)),
                "employment_burden": Column(int, Check.in_range(1, 5)),
                "outside_burden": Column(int, Check.in_range(1, 5)),
                "social_burden": Column(int, Check.in_range(1, 5)),
                "energy_level": Column(int, Check.in_range(1, 5)),
                "daily_rhythm_level": Column(int, Check.in_range(1, 5)),
                "preferred_contact_mode": Column(str, Check.isin(["online", "low_contact", "small_group", "in_person"])),
                "interests": Column(str),
                "max_outdoor_minutes": Column(int, Check.ge(0)),
                "budget_limit": Column(int, Check.ge(0)),
                "has_support_person": Column(bool),
                "created_at": Column(str),
            },
            coerce=True,
        )
        return schema.validate(df)
    return _manual_validate(
        df,
        {
            "user_id": lambda s: s.notna(),
            "age": lambda s: s.astype(int).between(19, 39),
            "future_anxiety": lambda s: s.astype(int).between(1, 5),
            "employment_burden": lambda s: s.astype(int).between(1, 5),
            "outside_burden": lambda s: s.astype(int).between(1, 5),
            "social_burden": lambda s: s.astype(int).between(1, 5),
            "energy_level": lambda s: s.astype(int).between(1, 5),
            "daily_rhythm_level": lambda s: s.astype(int).between(1, 5),
            "preferred_contact_mode": _in_values({"online", "low_contact", "small_group", "in_person"}),
            "max_outdoor_minutes": lambda s: s.astype(int).ge(0),
            "budget_limit": lambda s: s.astype(int).ge(0),
        },
        "profiles",
    )


def validate_resources(df: pd.DataFrame) -> pd.DataFrame:
    resource_types = {"youth_program", "culture_event", "culture_facility", "support_program", "mini_project", "contest"}
    if pa is not None:
        schema = DataFrameSchema(
            {
                "resource_id": Column(str),
                "resource_type": Column(str, Check.isin(sorted(resource_types))),
                "name": Column(str),
                "description": Column(str),
                "district": Column(str),
                "address": Column(str),
                "cost_type": Column(str, Check.isin(["free", "low_cost", "paid", "unknown"])),
                "online_available": Column(bool),
                "social_contact_level": Column(int, Check.in_range(0, 5)),
                "outdoor_required": Column(bool),
                "estimated_duration_minutes": Column(int, Check.ge(0)),
                "burden_level": Column(int, Check.in_range(0, 5)),
                "career_tags": Column(str),
                "recovery_tags": Column(str),
                "source_name": Column(str),
                "source_url": Column(str),
                "detail_url": Column(str),
                "source_kind": Column(str, Check.isin(["open_api", "html_scrape", "fallback_seed", "manual_verified"])),
                "crawl_status": Column(str, Check.isin(["ok", "fallback_seed", "partial", "failed"])),
                "source_checked_at": Column(str),
                "official_title": Column(str),
                "official_summary": Column(str),
                "derived_reason": Column(str),
                "updated_at": Column(str),
            },
            coerce=True,
        )
        return _validate_resource_provenance(schema.validate(df))
    validated = _manual_validate(
        df,
        {
            "resource_id": lambda s: s.notna(),
            "resource_type": _in_values(resource_types),
            "cost_type": _in_values({"free", "low_cost", "paid", "unknown"}),
            "social_contact_level": lambda s: s.astype(int).between(0, 5),
            "estimated_duration_minutes": lambda s: s.astype(int).ge(0),
            "burden_level": lambda s: s.astype(int).between(0, 5),
        },
        "resources",
    )
    return _validate_resource_provenance(validated)


def validate_missions(df: pd.DataFrame) -> pd.DataFrame:
    mission_types = {
        "info_contact",
        "save",
        "micro_action",
        "short_outing",
        "low_contact_participation",
        "program_participation",
        "career_exploration",
        "mini_work_experience",
        "self_reliance_link",
    }
    evidence_types = {"none", "save_click", "text_note", "photo_optional", "checkin_optional", "link_click", "file_upload"}
    if pa is not None:
        schema = DataFrameSchema(
            {
                "mission_id": Column(str),
                "stage": Column(int, Check.in_range(0, 7)),
                "title": Column(str),
                "description": Column(str),
                "mission_type": Column(str, Check.isin(sorted(mission_types))),
                "expected_minutes": Column(int, Check.ge(1)),
                "outdoor_required": Column(bool),
                "social_contact_required": Column(bool),
                "evidence_type": Column(str, Check.isin(sorted(evidence_types))),
                "burden_level": Column(int, Check.in_range(0, 5)),
                "reward_points": Column(int, Check.ge(0)),
                "career_tags": Column(str),
                "recovery_tags": Column(str),
            },
            coerce=True,
        )
        return schema.validate(df)
    return _manual_validate(
        df,
        {
            "mission_id": lambda s: s.notna(),
            "stage": lambda s: s.astype(int).between(0, 7),
            "mission_type": _in_values(mission_types),
            "expected_minutes": lambda s: s.astype(int).ge(1),
            "evidence_type": _in_values(evidence_types),
            "burden_level": lambda s: s.astype(int).between(0, 5),
            "reward_points": lambda s: s.astype(int).ge(0),
        },
        "missions",
    )


def validate_progress(df: pd.DataFrame) -> pd.DataFrame:
    statuses = {"recommended", "started", "completed", "skipped", "too_hard"}
    if pa is not None:
        schema = DataFrameSchema(
            {
                "log_id": Column(str),
                "user_id": Column(str),
                "mission_id": Column(str),
                "status": Column(str, Check.isin(sorted(statuses))),
                "points_awarded": Column(int, Check.ge(0)),
            },
            coerce=True,
        )
        return schema.validate(df)
    return _manual_validate(
        df,
        {
            "log_id": lambda s: s.notna(),
            "user_id": lambda s: s.notna(),
            "mission_id": lambda s: s.notna(),
            "status": _in_values(statuses),
            "points_awarded": lambda s: s.astype(int).ge(0),
        },
        "progress",
    )


def validate_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    outcome_types = {
        "program_participation",
        "support_application",
        "support_result",
        "mini_project_submission",
        "operator_review",
    }
    outcome_statuses = {
        "planned",
        "applied",
        "participated",
        "submitted",
        "accepted",
        "rejected",
        "not_eligible",
        "needs_follow_up",
        "verified",
        "rework_requested",
        "unknown",
    }
    if df.empty:
        return df
    if pa is not None:
        schema = DataFrameSchema(
            {
                "outcome_id": Column(str),
                "user_id": Column(str),
                "outcome_type": Column(str, Check.isin(sorted(outcome_types))),
                "outcome_status": Column(str, Check.isin(sorted(outcome_statuses))),
                "readiness_rating": Column(float, nullable=True),
                "burden_after": Column(float, nullable=True),
                "created_at": Column(str),
            },
            coerce=True,
        )
        return schema.validate(df)
    return _manual_validate(
        df,
        {
            "outcome_id": lambda s: s.notna(),
            "user_id": lambda s: s.notna(),
            "outcome_type": _in_values(outcome_types),
            "outcome_status": _in_values(outcome_statuses),
        },
        "outcomes",
    )


def validate_all() -> dict[str, int]:
    cfg = load_config()
    ensure_directories(cfg)
    paths = ensure_mock_data()
    profiles = validate_profiles(pd.read_csv(paths["profiles"]))
    resources = validate_resources(pd.read_csv(paths["resources"]))
    missions = validate_missions(pd.read_csv(paths["missions"]))
    progress = validate_progress(pd.read_csv(paths["progress"]))
    outcomes = validate_outcomes(pd.read_csv(paths["outcomes"]))
    return {
        "profiles": len(profiles),
        "resources": len(resources),
        "missions": len(missions),
        "progress": len(progress),
        "outcomes": len(outcomes),
        "pandera_available": int(pa is not None),
    }


if __name__ == "__main__":
    result = validate_all()
    print(result)
