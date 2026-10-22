"""Validate screenshot-only anatomical QA without upgrading it to native evidence."""
import json
import re
from pathlib import Path

from .registry import expand


def validate(data, seed, contracts):
    errors = []
    if data.get("schema_version") != 1 or data.get("evidence_scope") != "visual_only":
        errors.append("Invalid visual QA header")
    if data.get("blender_executed") is not False:
        errors.append("Blender execution must remain false for screenshot-only review")
    if data.get("source_identity", {}).get("status") != "unresolved":
        errors.append("Screenshot source identity must remain unresolved until pinned")

    images = data.get("evidence_images", [])
    image_ids = {image.get("id") for image in images}
    if not images or len(image_ids) != len(images):
        errors.append("Missing or duplicate evidence images")
    for image in images:
        if not re.fullmatch(r"[0-9a-f]{64}", image.get("sha256", "")):
            errors.append(f"{image.get('id')}: evidence image hash")
        pixels = image.get("pixel_dimensions")
        if not isinstance(pixels, list) or len(pixels) != 2 or any(not isinstance(x, int) or x <= 0 for x in pixels):
            errors.append(f"{image.get('id')}: evidence image dimensions")

    muscle_ids = {m["id"] for m in expand(seed)["muscles"]}
    exercise_phases = {
        (exercise["id"], phase["id"])
        for exercise in contracts.get("exercises", [])
        for phase in exercise.get("phases", [])
    }
    finding_ids = []
    allowed_priorities = {"P0", "P1", "P2", "P3"}
    for finding in data.get("findings", []):
        fid = finding.get("id", "<missing>")
        finding_ids.append(fid)
        if finding.get("status") != "visual_observation_unverified":
            errors.append(f"{fid}: invalid evidence status")
        if finding.get("causal_conclusion") is not None:
            errors.append(f"{fid}: screenshot review cannot assert a causal conclusion")
        if finding.get("priority") not in allowed_priorities:
            errors.append(f"{fid}: invalid priority")
        if not finding.get("symptom") or not finding.get("diagnostic_tests"):
            errors.append(f"{fid}: incomplete observation")
        if any(ref not in image_ids for ref in finding.get("evidence_image_ids", [])):
            errors.append(f"{fid}: unknown evidence image")
        for muscle_id in finding.get("affected_muscle_ids", []):
            if muscle_id not in muscle_ids:
                errors.append(f"{fid}: unknown muscle {muscle_id}")
        for ref in finding.get("exercise_phase_refs", []):
            pair = (ref.get("exercise_id"), ref.get("phase_id"))
            if pair not in exercise_phases:
                errors.append(f"{fid}: unknown exercise phase {pair}")
    if not finding_ids or len(finding_ids) != len(set(finding_ids)):
        errors.append("Missing or duplicate finding IDs")
    return errors


def main():
    root = Path(__file__).resolve().parents[2]
    data = json.loads((Path(__file__).with_name("current_w8_visual_qa.json")).read_text())
    seed = json.loads((root / "docs/ORIGINAL_V1_MUSCLE_REGISTRY_SEED_20261022.json").read_text())
    contracts = json.loads((Path(__file__).with_name("exercise_contracts.json")).read_text())
    errors = validate(data, seed, contracts)
    if errors:
        raise ValueError(errors)
    print(json.dumps({"findings": len(data["findings"]), "status": "PASS", "native_validation": "NOT_RUN"}))


if __name__ == "__main__":
    main()
