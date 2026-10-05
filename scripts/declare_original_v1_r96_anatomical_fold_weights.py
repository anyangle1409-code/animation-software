"""Declare the exact mirrored r96 anterior/posterior axillary fold weight patch."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
import sys
sys.path.insert(0, str(SCRIPT.parent))
from original_v1_shoulder_yoke_probe import R95_SHA256, select_anatomical_fold_pairs  # noqa: E402


TOPOLOGY_SHA256 = "6934594dde9140193882c0e293f8b404fb24bed8b1b1b2722267ff97d13844dd"
DUMP = ROOT / "work/r96/r96_topology_arc_skinning.npz"
BASE = ROOT / "ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/r96_topology_weight_subzone_declared_before_edit.json"
OUT = BASE.with_name("r96_anatomical_fold_weights_declared_before_edit.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if OUT.exists():
        raise SystemExit("refusing to overwrite the anatomical fold declaration")
    dump = np.load(DUMP)
    if str(dump["source_sha256"].item()) != TOPOLOGY_SHA256:
        raise SystemExit("exact topology dump is required")
    base = json.loads(BASE.read_text(encoding="utf-8-sig"))
    if base.get("parent", {}).get("sha256") != TOPOLOGY_SHA256:
        raise SystemExit("topology weight declaration has the wrong parent")
    candidate_pairs = [tuple(int(value) for value in pair) for pair in base["mirror_pairs"]]
    pairs = select_anatomical_fold_pairs(np.asarray(dump["rest"], dtype=float), candidate_pairs)
    if len(pairs) != 82:
        raise SystemExit(f"expected 82 exact fold pairs, found {len(pairs)}")
    left = [pair[0] for pair in pairs]
    right = [pair[1] for pair in pairs]
    record = {
        "schema_version": 1,
        "declared_utc": datetime.now(timezone.utc).isoformat(),
        "declared_before_edit": True,
        "target_revision": "r96",
        "parent": {
            "stage": "r96 declared support topology intermediate",
            "candidate_path": "work/r96/candidates/r96_topology.blend",
            "sha256": TOPOLOGY_SHA256,
            "lineage_parent_r95_sha256": R95_SHA256,
        },
        "base_weight_declaration": BASE.relative_to(ROOT).as_posix(),
        "base_weight_declaration_sha256": digest(BASE),
        "source_dump_sha256": digest(DUMP),
        "issues": ["WB-AX-001", "WB-PEC-002", "WB-PEC-003"],
        "anatomical_rule": {
            "front_direction": "negative local Y",
            "anterior_fold_targets": {"upperarm": 0.6, "clavicle": 0.4},
            "posterior_fold_targets": {"upperarm": 0.5, "scapula": 0.5},
            "trunk_sources": ["spine_02", "spine_03"],
            "front_back_split_y_m": 0.015,
        },
        "rest_bounds_m": {
            "absolute_x": [0.13, 0.22],
            "y": [-0.09, 0.06],
            "z": [1.33, 1.47],
        },
        "mirror_pairs": [list(pair) for pair in pairs],
        "left_owned_vertex_ids": left,
        "mirror_of_strict_left_vertex_ids": right,
        "vertex_count_total": len(left) + len(right),
        "pair_count": len(pairs),
        "probe_transfer_fractions": [0.15, 0.30, 0.45],
        "maximum_influences": 4,
        "allowed_change": "transfer only the declared fraction of spine_02/spine_03 weight into the side-specific anatomical fold targets on exactly these vertices; preserve all other weight columns and all other vertices",
        "preserve": ["topology", "rest_geometry", "shape_keys", "rig", "baselines", "thresholds"],
        "correctives_disabled_during_gate": True,
        "stop_conditions": ["critical_or_high_defect", "material_regression", "out_of_scope_edit"],
        "production_approved": False,
    }
    OUT.write_bytes((json.dumps(record, indent=2) + "\n").encode("utf-8"))
    print("R96 ANATOMICAL FOLD WEIGHT DECLARATION", len(pairs), digest(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
