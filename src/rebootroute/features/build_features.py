from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from rebootroute.config import ensure_directories, load_config
from rebootroute.data.mock_data import load_raw_data
from rebootroute.data.validation import parse_list


INTEREST_VOCAB = ["culture", "design", "writing", "IT", "public_policy", "planning", "library", "media", "craft", "data"]
CONTACT_ENCODING = {"online": 0, "low_contact": 1, "small_group": 2, "in_person": 3}
BASE_FEATURE_COLUMNS = [
    "age",
    "future_anxiety_score",
    "employment_burden_score",
    "outside_burden_score",
    "social_burden_score",
    "energy_score",
    "daily_rhythm_score",
    "isolation_risk_proxy",
    "readiness_score",
    "preferred_contact_encoded",
    "max_outdoor_minutes",
    "budget_limit",
    "has_support_person_int",
    "recent_success_rate",
    "recent_too_hard_rate",
]
STAGE_FEATURE_COLUMNS = [f"completed_stage_{stage}" for stage in range(8)]
INTEREST_FEATURE_COLUMNS = [f"interest_{interest}" for interest in INTEREST_VOCAB]
FEATURE_COLUMNS = BASE_FEATURE_COLUMNS + STAGE_FEATURE_COLUMNS + INTEREST_FEATURE_COLUMNS


def normalize_score(value: float, low: float = 1, high: float = 5) -> float:
    if high == low:
        return 0.0
    return float(np.clip((value - low) / (high - low), 0, 1))


def _progress_aggregates(progress: pd.DataFrame, missions: pd.DataFrame) -> pd.DataFrame:
    if progress.empty:
        base = pd.DataFrame(columns=["user_id", "recent_success_rate", "recent_too_hard_rate"] + STAGE_FEATURE_COLUMNS)
        return base

    merged = progress.merge(missions[["mission_id", "stage"]], on="mission_id", how="left")
    completed = merged[merged["status"] == "completed"]
    stage_counts = (
        completed.pivot_table(index="user_id", columns="stage", values="mission_id", aggfunc="count", fill_value=0)
        .rename(columns={stage: f"completed_stage_{int(stage)}" for stage in range(8)})
        .reset_index()
    )
    for column in STAGE_FEATURE_COLUMNS:
        if column not in stage_counts.columns:
            stage_counts[column] = 0

    status_counts = merged.pivot_table(index="user_id", columns="status", values="mission_id", aggfunc="count", fill_value=0).reset_index()
    total = status_counts.drop(columns=["user_id"]).sum(axis=1).replace(0, np.nan)
    status_counts["recent_success_rate"] = status_counts.get("completed", 0) / total
    status_counts["recent_too_hard_rate"] = status_counts.get("too_hard", 0) / total
    status_counts = status_counts[["user_id", "recent_success_rate", "recent_too_hard_rate"]].fillna(0)
    return stage_counts.merge(status_counts, on="user_id", how="outer").fillna(0)


def add_profile_features(profiles: pd.DataFrame, progress: pd.DataFrame | None = None, missions: pd.DataFrame | None = None) -> pd.DataFrame:
    df = profiles.copy()
    df["future_anxiety_score"] = df["future_anxiety"].apply(normalize_score)
    df["employment_burden_score"] = df["employment_burden"].apply(normalize_score)
    df["outside_burden_score"] = df["outside_burden"].apply(normalize_score)
    df["social_burden_score"] = df["social_burden"].apply(normalize_score)
    df["energy_score"] = df["energy_level"].apply(normalize_score)
    df["daily_rhythm_score"] = df["daily_rhythm_level"].apply(normalize_score)
    df["isolation_risk_proxy"] = (
        0.30 * df["outside_burden_score"]
        + 0.30 * df["social_burden_score"]
        + 0.20 * (1 - df["energy_score"])
        + 0.20 * (1 - df["daily_rhythm_score"])
    )
    df["readiness_score"] = (
        0.35 * df["energy_score"]
        + 0.25 * df["daily_rhythm_score"]
        + 0.15 * (1 - df["outside_burden_score"])
        + 0.15 * (1 - df["social_burden_score"])
        + 0.10 * df["has_support_person"].astype(int)
    )
    df["preferred_contact_encoded"] = df["preferred_contact_mode"].map(CONTACT_ENCODING).fillna(0).astype(int)
    df["has_support_person_int"] = df["has_support_person"].astype(int)

    interests = df["interests"].apply(parse_list)
    for interest in INTEREST_VOCAB:
        df[f"interest_{interest}"] = interests.apply(lambda values, interest=interest: int(interest in values))

    for column in STAGE_FEATURE_COLUMNS:
        df[column] = 0
    df["recent_success_rate"] = 0.0
    df["recent_too_hard_rate"] = 0.0

    if progress is not None and missions is not None:
        aggregates = _progress_aggregates(progress, missions)
        if not aggregates.empty:
            df = df.drop(columns=STAGE_FEATURE_COLUMNS + ["recent_success_rate", "recent_too_hard_rate"], errors="ignore")
            df = df.merge(aggregates, on="user_id", how="left")
            for column in STAGE_FEATURE_COLUMNS:
                if column not in df.columns:
                    df[column] = 0
            df[STAGE_FEATURE_COLUMNS + ["recent_success_rate", "recent_too_hard_rate"]] = df[
                STAGE_FEATURE_COLUMNS + ["recent_success_rate", "recent_too_hard_rate"]
            ].fillna(0)
    return df


def create_synthetic_labels(features: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = features.copy()
    labels: list[int] = []
    for _, row in df.iterrows():
        energy = row["energy_score"]
        outside = row["outside_burden_score"]
        social = row["social_burden_score"]
        readiness = row["readiness_score"]
        completed_34 = row.get("completed_stage_3", 0) + row.get("completed_stage_4", 0)
        completed_5 = row.get("completed_stage_5", 0)
        completed_6 = row.get("completed_stage_6", 0)

        if completed_6 >= 1 and readiness >= 0.62:
            stage = 7
        elif completed_5 >= 1 and readiness >= 0.45:
            stage = 6
        elif completed_34 >= 2:
            stage = 5
        elif energy >= 0.55 and outside <= 0.55 and social <= 0.65:
            stage = 4
        elif energy >= 0.50 and outside <= 0.60:
            stage = 3 if row["max_outdoor_minutes"] >= 20 else 2
        elif outside >= 0.75 or social >= 0.75:
            stage = 1 if energy >= 0.25 or row.get("completed_stage_0", 0) > 0 else 0
        else:
            stage = 2

        if rng.random() < 0.12:
            stage = int(np.clip(stage + rng.choice([-1, 1]), 0, 7))
        labels.append(stage)

    burden_pressure = (
        df["future_anxiety_score"]
        + df["employment_burden_score"]
        + df["outside_burden_score"]
        + df["social_burden_score"]
    ) / 4
    success_score = np.clip(
        0.20
        + 0.55 * df["readiness_score"]
        + 0.15 * df["recent_success_rate"]
        - 0.20 * df["recent_too_hard_rate"]
        - 0.15 * burden_pressure,
        0.05,
        0.95,
    )
    df["synthetic_stage_label"] = labels
    df["synthetic_mission_success"] = ((success_score + rng.normal(0, 0.07, len(df))) >= 0.42).astype(int)
    return df


def data_version_hash(df: pd.DataFrame) -> str:
    stable = df.sort_index(axis=1).to_csv(index=False).encode("utf-8")
    return hashlib.sha256(stable).hexdigest()[:16]


def build_feature_tables() -> dict[str, Any]:
    cfg = load_config()
    ensure_directories(cfg)
    data = load_raw_data()
    profiles = add_profile_features(data["profiles"], data["progress"], data["missions"])
    training = create_synthetic_labels(profiles, cfg.random_seed)
    feature_path = cfg.feature_data_dir / "user_features.csv"
    training_path = cfg.feature_data_dir / "training_features.csv"
    profiles.to_csv(feature_path, index=False)
    training.to_csv(training_path, index=False)
    version = data_version_hash(training[FEATURE_COLUMNS + ["synthetic_stage_label", "synthetic_mission_success"]])
    version_path = cfg.feature_data_dir / "data_version.json"
    version_path.write_text(json.dumps({"data_version": version}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "feature_path": feature_path,
        "training_path": training_path,
        "data_version": version,
        "rows": len(training),
        "feature_columns": FEATURE_COLUMNS,
    }


def profile_to_feature_frame(profile: dict[str, Any], progress: pd.DataFrame | None = None, missions: pd.DataFrame | None = None) -> pd.DataFrame:
    row = profile.copy()
    if isinstance(row.get("interests"), list):
        row["interests"] = json.dumps(row["interests"], ensure_ascii=False)
    if "user_id" not in row:
        row["user_id"] = "runtime_user"
    df = pd.DataFrame([row])
    features = add_profile_features(df, progress=progress, missions=missions)
    for column in FEATURE_COLUMNS:
        if column not in features.columns:
            features[column] = 0
    return features[FEATURE_COLUMNS]


if __name__ == "__main__":
    result = build_feature_tables()
    print(result)
