#!/usr/bin/env python3
"""Compare a replayed W8 (replay_build_blender.py with evidence/build_w8) with the archived v13s / w8 files in
review-assets/body_v2/draft_v13s_standing - the same checks as the workbench's compare_rebuild_to_archive.py
(skeleton edits, every numeric report leaf, offsets / proportion within 0.01 mm) plus triangulation identity.

usage: python3 compare_w8_replay.py <repo root> <replayed W8 dir> <out.json>
"""
import json
import sys
from pathlib import Path

import numpy as np


def leaves(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f"{p}[{i}]")
    else:
        yield p, x


def main():
    repo, w8, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    arc = repo / "review-assets/body_v2/draft_v13s_standing"
    pre = np.load(repo / "scripts/v14_investigation/evidence/build_w8/refined_mesh_and_offsets.npz")
    R = {"W8_rest_identical_to_preserved": bool(np.array_equal(np.load(w8 / "rest.npy"), pre["rest"])),
         "W8_tris_identical_to_preserved": bool(np.array_equal(np.load(w8 / "tris.npy"), pre["tris"]))}
    za, zb = np.load(arc / "body_v2_offsets.npz"), np.load(w8 / "body_v2_offsets.npz")
    for k in ("offsets", "proportion"):
        R[f"{k}_max_dev_mm_vs_archive"] = float(np.abs(za[k] - zb[k]).max() * 1000)
    a, b = dict(leaves(json.loads((arc / "skeleton_edits.json").read_text()))), dict(leaves(json.loads((w8 / "skeleton_edits.json").read_text())))
    R["skeleton_edit_leaves_differing_rel_1e-9"] = [k for k in a if not (a[k] == b.get(k) or (isinstance(a[k], float) and isinstance(b.get(k), float) and abs(a[k] - b[k]) <= 1e-12 + 1e-9 * abs(a[k])))]
    ra, rb = dict(leaves(json.loads((arc / "body_v2_report.json").read_text()))), dict(leaves(json.loads((w8 / "body_v2_report.json").read_text())))
    R["report_numeric_leaves"] = len(ra)
    R["report_leaves_differing_rel_1e-4"] = [(k, ra[k], rb.get(k)) for k in ra if (isinstance(ra[k], (int, float)) and not isinstance(ra[k], bool))
                                             and not (k in rb and isinstance(rb[k], (int, float)) and abs(ra[k] - rb[k]) <= 1e-6 + 1e-4 * abs(ra[k]))]
    R["PASS_archived_w8_reproduced"] = (R["W8_rest_identical_to_preserved"] and R["W8_tris_identical_to_preserved"]
                                        and R["offsets_max_dev_mm_vs_archive"] <= 0.01 and R["proportion_max_dev_mm_vs_archive"] <= 0.01
                                        and not R["skeleton_edit_leaves_differing_rel_1e-9"]
                                        and all(k.startswith("/refine/beautify_geom") for k, _, _ in R["report_leaves_differing_rel_1e-4"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(R, indent=1)); print(json.dumps(R, indent=1))
    return 0 if R["PASS_archived_w8_reproduced"] else 1


if __name__ == "__main__":
    sys.exit(main())
