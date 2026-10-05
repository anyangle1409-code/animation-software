"""Localize exact shoulder/axilla edge strain and new folds in a skinning dump."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def _v3(values):
    return [round(float(value), 6) for value in values]


def edge_ratio_rows(rest, posed, edges, zone):
    rest = np.asarray(rest, dtype=float)
    posed = np.asarray(posed, dtype=float)
    edges = np.asarray(edges, dtype=int)
    zone = np.asarray(zone, dtype=bool)
    local = edges[zone[edges].all(axis=1)]
    rest_length = np.linalg.norm(rest[local[:, 1]] - rest[local[:, 0]], axis=1)
    posed_length = np.linalg.norm(posed[local[:, 1]] - posed[local[:, 0]], axis=1)
    ratio = posed_length / np.maximum(rest_length, 1.0e-12)
    order = sorted(range(len(local)), key=lambda i: (-abs(float(np.log(max(ratio[i], 1.0e-12)))), int(local[i, 0]), int(local[i, 1])))
    return [
        {
            "vertices": [int(local[i, 0]), int(local[i, 1])],
            "ratio": round(float(ratio[i]), 6),
            "absolute_log_strain": round(abs(float(np.log(max(ratio[i], 1.0e-12)))), 6),
            "rest_midpoint_m": _v3(0.5 * (rest[local[i, 0]] + rest[local[i, 1]])),
        }
        for i in order
    ]


def _unit_face_normals(points, tris):
    a, b, c = points[tris[:, 0]], points[tris[:, 1]], points[tris[:, 2]]
    normals = np.cross(b - a, c - a)
    return normals / np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1.0e-18)


def dihedral_rows(rest, posed, tris, zone):
    rest = np.asarray(rest, dtype=float)
    posed = np.asarray(posed, dtype=float)
    tris = np.asarray(tris, dtype=int)
    zone = np.asarray(zone, dtype=bool)
    adjacency = {}
    for face_id, tri in enumerate(tris):
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edge = tuple(sorted((int(a), int(b))))
            adjacency.setdefault(edge, []).append(face_id)
    shared = [(edge, faces) for edge, faces in adjacency.items() if len(faces) == 2 and zone[list(edge)].all()]
    rest_normals = _unit_face_normals(rest, tris)
    posed_normals = _unit_face_normals(posed, tris)
    rows = []
    for edge, faces in shared:
        rest_cosine = float(np.dot(rest_normals[faces[0]], rest_normals[faces[1]]))
        posed_cosine = float(np.dot(posed_normals[faces[0]], posed_normals[faces[1]]))
        rows.append({
            "shared_edge": list(edge),
            "faces": [int(faces[0]), int(faces[1])],
            "rest_cosine": round(rest_cosine, 6),
            "posed_cosine": round(posed_cosine, 6),
            "cosine_drop": round(rest_cosine - posed_cosine, 6),
            "rest_midpoint_m": _v3(0.5 * (rest[edge[0]] + rest[edge[1]])),
        })
    return sorted(rows, key=lambda row: (-row["cosine_drop"], row["shared_edge"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dump", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--poses", default="press_top,press_top_rhythm,pullup_hang,pullup_hang_rhythm")
    parser.add_argument("--center", nargs=3, type=float, default=(-0.169, -0.017, 1.403))
    parser.add_argument("--radius", type=float, default=0.085)
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("refusing to overwrite localization evidence")
    dump = np.load(args.dump)
    rest = np.asarray(dump["rest"], dtype=float)
    evaluated = np.asarray(dump["evaluated"], dtype=float)
    pose_names = [str(value) for value in dump["poses"]]
    selected = [value for value in args.poses.split(",") if value]
    missing = sorted(set(selected) - set(pose_names))
    if missing:
        raise SystemExit(f"missing requested poses: {missing}")
    center = np.asarray(args.center, dtype=float)
    left = np.linalg.norm(rest - center, axis=1) <= args.radius
    right_center = center * np.array([-1.0, 1.0, 1.0])
    zone = left | (np.linalg.norm(rest - right_center, axis=1) <= args.radius)
    bones = [str(value) for value in dump["bones"]]
    weights = np.asarray(dump["W"], dtype=float)
    regions = [str(value) for value in dump["region_names"]]
    region = np.asarray(dump["region"], dtype=int)

    pose_rows = []
    implicated = set()
    for pose in selected:
        points = evaluated[pose_names.index(pose)]
        edges = edge_ratio_rows(rest, points, dump["edges"], zone)[: args.limit]
        folds = dihedral_rows(rest, points, dump["tris"], zone)[: args.limit]
        for row in edges:
            implicated.update(row["vertices"])
        for row in folds:
            implicated.update(row["shared_edge"])
        pose_rows.append({"pose": pose, "worst_edges": edges, "new_folds": folds})

    vertex_rows = []
    for vertex in sorted(implicated):
        active = np.flatnonzero(weights[vertex] > 1.0e-6)
        active = sorted(active, key=lambda index: -weights[vertex, index])[:4]
        vertex_rows.append({
            "vertex": int(vertex),
            "rest_position_m": _v3(rest[vertex]),
            "region": regions[int(region[vertex])],
            "weights": [{"bone": bones[index], "weight": round(float(weights[vertex, index]), 6)} for index in active],
        })
    report = {
        "schema_version": 1,
        "source": str(dump["source"].item()),
        "source_sha256": str(dump["source_sha256"].item()),
        "dump_sha256": hashlib.sha256(args.dump.read_bytes()).hexdigest(),
        "correctives_disabled": True,
        "selection": {
            "left_center_m": _v3(center),
            "right_center_m": _v3(right_center),
            "radius_m": args.radius,
            "zone_vertex_count": int(zone.sum()),
            "poses": selected,
            "rows_per_measure_per_pose": args.limit,
        },
        "poses": pose_rows,
        "implicated_vertices": vertex_rows,
        "production_approved": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"out": str(args.out), "zone_vertices": int(zone.sum()), "implicated_vertices": len(implicated)}))


if __name__ == "__main__":
    main()
