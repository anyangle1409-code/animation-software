#!/usr/bin/env python3
"""Compare a replayed W8 / V14 with the preserved L0 build and the archived V14 report (plain Python + numpy).

usage: python3 compare_replay.py <repo root> <replayed W8 dir> <replayed V14 dir> <cut json of replayed W8> <out.json>
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


def num_close(a, b, rel=1e-9, abs_=1e-12):
    if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return a == b
    return abs(a - b) <= abs_ + rel * abs(a)


def main():
    repo, w8, v14, cutf, out = (Path(a) for a in sys.argv[1:6])
    ev = repo / "scripts/v14_investigation/evidence"
    pre = np.load(ev / "build_L0/refined_mesh_and_offsets.npz")
    R = {}
    R["W8_rest_identical"] = bool(np.array_equal(np.load(w8 / "rest.npy"), pre["rest"]))
    R["W8_tris_identical"] = bool(np.array_equal(np.load(w8 / "tris.npy"), pre["tris"]))
    o = np.load(w8 / "body_v2_offsets.npz")
    for k in ("offsets", "proportion"):
        R[f"W8_{k}_max_dev_mm"] = float(np.abs(pre[k] - o[k]).max() * 1000)
    a = dict(leaves(json.loads((ev / "build_L0/body_v2_report.json").read_text())))
    b = dict(leaves(json.loads((w8 / "body_v2_report.json").read_text())))
    R["W8_report_leaves_differing"] = [k for k in a if not num_close(a[k], b.get(k))]
    a = dict(leaves(json.loads((ev / "build_L0/skeleton_edits.json").read_text())))
    b = dict(leaves(json.loads((w8 / "skeleton_edits.json").read_text())))
    R["W8_skeleton_edit_leaves_differing_beyond_1e-12_rel"] = [k for k in a if not num_close(a[k], b.get(k))]
    c0 = json.loads((ev / "local_cut_L0_archiveV14input.json").read_text()); c1 = json.loads(cutf.read_text())
    R["cut_fingerprints_identical_to_L0"] = all(c0["sides"][s][k] == c1["sides"][s][k] for s in "rl" for k in c0["sides"][s])
    a = dict(leaves(json.loads((repo / "review-assets/body_v2/draft_v14b_torso/legs_v2_report.json").read_text())))
    b = dict(leaves(json.loads((v14 / "legs_v2_report.json").read_text())))
    R["V14_report_leaves_vs_archive"] = len(a)
    R["V14_report_leaves_differing_from_archive"] = [(k, a[k], b.get(k)) for k in a if not num_close(a[k], b.get(k))]
    R["V14_vertices"] = b.get("/verts_before_after[1]")
    R["PASS_exact_archived_V14_reproduced"] = (R["W8_rest_identical"] and R["W8_tris_identical"] and R["W8_offsets_max_dev_mm"] < 0.01
                                               and R["cut_fingerprints_identical_to_L0"] and not R["V14_report_leaves_differing_from_archive"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(R, indent=1))
    print(json.dumps(R, indent=1))
    return 0 if R["PASS_exact_archived_V14_reproduced"] else 1


if __name__ == "__main__":
    sys.exit(main())
