"""Declare the measured r96 weights-only probe zone without editing a Blend.

Run with Blender's Python so numpy is available:
  blender --background --factory-startup --python this_script.py -- dump.npz [out.json]
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))
from original_v1_shoulder_yoke_declaration import R95_SHA256, validate_declaration
from original_v1_shoulder_yoke_probe import select_safe_mirror_subzone


ROOT = SCRIPT.parents[1]
MAX_DECLARATION = ROOT / "ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/shoulder_yoke_declared_before_edit.json"
AUDIT = MAX_DECLARATION.with_name("r95_declared_zone_weight_audit.json")
DEFAULT_OUT = MAX_DECLARATION.with_name("r96_weight_subzone_declared_before_edit.json")
GRADIENT_THRESHOLD = 0.25
DILATION_RINGS = 1


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        raise SystemExit("dump path is required")
    dump_path = Path(args[0]).resolve()
    out = Path(args[1]).resolve() if len(args) > 1 else DEFAULT_OUT.resolve()
    markdown = out.with_name("WEIGHT_SUBZONE_DECLARATION.md")
    if out.exists() or markdown.exists():
        raise SystemExit("refusing to overwrite the r96 weight subzone declaration")

    maximum = json.loads(MAX_DECLARATION.read_text(encoding="utf-8-sig"))
    errors = validate_declaration(maximum, ROOT)
    if errors:
        raise SystemExit("invalid maximum r96 declaration: " + "; ".join(errors))
    dump = np.load(dump_path)
    source_sha = str(dump["source_sha256"].item())
    if source_sha != R95_SHA256:
        raise SystemExit("exact frozen r95 skinning dump required: " + source_sha)

    weights = dump["W"]
    bones = [str(item) for item in dump["bones"]]
    rest = dump["rest"]
    edges = dump["edges"]
    region_names = [str(item) for item in dump["region_names"]]
    regions = [region_names[int(item)] for item in dump["region"]]
    rows = [
        {bone: float(row[index]) for index, bone in enumerate(bones) if row[index] > 1e-8}
        for row in weights
    ]
    zone = maximum["zone"]
    selection = select_safe_mirror_subzone(
        zone["left_vertex_ids"],
        zone["right_vertex_ids"],
        rows,
        regions,
        set(zone["permitted_regions"]),
        set(maximum["permitted_bones"]),
        edges,
        gradient_threshold=GRADIENT_THRESHOLD,
        dilation_rings=DILATION_RINGS,
    )
    left = selection.pop("left_vertex_ids")
    right = selection.pop("right_vertex_ids")
    if not left or len(left) != len(right):
        raise SystemExit("measured r96 weight subzone is empty or not mirror closed")
    if not set(left).issubset(zone["left_vertex_ids"]) or not set(right).issubset(zone["right_vertex_ids"]):
        raise SystemExit("measured r96 weight subzone escaped the maximum declaration")

    record = {
        "schema_version": 1,
        "declared_utc": datetime.now(timezone.utc).isoformat(),
        "declared_before_edit": True,
        "target_revision": "r96",
        "parent": maximum["parent"],
        "maximum_declaration": MAX_DECLARATION.relative_to(ROOT).as_posix(),
        "maximum_declaration_sha256": digest(MAX_DECLARATION),
        "diagnostic_audit": AUDIT.relative_to(ROOT).as_posix(),
        "diagnostic_audit_sha256": digest(AUDIT),
        "skinning_dump_source_sha256": source_sha,
        "zone_rule": (
            "mirror pairs inside the maximum r96 shoulder-yoke declaration whose existing deform influences "
            "are limited to the declared shoulder-yoke bones and whose r95 incident deform-weight L1 jump is "
            f">= {GRADIENT_THRESHOLD}, dilated by {DILATION_RINGS} mesh ring within those safe pairs"
        ),
        "gradient_threshold_l1": GRADIENT_THRESHOLD,
        "dilation_rings": DILATION_RINGS,
        "left_owned_vertex_ids": left,
        "mirror_of_strict_left_vertex_ids": right,
        "mirror_pairs": [[a, b] for a, b in zip(left, right)],
        "vertex_count_total": len(left) + len(right),
        "pair_count": len(left),
        "selection_counts": selection,
        "ids_sha256": hashlib.sha256(np.asarray([left, right], dtype="<i8").tobytes()).hexdigest(),
        "rest_bbox_min_m": [round(float(value), 6) for value in rest[left].min(axis=0)],
        "rest_bbox_max_m": [round(float(value), 6) for value in rest[left].max(axis=0)],
        "permitted_regions": zone["permitted_regions"],
        "permitted_bones": maximum["permitted_bones"],
        "allowed_change": (
            "deform weights on exactly these mirror-closed existing vertices; preserve every non-permitted "
            "bone column exactly; normalized deterministic diffusion using only the existing 67-bone rig"
        ),
        "weights_only_gate": {
            "correctives_disabled": True,
            "maximum_influences": 4,
            "mirror_symmetric": True,
            "topology_change": False,
            "baseline_or_threshold_change": False,
        },
        "stop_conditions": maximum["stop_conditions"],
        "production_approved": False,
    }
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    markdown.write_text(
        "# r96 weights-only subzone declaration\n\n"
        "Declared before any model edit from the exact frozen r95 skinning dump.\n\n"
        f"- Scope: {record['vertex_count_total']} vertices ({record['pair_count']} exact mirror pairs)\n"
        f"- Seeds: {selection['seed_pair_count']} pairs at incident deform-weight L1 >= {GRADIENT_THRESHOLD}\n"
        f"- Safe eligible ceiling: {selection['eligible_pair_count']} pairs; {selection['excluded_forbidden_pair_count']} pairs excluded for existing non-permitted influences\n"
        "- Solver boundary: non-permitted bone columns fixed exactly; correctives disabled; no topology change\n"
        "- Production approval remains false\n",
        encoding="utf-8",
    )
    print("R96 WEIGHT SUBZONE DECLARED", out, record["vertex_count_total"], "vertices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
