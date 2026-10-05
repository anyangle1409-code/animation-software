"""Create a constrained weights-only r96 probe solution from the frozen dump."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
sys.path.insert(0, str(SCRIPT.parent))
from original_v1_shoulder_yoke_declaration import R95_SHA256  # noqa: E402
from original_v1_shoulder_yoke_probe import (  # noqa: E402
    diffuse_permitted_weights,
    limit_influences,
    symmetrise_pairs,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dump")
    parser.add_argument("declaration")
    parser.add_argument("out")
    parser.add_argument("--iters", type=int, required=True)
    parser.add_argument("--lam", type=float, required=True)
    cli = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None
    args = parser.parse_args(cli)

    dump_path = Path(args.dump).resolve()
    declaration_path = Path(args.declaration).resolve()
    out = Path(args.out).resolve()
    receipt = out.with_suffix(".json")
    if out.exists() or receipt.exists():
        raise SystemExit("refusing to overwrite an existing r96 weight probe")
    declaration = json.loads(declaration_path.read_text(encoding="utf-8-sig"))
    dump = np.load(dump_path)
    if str(dump["source_sha256"].item()) != R95_SHA256:
        raise SystemExit("exact frozen r95 skinning dump required")
    if declaration.get("parent", {}).get("sha256") != R95_SHA256 or declaration.get("target_revision") != "r96":
        raise SystemExit("exact r96 weight subzone declaration required")

    weights = np.asarray(dump["W"], dtype=float)
    rest = np.asarray(dump["rest"], dtype=float)
    edges = np.asarray(dump["edges"], dtype=np.int64)
    bones = [str(item) for item in dump["bones"]]
    left = [int(item) for item in declaration["left_owned_vertex_ids"]]
    right = [int(item) for item in declaration["mirror_of_strict_left_vertex_ids"]]
    zone = left + right
    if declaration.get("vertex_count_total") != len(zone) or len(left) != len(right):
        raise SystemExit("weight subzone is not complete and mirror closed")
    permitted = [bones.index(name) for name in declaration["permitted_bones"]]
    swap = []
    for name in bones:
        mirror_name = name[:-2] + ("_r" if name.endswith("_l") else "_l") if name.endswith(("_l", "_r")) else name
        swap.append(bones.index(mirror_name))

    edge_weights = 1.0 / np.maximum(np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1), 1e-6)
    solved = diffuse_permitted_weights(
        weights, edges, zone, permitted, args.iters, args.lam, edge_weights=edge_weights
    )
    solved = symmetrise_pairs(solved, left, right, swap)
    solved = limit_influences(solved, left, maximum=4)
    solved[right] = solved[left][:, swap]

    outside = np.ones(len(weights), dtype=bool)
    outside[zone] = False
    permitted_mask = np.zeros(weights.shape[1], dtype=bool)
    permitted_mask[permitted] = True
    outside_change = float(np.abs(solved[outside] - weights[outside]).max())
    forbidden_change = float(np.abs(solved[zone][:, ~permitted_mask] - weights[zone][:, ~permitted_mask]).max())
    mirror_error = float(np.abs(solved[left] - solved[right][:, swap]).max())
    influence_max = int((solved[zone] > 1e-6).sum(axis=1).max())
    normalisation_error = float(np.abs(solved[zone].sum(axis=1) - 1.0).max())
    if outside_change != 0.0 or forbidden_change != 0.0 or mirror_error > 1e-12:
        raise SystemExit("r96 probe escaped its declared weight boundary")
    if influence_max > 4 or normalisation_error > 1e-9:
        raise SystemExit("r96 probe violates normalized four-influence weights")

    output_weights = solved[zone]
    np.savez_compressed(
        out,
        vertices=np.asarray(zone, dtype=np.int64),
        bones=np.asarray(bones),
        weights=output_weights,
    )
    record = {
        "schema_version": 1,
        "probe_only": True,
        "production_approved": False,
        "source_revision": "r95",
        "source_sha256": R95_SHA256,
        "dump_sha256": digest(dump_path),
        "declaration": declaration_path.relative_to(ROOT).as_posix(),
        "declaration_sha256": digest(declaration_path),
        "iterations": args.iters,
        "lambda": args.lam,
        "zone_vertex_count": len(zone),
        "maximum_weight_change": float(np.abs(output_weights - weights[zone]).max()),
        "mean_weight_l1_change": float(np.abs(output_weights - weights[zone]).sum(axis=1).mean()),
        "outside_zone_max_change": outside_change,
        "non_permitted_column_max_change": forbidden_change,
        "mirror_max_error": mirror_error,
        "maximum_influences": influence_max,
        "normalisation_max_error": normalisation_error,
        "correctives_disabled_during_gate": True,
    }
    receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("R96 WEIGHT PROBE", json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
