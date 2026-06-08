from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rebootroute.rag.retriever import search_policy_culture_resources
from rebootroute.recommender.route_builder import analyze_profile
from rebootroute.schemas import UserProfile


def main() -> None:
    cases_path = ROOT / "evaluation" / "human_eval_cases.csv"
    out_path = ROOT / "reports" / "human_eval_review_sheet.csv"
    cases = pd.read_csv(cases_path)
    rows = []
    for _, case in cases.iterrows():
        profile = UserProfile(
            age=int(case.age),
            district=str(case.district),
            free_text=str(case.free_text),
            future_anxiety=int(case.future_anxiety),
            employment_burden=int(case.employment_burden),
            outside_burden=int(case.outside_burden),
            social_burden=int(case.social_burden),
            energy_level=int(case.energy_level),
            daily_rhythm_level=int(case.daily_rhythm_level),
            preferred_contact_mode=str(case.preferred_contact_mode),
            interests=str(case.interests).split("|"),
            max_outdoor_minutes=int(case.max_outdoor_minutes),
            budget_limit=int(case.budget_limit),
            has_support_person=bool(case.has_support_person),
        )
        result = analyze_profile(profile)
        rag = search_policy_culture_resources(case.free_text, district=case.district, max_burden_level=3, top_k=3)
        rows.append(
            {
                "case_id": case.case_id,
                "expected_stage_min": case.expected_stage_min,
                "expected_stage_max": case.expected_stage_max,
                "safety_expected": case.safety_expected,
                "predicted_stage": result["recommended_stage"],
                "safety_flag": result["safety_flag"],
                "route_name": result["recommended_route_name"],
                "top_missions": json.dumps([m["title"] for m in result.get("next_3_missions", [])], ensure_ascii=False),
                "rag_sources": json.dumps([s["name"] for s in rag.get("sources", [])], ensure_ascii=False),
                "stage_score": "",
                "mission_burden_score": "",
                "rag_grounding_score": "",
                "safety_score": "",
                "reviewer_comment": "",
            }
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(out_path)


if __name__ == "__main__":
    main()
