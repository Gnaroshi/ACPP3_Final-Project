from __future__ import annotations

import re
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

from rebootroute.config import load_config


HIGH_RISK_PATTERNS = [
    r"죽고\s*싶",
    r"자살",
    r"극단적\s*선택",
    r"사라지고\s*싶",
    r"해치고\s*싶",
    r"죽이",
    r"위험한\s*충동",
    r"self[- ]?harm",
    r"suicide",
    r"kill myself",
    r"hurt someone",
]


def load_safety_resources() -> dict[str, Any]:
    cfg = load_config()
    if not cfg.safety_resources_path.exists():
        return {"message": "지금은 미션 추천보다 안전 확인과 즉시 도움 연결이 우선입니다.", "resources": []}
    if yaml is None:
        return _parse_simple_safety_yaml(cfg.safety_resources_path)
    with cfg.safety_resources_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"resources": []}


def _parse_simple_safety_yaml(path) -> dict[str, Any]:
    message = "지금은 미션 추천보다 안전 확인과 즉시 도움 연결이 우선입니다."
    resources: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("message:"):
            message = stripped.split(":", 1)[1].strip().strip('"')
        elif stripped.startswith("- "):
            if current:
                resources.append(current)
            current = {}
            key, _, value = stripped[2:].partition(":")
            current[key.strip()] = value.strip().strip('"')
        elif current is not None and ":" in stripped:
            key, _, value = stripped.partition(":")
            current[key.strip()] = value.strip().strip('"')
    if current:
        resources.append(current)
    return {"message": message, "resources": resources}


def check_safety(free_text: str | None) -> dict[str, Any]:
    text = free_text or ""
    for pattern in HIGH_RISK_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            resources = load_safety_resources()
            return {
                "safety_flag": True,
                "risk_type": "urgent_support_needed",
                "message": resources.get("message", "지금은 미션 추천보다 안전 확인과 즉시 도움 연결이 우선입니다."),
                "safety_resources": resources.get("resources", []),
            }
    return {"safety_flag": False, "risk_type": None, "message": None, "safety_resources": []}


def safety_language_notice() -> str:
    return (
        "RebootRoute는 진단이나 치료 서비스가 아니며, 생활 리듬 회복과 지역 자원 탐색을 위한 단계형 추천 도구입니다. "
        "추천은 부담을 낮추는 선택지이며 오늘은 확인만 해도 충분합니다."
    )
