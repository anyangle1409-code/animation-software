"""Validate unbound ISB-inspired anatomical landmarks, never auto-bind to bones."""
import json
from pathlib import Path

REFERENCE = Path(__file__).resolve().parents[2] / "docs" / "anatomy" / "HGPT_ISB_LANDMARK_REQUIREMENTS_V1.json"
FIELDS_MUST_BE_NULL = (
    "model_bone_id", "model_mesh_vertex_id", "model_coordinate_body_local_m",
    "coordinate_frame", "reviewed_attachment_region", "model_source_sha256",
    "independent_side_evidence",
)
FIELDS_MUST_BE_FALSE = (
    "anatomical_side_verified", "landmark_verified", "muscle_attachment_authorized",
)

def validate(d):
    errors = []
    if d.get("schema_version") != 1 or d.get("status") != "UNBOUND_ANATOMICAL_LANDMARK_REQUIREMENTS_NOT_A_MODEL_CALIBRATION":
        errors.append("unapproved schema/status required")
    if d.get("native_bindings_approved") is not False or d.get("hard_limits_approved") is not False:
        errors.append("unearned native or ROM approval")
    if d.get("muscle_highlighting") != "DEFERRED_BY_OWNER":
        errors.append("muscle highlighting is deferred")
    source_ids = {s["id"] for s in d.get("sources", [])}
    if not {"isb_part_i_2002", "isb_part_ii_2005", "isb_multisegment_foot_2021"}.issubset(source_ids):
        errors.append("ISB provenance missing")
    landmarks = d.get("landmarks", [])
    if len(landmarks) != d.get("landmark_count") or len(landmarks) != 46:
        errors.append("landmark coverage count mismatch")
    names = set()
    for x in landmarks:
        if not isinstance(x, dict):
            errors.append("malformed landmark")
            continue
        name = x.get("id")
        if not isinstance(name, str) or not name.startswith("hgpt.landmark.") or name in names:
            errors.append("duplicate or malformed landmark ID")
        names.add(name)
        if x.get("source_id") not in source_ids:
            errors.append("unknown source for landmark")
        if x.get("side") not in {"L", "R", "MIDLINE"}:
            errors.append("invalid anatomical side label")
        if any(x.get(key, "MISSING") is not None for key in FIELDS_MUST_BE_NULL):
            errors.append("unverified native landmark binding must remain NULL")
        if any(x.get(key, "MISSING") is not False for key in FIELDS_MUST_BE_FALSE):
            errors.append("landmark/side/attachment cannot be approved")
        if x.get("source_precision") not in {
            "ISB_UPPER_LIMB_SEGMENT_LANDMARK",
            "CENTRE_ESTIMATION_METHOD_UNSELECTED",
            "PROPOSED_REVIEW_CANDIDATE_NOT_CLAIMED_EXACT_ISB_DEFINITION",
        }:
            errors.append("unreviewed landmark provenance precision")
    for x in landmarks:
        if not isinstance(x, dict) or x.get("side") not in {"L", "R"}:
            continue
        other = x["id"][:-1] + ("R" if x["side"] == "L" else "L")
        if other not in names:
            errors.append("missing contralateral landmark ID")
    if not all("hgpt.landmark.thorax." + name + ".MIDLINE" in names for name in ("IJ", "PX", "C7", "T8")):
        errors.append("thorax landmark frame incomplete")
    segments = d.get("segment_requirements", [])
    if len(segments) != 9:
        errors.append("missing anatomical segment frame requirements")
    for segment in segments:
        if segment.get("isb_axes_defined") is not False:
            errors.append("unearned ISB segment frame")
        for key in segment.get("required_landmarks", []):
            if "." not in key:
                errors.append("malformed required landmark")
                continue
            if key.endswith(".MIDLINE"):
                full = "hgpt.landmark." + key
                if full not in names:
                    errors.append("missing midline segment landmark")
            else:
                for side in ("L", "R"):
                    if "hgpt.landmark." + key + "." + side not in names:
                        errors.append("missing bilateral segment landmark")
    motions = d.get("joint_motion_distinctions", [])
    if len(motions) < 4 or any(m.get("status") != "NOT_MEASURED" for m in motions):
        errors.append("coupled human motion remains unmeasured")
    return errors

def load(path=REFERENCE):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate(d)
    if errors:
        raise ValueError("; ".join(errors))
    return d

if __name__ == "__main__":
    doc = load()
    print("RESEARCH_ONLY_UNBOUND_ISB_LANDMARKS", len(doc["landmarks"]), "native calibration NOT_GRANTED")
