#!/usr/bin/env python3
"""Summarise the V14 investigation diagnostics (plain Python, no Blender).

usage: python3 summarize.py <dir with refine_*.json and cut_*.json> <out dir>

Verdicts:
  R1  refine() in Python-set order gives different triangulations in separate processes on identical input
  R2  refine() with index-sorted element lists gives identical triangulations
  C1  the cut replayed on a W8 file reproduces the archived V14 cut (699 / 696 loops, 92,664 old vertices removed)
  C2  the leg-step identity  final = W8 - removed + loops + rings + feet  explains each V14 total
"""
import json
import sys
from pathlib import Path

ARCH_V14 = {"final": 238067, "loop_r": 699, "loop_l": 696}
RECON_V14 = {"final": 238065, "loop_r": 700, "loop_l": 696}
RINGS_AND_FEET = 168 * 165 + 168 * 166 + 2 * 26877      # identical in both reports (legs_v2_report.json)
W8_VERTS = 219974


def main():
    d, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    ref = {p.stem: json.loads(p.read_text()) for p in sorted(d.rglob("*refine_*.json"))}
    cut = {p.stem: json.loads(p.read_text()) for p in sorted(d.rglob("*cut_*.json"))}
    res = {"refine_runs": {k: {"mode": v["mode"], "beautify_geom": v["refine_report"]["beautify_geom"],
                               "sha256_triangles_geometric": v["sha256_triangles_geometric"],
                               "sha256_vertex_positions_as_set": v["sha256_vertex_positions_as_set"]} for k, v in ref.items()},
           "cut_runs": {k: {"input_sha256": v["input_sha256"], "zc_m": v["zc_m"], "stature_m": v["stature_m"],
                            **{f"{s}_{f}": v["sides"][s][f] for s in ("r", "l") for f in
                               ("cut_loop_boundary_vertices", "old_vertices_removed", "sha256_band_vertex_positions", "sha256_band_triangles")}}
                        for k, v in cut.items()},
           "verdicts": {}}
    uns = [v for v in ref.values() if v["mode"].startswith("python-set")]; srt = [v for v in ref.values() if v["mode"] == "sorted"]
    pat = [v for v in ref.values() if "patch" in v["mode"]]
    V = res["verdicts"]
    if pat:
        V["R3_candidate_patch_deterministic_and_equal_to_sorted"] = len({v["sha256_triangles_geometric"] for v in pat + srt}) == 1
    if len(uns) >= 2:
        V["R1_set_order_nondeterministic"] = len({v["sha256_triangles_geometric"] for v in uns}) > 1 and \
            len({v["sha256_vertex_positions_as_set"] for v in uns}) == 1
    if len(srt) >= 2:
        V["R2_sorted_deterministic"] = len({v["sha256_triangles_geometric"] for v in srt}) == 1
    for k, v in cut.items():
        rem = v["sides"]["r"]["old_vertices_removed"] + v["sides"]["l"]["old_vertices_removed"]
        loops = v["sides"]["r"]["cut_loop_boundary_vertices"] + v["sides"]["l"]["cut_loop_boundary_vertices"]
        V[f"C2_{k}_predicted_V14_total"] = W8_VERTS - rem + loops + RINGS_AND_FEET
        V[f"C1_{k}_matches_archive_cut"] = (v["sides"]["r"]["cut_loop_boundary_vertices"], v["sides"]["l"]["cut_loop_boundary_vertices"], rem) == (699, 696, 92664)
    (out / "v14_investigation_summary.json").write_text(json.dumps(res, indent=1))
    lines = ["# V14 investigation summary", "", "| verdict | value |", "|---|---|"] + [f"| {k} | {v} |" for k, v in V.items()]
    (out / "v14_investigation_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
