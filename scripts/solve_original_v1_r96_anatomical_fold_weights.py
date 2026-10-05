"""Create one declared anatomy-led r96 axillary fold weight probe."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
import sys
sys.path.insert(0, str(SCRIPT.parent))
from original_v1_shoulder_yoke_probe import (  # noqa: E402
    limit_influences,
    symmetrise_pairs,
    transfer_trunk_to_anatomical_folds,
    validate_probe_parent,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dump", type=Path)
    parser.add_argument("declaration", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--fraction", type=float, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.with_suffix(".json").exists():
        raise SystemExit("refusing to overwrite an anatomical fold probe")
    dump = np.load(args.dump)
    declaration = json.loads(args.declaration.read_text(encoding="utf-8-sig"))
    source_sha = str(dump["source_sha256"].item())
    if not validate_probe_parent(source_sha, declaration.get("parent", {})):
        raise SystemExit("exact declared topology parent is required")
    if args.fraction not in [float(value) for value in declaration["probe_transfer_fractions"]]:
        raise SystemExit("fraction is outside the declared probe family")

    weights = np.asarray(dump["W"], dtype=float)
    rest = np.asarray(dump["rest"], dtype=float)
    bones = [str(value) for value in dump["bones"]]
    left = [int(value) for value in declaration["left_owned_vertex_ids"]]
    right = [int(value) for value in declaration["mirror_of_strict_left_vertex_ids"]]
    pairs = list(zip(left, right))
    if len(pairs) != declaration["pair_count"] or len(left) + len(right) != declaration["vertex_count_total"]:
        raise SystemExit("declared fold patch is incomplete")
    bone_index = {name: index for index, name in enumerate(bones)}
    solved = transfer_trunk_to_anatomical_folds(
        weights,
        rest,
        pairs,
        spine_indices=(bone_index["spine_02"], bone_index["spine_03"]),
        left_targets={
            "upperarm": bone_index["upperarm_l"],
            "clavicle": bone_index["clavicle_l"],
            "scapula": bone_index["scapula_l"],
        },
        right_targets={
            "upperarm": bone_index["upperarm_r"],
            "clavicle": bone_index["clavicle_r"],
            "scapula": bone_index["scapula_r"],
        },
        fraction=args.fraction,
        front_back_split_y=float(declaration["anatomical_rule"]["front_back_split_y_m"]),
    )
    swap = []
    for name in bones:
        mirror = name[:-2] + ("_r" if name.endswith("_l") else "_l") if name.endswith(("_l", "_r")) else name
        swap.append(bone_index[mirror])
    solved = symmetrise_pairs(solved, left, right, swap)
    solved = limit_influences(solved, left, maximum=int(declaration["maximum_influences"]))
    solved[right] = solved[left][:, swap]

    zone = left + right
    outside = np.ones(len(weights), dtype=bool)
    outside[zone] = False
    outside_change = float(np.abs(solved[outside] - weights[outside]).max())
    mirror_error = float(np.abs(solved[left] - solved[right][:, swap]).max())
    normalisation_error = float(np.abs(solved[zone].sum(axis=1) - 1.0).max())
    influence_max = int((solved[zone] > 1.0e-6).sum(axis=1).max())
    if outside_change != 0.0 or mirror_error > 1.0e-12 or normalisation_error > 1.0e-9 or influence_max > 4:
        raise SystemExit("anatomical fold solution violated its declared boundary")

    np.savez_compressed(
        args.out,
        vertices=np.asarray(zone, dtype=np.int64),
        bones=np.asarray(bones),
        weights=solved[zone],
    )
    receipt = {
        "schema_version": 1,
        "probe_only": True,
        "production_approved": False,
        "source_sha256": source_sha,
        "declaration": args.declaration.resolve().relative_to(ROOT).as_posix(),
        "declaration_sha256": digest(args.declaration),
        "fraction": args.fraction,
        "zone_vertex_count": len(zone),
        "maximum_weight_change": float(np.abs(solved[zone] - weights[zone]).max()),
        "mean_weight_l1_change": float(np.abs(solved[zone] - weights[zone]).sum(axis=1).mean()),
        "outside_zone_max_change": outside_change,
        "mirror_max_error": mirror_error,
        "maximum_influences": influence_max,
        "normalisation_max_error": normalisation_error,
        "correctives_disabled_during_gate": True,
    }
    args.out.with_suffix(".json").write_bytes((json.dumps(receipt, indent=2) + "\n").encode("utf-8"))
    print("R96 ANATOMICAL FOLD PROBE", json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
