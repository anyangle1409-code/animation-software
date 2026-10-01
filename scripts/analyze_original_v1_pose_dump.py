#!/usr/bin/env python3
"""Analyse exact deformation-edge extremes from an ORIGINAL-v1 pose dump.

The dump is produced by dump_original_v1_o4_pose_skinning_blender.py. This
script is Blender-free and read-only. It reports the actual mesh edges behind
the remaining push-up and lunge regional extremes so the next Blender edit can
stay local instead of reopening broad weight zones.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

DEFAULT_TARGETS = (
    ("pushup_bottom", "hand", "max"),
    ("lunge", "pelvis", "max"),
    ("lunge", "torso", "min"),
    ("lunge", "torso", "max"),
)


def top_weights(W, bones, vertex):
    row = W[vertex]
    order = np.argsort(-row)
    return [
        {"bone": bones[int(i)], "weight": round(float(row[int(i)]), 6)}
        for i in order[:4]
        if row[int(i)] > 1e-8
    ]


def vec(x):
    return [round(float(v), 6) for v in x]


def parse_target(value):
    parts = value.split(":")
    if len(parts) != 3 or parts[2] not in {"min", "max"}:
        raise argparse.ArgumentTypeError("target must be pose:region:min or pose:region:max")
    return tuple(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump", type=Path)
    ap.add_argument("--target", action="append", type=parse_target)
    ap.add_argument("--count", type=int, default=12)
    ap.add_argument("--json-out", type=Path, required=True)
    ap.add_argument("--markdown-out", type=Path, required=True)
    args = ap.parse_args()

    d = np.load(args.dump)
    W = d["W"]
    rest = d["rest"]
    edges = d["edges"]
    region = d["region"]
    regions = [str(x) for x in d["region_names"]]
    bones = [str(x) for x in d["bones"]]
    evaluated = d["evaluated"]
    poses = [str(x) for x in d["poses"]]
    source = str(d["source"].item()) if d["source"].shape == () else str(d["source"])
    source_sha256 = str(d["source_sha256"].item()) if "source_sha256" in d else None

    pose_index = {n: i for i, n in enumerate(poses)}
    region_index = {n: i for i, n in enumerate(regions)}
    rest_len = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
    edge_region = region[edges[:, 0]]

    rest_key = {tuple(np.round(p, 5)): i for i, p in enumerate(rest)}
    mirror_vertex = {
        i: rest_key.get(tuple(np.round(np.array([-p[0], p[1], p[2]]), 5)))
        for i, p in enumerate(rest)
    }
    edge_lookup = {tuple(sorted(map(int, e))): i for i, e in enumerate(edges)}

    result = {
        "schema_version": 1,
        "source_dump": str(args.dump),
        "source_candidate": source,
        "source_candidate_sha256": source_sha256,
        "purpose": "read-only exact-edge diagnostics for remaining ORIGINAL-v1 blockers",
        "targets": [],
    }

    for pose_name, region_name, direction in (args.target or list(DEFAULT_TARGETS)):
        if pose_name not in pose_index:
            raise SystemExit("pose not present in dump: " + pose_name)
        if region_name not in region_index:
            raise SystemExit("region not present in dump: " + region_name)

        p = pose_index[pose_name]
        rid = region_index[region_name]
        posed = evaluated[p]
        posed_len = np.linalg.norm(posed[edges[:, 0]] - posed[edges[:, 1]], axis=1)
        ratio = posed_len / np.maximum(rest_len, 1e-12)
        candidates = np.nonzero(edge_region == rid)[0]
        order = candidates[np.argsort(ratio[candidates])]
        if direction == "max":
            order = order[::-1]
        order = order[: max(1, args.count)]

        rows = []
        for rank, ei in enumerate(order, 1):
            a, b = map(int, edges[ei])
            ma, mb = mirror_vertex.get(a), mirror_vertex.get(b)
            mei = None
            mratio = None
            if ma is not None and mb is not None:
                mei = edge_lookup.get(tuple(sorted((ma, mb))))
                if mei is not None:
                    mratio = float(ratio[mei])
            rows.append({
                "rank": rank,
                "edge_index": int(ei),
                "vertices": [a, b],
                "ratio": round(float(ratio[ei]), 6),
                "rest_length_m": round(float(rest_len[ei]), 8),
                "posed_length_m": round(float(posed_len[ei]), 8),
                "rest_midpoint": vec((rest[a] + rest[b]) * 0.5),
                "posed_midpoint": vec((posed[a] + posed[b]) * 0.5),
                "vertex_a_weights": top_weights(W, bones, a),
                "vertex_b_weights": top_weights(W, bones, b),
                "mirror_edge_index": None if mei is None else int(mei),
                "mirror_ratio": None if mratio is None else round(mratio, 6),
            })

        result["targets"].append({
            "pose": pose_name,
            "region": region_name,
            "direction": direction,
            "edge_count_in_region": int(len(candidates)),
            "extreme_ratio": rows[0]["ratio"],
            "edges": rows,
        })

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    md = [
        "# ORIGINAL v1 remaining deformation edge probe",
        "",
        "- Candidate: " + source,
        "- Candidate SHA-256: " + (source_sha256 or "unavailable in legacy dump"),
        "- Read-only diagnostic; no mesh, weights, gates or baseline changed.",
        "",
    ]
    for t in result["targets"]:
        md += [
            "## " + t["pose"] + " / " + t["region"] + " / " + t["direction"],
            "",
            "Extreme ratio: **" + str(t["extreme_ratio"]) + "**",
            "",
            "| Rank | Edge | Ratio | Rest midpoint (m) | A top weights | B top weights | Mirror ratio |",
            "|---:|---:|---:|---|---|---|---:|",
        ]
        for e in t["edges"]:
            wa = ", ".join(x["bone"] + " " + format(x["weight"], ".3f") for x in e["vertex_a_weights"])
            wb = ", ".join(x["bone"] + " " + format(x["weight"], ".3f") for x in e["vertex_b_weights"])
            mp = ", ".join(format(x, ".4f") for x in e["rest_midpoint"])
            mr = "-" if e["mirror_ratio"] is None else format(e["mirror_ratio"], ".3f")
            md.append("| {0} | {1} | {2:.3f} | {3} | {4} | {5} | {6} |".format(
                e["rank"], e["edge_index"], e["ratio"], mp, wa, wb, mr))
        md.append("")

    args.markdown_out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("EDGE PROBE:", len(result["targets"]), "targets ->", args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
