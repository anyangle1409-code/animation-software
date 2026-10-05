"""Declare the post-topology r96 weight zone before changing its weights."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASE_DECLARATION = ROOT / "ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/r96_weight_subzone_declared_before_edit.json"
TOPOLOGY_RECEIPT = ROOT / "ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/r96_topology_intermediate_receipt.json"
DEFAULT_OUT = BASE_DECLARATION.with_name("r96_topology_weight_subzone_declared_before_edit.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dump")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()
    dump_path = Path(args.dump).resolve()
    out = Path(args.out).resolve()
    markdown = out.with_name("TOPOLOGY_WEIGHT_SUBZONE_DECLARATION.md")
    if out.exists() or markdown.exists():
        raise SystemExit("refusing to overwrite the topology weight declaration")

    base = json.loads(BASE_DECLARATION.read_text(encoding="utf-8-sig"))
    topology = json.loads(TOPOLOGY_RECEIPT.read_text(encoding="utf-8-sig"))
    dump = np.load(dump_path)
    parent_sha = str(dump["source_sha256"].item())
    if parent_sha != topology["candidate_sha256"]:
        raise SystemExit("topology dump and receipt identity mismatch")
    weights = dump["W"]
    rest = dump["rest"]
    bones = [str(item) for item in dump["bones"]]
    permitted_bones = set(base["permitted_bones"])
    forbidden_columns = [index for index, bone in enumerate(bones) if bone not in permitted_bones]
    old_left = [int(item) for item in base["left_owned_vertex_ids"]]
    old_right = [int(item) for item in base["mirror_of_strict_left_vertex_ids"]]
    old_zone = set(old_left) | set(old_right)

    candidate_new = set()
    for row in topology["new_vertex_source_edges"]:
        vertex = int(row["new_vertex_id"])
        endpoints = {int(item) for item in row["endpoint_vertex_ids"]}
        if not endpoints & old_zone:
            continue
        if np.any(weights[vertex, forbidden_columns] > 1e-8):
            continue
        candidate_new.add(vertex)
    key = {tuple(np.round(rest[index], 5)): index for index in range(len(rest))}
    mirror = {
        index: int(key[tuple(np.round(rest[index] * (-1, 1, 1), 5))])
        for index in candidate_new
    }
    new_left = sorted(index for index in candidate_new if rest[index, 0] < -1e-8)
    new_right = [mirror[index] for index in new_left]
    if set(new_right) != {index for index in candidate_new if rest[index, 0] > 1e-8}:
        raise SystemExit("new topology weight vertices are not strict mirror closed")
    left = old_left + new_left
    right = old_right + new_right
    if len(left) != len(right) or len(set(left + right)) != len(left) + len(right):
        raise SystemExit("combined topology weight zone is not disjoint and mirror closed")

    record = {
        "schema_version": 1,
        "declared_utc": datetime.now(timezone.utc).isoformat(),
        "declared_before_edit": True,
        "target_revision": "r96",
        "parent": {
            "stage": "r96 declared support topology intermediate",
            "candidate_path": "work/r96/candidates/r96_topology.blend",
            "sha256": parent_sha,
            "lineage_parent_r95_sha256": topology["source_sha256"],
        },
        "topology_receipt": TOPOLOGY_RECEIPT.relative_to(ROOT).as_posix(),
        "topology_receipt_sha256": digest(TOPOLOGY_RECEIPT),
        "base_weight_declaration": BASE_DECLARATION.relative_to(ROOT).as_posix(),
        "base_weight_declaration_sha256": digest(BASE_DECLARATION),
        "zone_rule": "the 440 pre-topology declared vertices plus new support-ring vertices that touch that zone and carry only permitted deform bones; strict mirror pairs only",
        "left_owned_vertex_ids": left,
        "mirror_of_strict_left_vertex_ids": right,
        "mirror_pairs": [[a, b] for a, b in zip(left, right)],
        "base_vertex_count": len(old_left) + len(old_right),
        "new_support_vertex_ids": new_left + new_right,
        "new_support_pair_count": len(new_left),
        "vertex_count_total": len(left) + len(right),
        "pair_count": len(left),
        "permitted_bones": base["permitted_bones"],
        "allowed_change": "normalized mirror-symmetric deform weights on exactly these vertices; no topology, rest geometry, shape-key, rig, baseline, threshold, or other-vertex change",
        "maximum_influences": 4,
        "correctives_disabled_during_gate": True,
        "stop_conditions": ["parent_identity_mismatch", "out_of_scope_edit", "critical_or_high_defect", "material_regression"],
        "production_approved": False,
    }
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    markdown.write_text(
        "# r96 post-topology weight-zone declaration\n\n"
        "Declared after the support topology was audited and before any weight change on that topology parent.\n\n"
        f"- Exact topology parent SHA-256: `{parent_sha}`\n"
        f"- Scope: {record['vertex_count_total']} vertices / {record['pair_count']} mirror pairs\n"
        f"- Added support degrees of freedom: {record['new_support_pair_count']} mirror pairs\n"
        "- Correctives disabled during the gate; production approval remains false\n",
        encoding="utf-8",
    )
    print("R96 TOPOLOGY WEIGHT ZONE DECLARED", out, record["vertex_count_total"], "vertices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
