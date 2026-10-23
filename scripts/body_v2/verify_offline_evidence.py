#!/usr/bin/env python3
"""Offline (no Blender) consistency check of the archived Body v2 evidence.

Runs with plain Python 3 + numpy.  It does NOT prove a reconstructed .blend is correct; it proves that the archived
evidence in this repository is internally consistent and pinned, and it writes the expected values that
verify_body_v2_blend.py (the Blender-side check) compares a rebuilt file against.

usage: python3 verify_offline_evidence.py <repo_root> <r57src_root> <out.json>
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

R41_REL = "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend"
R41_PINNED = "4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e"   # PR #124 CLAUDE_HANDOFF.md
# Screenshot hashes pinned by PR #124 experiments/anatomical_muscles/CURRENT_W8_VISUAL_QA_20261022.md.
# The image files themselves are not in any repository; they are listed so a holder of the files can check them.
W8_SCREENSHOTS = {
    "full_w8.jpeg": "b9f92d67a2948a5776ccb6375af94058c142017ffb73a548fb243e7613a12438",
    "arm_front.jpeg": "93bac98ed25e79391f37aee2d57fcc9f05070fc7230a1b10eedebdc4f8d33a8d",
    "legs_front.jpeg": "e7405219a10e066529880e63b5bc0d5f84e6545c84a970260b54269d27516d9f",
    "feet_side.jpeg": "6894aeb202655d6d9865cd8e25a4da95b6424ace5f5c6863b6ee0137910acd99",
}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    repo, r57, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3])
    rb = repo / "review-assets/body_v2"
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})

    r41 = r57 / R41_REL
    r41_sha = sha(r41)
    check("R41 input SHA256 equals the hash pinned in PR #124", r41_sha == R41_PINNED, r41_sha)
    check("R41 input size", r41.stat().st_size == 5294269, r41.stat().st_size)

    v13 = json.loads((rb / "draft_v13s_standing/body_v2_report.json").read_text())
    npz = np.load(rb / "draft_v13s_standing/body_v2_offsets.npz")
    nv = v13["refine"]["vertices_after"]
    check("v13s refine: 21,600 -> 219,974 vertices", (v13["refine"]["vertices_before"], nv) == (21600, 219974), (v13["refine"]["vertices_before"], nv))
    check("v13s offsets array rows == refined vertex count", npz["offsets"].shape == (nv, 3) and npz["proportion"].shape == (nv, 3), npz["offsets"].shape)
    check("v13s offsets are finite", bool(np.isfinite(npz["offsets"]).all()), "finite")
    mx = float(np.abs(npz["offsets"]).max()) * 1000
    check("v13s largest offset magnitude plausible (< 200 mm)", mx < 200, f"{mx:.2f} mm")
    check("v13s standing-pose self-intersections v2 == 0", v13["standing_self_intersections"]["v2"] == 0, v13["standing_self_intersections"])
    check("v13s left/right symmetry <= 0.02 mm", v13["symmetry_max_mm"] <= 0.02, v13["symmetry_max_mm"])

    expected = {"v13s_w8": {"body_vertices": nv, "vertex_groups": None, "shape_keys": None}}
    for tag in ("draft_v14a_legs", "draft_v14b_torso"):
        r = json.loads((rb / tag / "legs_v2_report.json").read_text())
        check(f"{tag}: vertex groups 77, shape keys 79", (r["groups"], r["shape_keys"]) == (77, 79), (r["groups"], r["shape_keys"]))
        check(f"{tag}: 219,974 -> 238,067 vertices", r["verts_before_after"] == [219974, 238067], r["verts_before_after"])
        check(f"{tag}: stature 1.8562 m before and after", (r["stature_m"], r["stature_after_m"]) == (1.8562, 1.8562), (r["stature_m"], r["stature_after_m"]))
        check(f"{tag}: new meshes manifold and consistently wound", (r["winding_conflicts"], r["non_manifold_edges_new"]) == (0, 0), (r["winding_conflicts"], r["non_manifold_edges_new"]))
        check(f"{tag}: both feet 26,877 vertices, 289.6 mm", r["foot_r"] == r["foot_l"] and r["foot_r"]["verts"] == 26877, r["foot_r"])
        expected[tag] = {"body_vertices": 238067, "vertex_groups": 77, "shape_keys": 79, "stature_m": 1.8562,
                         "feet_vertices_each": 26877, "foot_length_mm": 289.6, "torso_relief": "torso_relief" in r}
    expected["draft_v14a_legs"]["note"] = "v14a = legs/feet only (no torso relief)"
    expected["draft_v14b_torso"]["note"] = "v14b = v14a + torso relief + hip fill; this is what 'default settings' of legs_v2_blender.py produce"

    sk = rb / "draft_v13s_standing/skeleton_edits.json"
    images = {f"{tag}/{p.name}": sha(p) for tag in ("draft_v13s_standing", "draft_v14a_legs", "draft_v14b_torso")
              for p in sorted((rb / tag).glob("*.jpg"))}
    rep = {
        "r41_input": {"path": R41_REL, "sha256": r41_sha, "bytes": r41.stat().st_size, "commit": "025d5f28fa7eba2064fba565b1c9b60119cdd2cb"},
        "archived_evidence_sha256": {
            "draft_v13s_standing/body_v2_offsets.npz": sha(rb / "draft_v13s_standing/body_v2_offsets.npz"),
            "draft_v13s_standing/body_v2_report.json": sha(rb / "draft_v13s_standing/body_v2_report.json"),
            "draft_v13s_standing/skeleton_edits.json": sha(sk),
            "draft_v14a_legs/legs_v2_report.json": sha(rb / "draft_v14a_legs/legs_v2_report.json"),
            "draft_v14b_torso/legs_v2_report.json": sha(rb / "draft_v14b_torso/legs_v2_report.json"),
        },
        "archived_review_renders_sha256": images,
        "expected_for_blend_check": expected,
        "w8_screenshots_pinned_by_pr124": {k: {"sha256": v, "file_present_in_any_repo": False} for k, v in W8_SCREENSHOTS.items()},
        "checks": checks,
        "summary": {"pass": sum(c["result"] == "PASS" for c in checks), "fail": sum(c["result"] == "FAIL" for c in checks)},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1))
    for c in checks:
        print(f"{c['result']}  {c['check']}  [{c['detail']}]")
    print("SUMMARY", rep["summary"])
    return 1 if rep["summary"]["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
