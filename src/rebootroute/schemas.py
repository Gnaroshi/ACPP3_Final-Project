from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


class ContactMode(str, Enum):
    online = "online"
    low_contact = "low_contact"
    small_group = "small_group"
    in_person = "in_person"


class ResourceType(str, Enum):
    youth_program = "youth_program"
    culture_event = "culture_event"
    culture_facility = "culture_facility"
    support_program = "support_program"
    mini_project = "mini_project"
    contest = "contest"


class CostType(str, Enum):
    free = "free"
    low_cost = "low_cost"
    paid = "paid"
    unknown = "unknown"


class MissionType(str, Enum):
    info_contact = "info_contact"
    save = "save"
    micro_action = "micro_action"
    short_outing = "short_outing"
    low_contact_participation = "low_contact_participation"
    program_participation = "program_participation"
    career_exploration = "career_exploration"
    mini_work_experience = "mini_work_experience"
    self_reliance_link = "self_reliance_link"


class EvidenceType(str, Enum):
    none = "none"
    save_click = "save_click"
    text_note = "text_note"
    photo_optional = "photo_optional"
    checkin_optional = "checkin_optional"
    link_click = "link_click"
    file_upload = "file_upload"


class ProgressStatus(str, Enum):
    recommended = "recommended"
    started = "started"
    completed = "completed"
    skipped = "skipped"
    too_hard = "too_hard"


class FeedbackEventType(str, Enum):
    impression = "impression"
    save = "save"
    start = "start"
    complete = "complete"
    skip = "skip"
    too_hard = "too_hard"
    resource_click = "resource_click"
    support_link_click = "support_link_click"
    safety_branch = "safety_branch"
    operator_review = "operator_review"


class OutcomeType(str, Enum):
    program_participation = "program_participation"
    support_application = "support_application"
    support_result = "support_result"
    mini_project_submission = "mini_project_submission"
    operator_review = "operator_review"


class OutcomeStatus(str, Enum):
    planned = "planned"
    applied = "applied"
    participated = "participated"
    submitted = "submitted"
    accepted = "accepted"
    rejected = "rejected"
    not_eligible = "not_eligible"
    needs_follow_up = "needs_follow_up"
    verified = "verified"
    rework_requested = "rework_requested"
    unknown = "unknown"


class UserProfile(BaseModel):
    user_id: str = Field(default_factory=lambda: new_id("user"))
    age: int = Field(ge=19, le=39)
    district: str
    free_text: str = ""
    future_anxiety: int = Field(ge=1, le=5)
    employment_burden: int = Field(ge=1, le=5)
    outside_burden: int = Field(ge=1, le=5)
    social_burden: int = Field(ge=1, le=5)
    energy_level: int = Field(ge=1, le=5)
    daily_rhythm_level: int = Field(ge=1, le=5)
    preferred_contact_mode: ContactMode
    interests: list[str] = Field(default_factory=list)
    max_outdoor_minutes: int = Field(ge=0, le=360)
    budget_limit: int = Field(ge=0)
    has_support_person: bool = False
    current_stage_label: str | None = None
    created_at: datetime = Field(default_factory=now_utc)


class Resource(BaseModel):
    resource_id: str
    resource_type: ResourceType
    name: str
    description: str
    district: str
    address: str
    latitude: float | None = None
    longitude: float | None = None
    start_date: date | None = None
    end_date: date | None = None
    cost_type: CostType
    online_available: bool
    social_contact_level: int = Field(ge=0, le=5)
    outdoor_required: bool
    estimated_duration_minutes: int = Field(ge=0)
    burden_level: int = Field(ge=0, le=5)
    career_tags: list[str] = Field(default_factory=list)
    recovery_tags: list[str] = Field(default_factory=list)
    source_name: str
    source_url: str | None = None
    detail_url: str | None = None
    thumbnail_url: str | None = None
    contact: str | None = None
    official_title: str | None = None
    official_summary: str | None = None
    official_period: str | None = None
    official_place: str | None = None
    source_kind: str | None = None
    crawl_status: str | None = None
    source_checked_at: datetime | None = None
    derived_reason: str | None = None
    updated_at: datetime = Field(default_factory=now_utc)


class Mission(BaseModel):
    mission_id: str
    stage: int = Field(ge=0, le=7)
    title: str
    description: str
    mission_type: MissionType
    expected_minutes: int = Field(ge=1)
    outdoor_required: bool
    social_contact_required: bool
    evidence_type: EvidenceType
    burden_level: int = Field(ge=0, le=5)
    reward_points: int = Field(ge=0)
    career_tags: list[str] = Field(default_factory=list)
    recovery_tags: list[str] = Field(default_factory=list)


class ProgressLog(BaseModel):
    log_id: str = Field(default_factory=lambda: new_id("log"))
    user_id: str
    mission_id: str
    status: ProgressStatus
    user_note: str | None = None
    completed_at: datetime | None = None
    points_awarded: int = Field(default=0, ge=0)


class IntakeResponse(BaseModel):
    recommended_stage: int
    recommended_route_name: str
    burden_summary: str
    explanation: str
    next_3_missions: list[dict[str, Any]]
    recommended_resources: list[dict[str, Any]]
    mini_project_candidates: list[dict[str, Any]]
    safety_flag: bool
    model_info: dict[str, Any]
    risk_type: str | None = None
    message: str | None = None
    safety_resources: list[dict[str, Any]] = Field(default_factory=list)
    contributing_factors: list[str] = Field(default_factory=list)


class FeedbackEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: new_id("event"))
    user_id: str
    event_type: FeedbackEventType
    mission_id: str | None = None
    resource_id: str | None = None
    recommended_stage: int | None = Field(default=None, ge=0, le=7)
    burden_after: int | None = Field(default=None, ge=1, le=5)
    appropriateness_rating: int | None = Field(default=None, ge=1, le=5)
    risk_rating: int | None = Field(default=None, ge=1, le=5)
    user_note: str | None = None
    policy_version: str | None = None
    created_at: datetime = Field(default_factory=now_utc)


class OutcomeEvent(BaseModel):
    outcome_id: str = Field(default_factory=lambda: new_id("outcome"))
    user_id: str
    outcome_type: OutcomeType
    outcome_status: OutcomeStatus
    mission_id: str | None = None
    resource_id: str | None = None
    readiness_rating: int | None = Field(default=None, ge=1, le=5)
    burden_after: int | None = Field(default=None, ge=1, le=5)
    result_note: str | None = None
    operator_review_status: str | None = None
    operator_note: str | None = None
    evidence_url: str | None = None
    policy_version: str | None = None
    created_at: datetime = Field(default_factory=now_utc)


class RAGSearchRequest(BaseModel):
    query: str
    district: str | None = None
    resource_types: list[ResourceType] = Field(default_factory=list)
    max_burden_level: int | None = Field(default=None, ge=0, le=5)
    top_k: int = Field(default=5, ge=1, le=10)


class SimulationRequest(BaseModel):
    profile: UserProfile
    changes: dict[str, list[int]] = Field(default_factory=dict)


def to_plain_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()
