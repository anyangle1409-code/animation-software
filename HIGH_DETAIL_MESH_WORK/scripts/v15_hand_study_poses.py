"""Build deterministic no-equipment hand-study poses from validated poses."""
from __future__ import annotations

import copy
import json
from pathlib import Path


def study_payload(source: dict, exercise: str) -> dict:
    payload = copy.deepcopy(source)
    payload["exercise"] = exercise
    payload["label"] = "review"
    payload["equipment"] = []
    return payload


def ensure_study_poses(pose_root: Path) -> list[str]:
    recipes = (
        ("open_hand_review_candidate.json", "push_up_bottom_candidate.json", "Open Hand Review"),
        ("closed_fist_review_candidate.json", "dumbbell_bicep_curl_bottom_candidate.json", "Closed Fist Review"),
    )
    created = []
    for output_name, source_name, exercise in recipes:
        output = pose_root / output_name
        if output.is_file():
            continue
        source = pose_root / source_name
        if not source.is_file():
            raise SystemExit(f"Missing validated source pose for hand study: {source}")
        payload = study_payload(json.loads(source.read_text(encoding="utf-8")), exercise)
        output.write_text(json.dumps(payload), encoding="utf-8")
        created.append(output.name)
    return created
