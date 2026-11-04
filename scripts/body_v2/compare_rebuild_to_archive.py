#!/usr/bin/env python3
"""Compare the outputs of a W8 rebuild with the archived reports (plain Python + numpy, no Blender).

usage: python3 compare_rebuild_to_archive.py <repo_root> <rebuild_out_W8_dir> <out.json>

Compares, from <rebuild_out_W8_dir>: skeleton_edits.json (exact), body_v2_report.json (every numeric leaf),
body_v2_offsets.npz (array equality with tolerance).  Prints PASS/FAIL per item; exit 1 on any FAIL.
STATUS: executed only against the archive itself (self-comparison) in the session that wrote it.
"""
import json
import sys
from pathlib import Path

import numpy as np


def leaves(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from leaves(v, f"{p}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from leaves(v, f"{p}[{i}]")
    else:
        yield p, o


def main():
    repo, new, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    old = repo / "review-assets/body_v2/draft_v13s_standing"
    res = []

    def add(name, ok, detail):
        res.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail}); print("PASS" if ok else "FAIL", name, detail)

    a, b = json.loads((old / "skeleton_edits.json").read_text()), json.loads((new / "skeleton_edits.json").read_text())
    add("skeleton_edits.json identical", a == b, "equal" if a == b else "differs")

    ra, rb = dict(leaves(json.loads((old / "body_v2_report.json").read_text()))), dict(leaves(json.loads((new / "body_v2_report.json").read_text())))
    bad = [(k, ra[k], rb.get(k)) for k in ra if (isinstance(ra[k], (int, float)) and not isinstance(ra[k], bool))
           and not (k in rb and isinstance(rb[k], (int, float)) and abs(ra[k] - rb[k]) <= 1e-6 + 1e-4 * abs(ra[k]))]
    add("body_v2_report.json numeric leaves match (rel 1e-4)", not bad, f"{len(ra)} leaves; mismatches: {bad[:5]}")

    za, zb = np.load(old / "body_v2_offsets.npz"), np.load(new / "body_v2_offsets.npz")
    for k in ("offsets", "proportion"):
        same_shape = za[k].shape == zb[k].shape
        dev = float(np.abs(za[k] - zb[k]).max() * 1000) if same_shape else None
        add(f"offsets.npz[{k}] max deviation <= 0.01 mm", same_shape and dev <= 0.01, {"shape": [za[k].shape, zb[k].shape], "max_dev_mm": dev})

    out.parent.mkdir(parents=True, exist_ok=True)
    s = {"pass": sum(r["result"] == "PASS" for r in res), "fail": sum(r["result"] == "FAIL" for r in res)}
    out.write_text(json.dumps({"checks": res, "summary": s}, indent=1))
    print("SUMMARY", s)
    return 1 if s["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
