"""Fresh-process measurements for R34; compare saved files, never mutate them."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit")]
import build_original_movement_benchmarks_blender as bench
import build_functional_shoulder_correction_blender as correction
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
import build_original_sculpt_corrective_blender as sculpt
BODY = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
CAND = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates"
R33 = CAND / "claude_review_r33_20261016/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R33_CLAUDE.blend"
def array_key(kb):
    out = np.empty(len(kb.data) * 3)
    kb.data.foreach_get("co", out)
    return out
def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects[BODY]
    rig = body.find_armature()
    keys = body.data.shape_keys.key_blocks
    h = lambda a: hashlib.sha256(a).hexdigest()
    return {
        "bones": [(b.name, b.parent.name if b.parent else None, b.use_deform,
                   [float(x) for row in b.matrix_local for x in row]) for b in rig.data.bones],
        "basis": h(array_key(keys[0]).tobytes()),
        "polygons": h(json.dumps([list(p.vertices) for p in body.data.polygons]).encode()),
        "weights": h(json.dumps([[g.name for g in body.vertex_groups],
                    [[(e.group, e.weight) for e in v.groups] for v in body.data.vertices]]).encode()),
        "non_s7": {k.name: h(array_key(k).tobytes()) for k in keys if not k.name.startswith("HGPT_S7_DELT_")},
    }
args = sys.argv[sys.argv.index("--") + 1:]
mode, source, dest = args[0], Path(args[1]), Path(args[2])
dest.parent.mkdir(parents=True, exist_ok=True)
if mode == "identity":
    a, b = snapshot(R33), snapshot(source)
    report = {key: a[key] == b[key] for key in a}
    dest.write_text(json.dumps(report, indent=2) + "\n")
    assert all(report.values()), report
    print("R34_IDENTITY", json.dumps(report), flush=True)
    raise SystemExit(0)
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
if mode == "benchmarks":
    # No px.install(): this is the standard 13-movement benchmark path,
    # in a clean process, with no full-press extension hook inherited.
    report = bench.run(setup=drives.setup,
                       post_pose=lambda r: drives.drive(r["runtime"], r["body"]))
    dest.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print("BENCHMARK_WORST", source.name, json.dumps({k: v["worst"] for k, v in report["benchmarks"].items()}), flush=True)
elif mode == "press":
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0
    drives.setup(res)
    px.install()
    bench._reset(rig)
    v0, faces = bench._evaluated(body)
    floor = min(v.z for v in v0)
    dom = bench.dominant_groups(body)
    rows = []
    for i in range(41):
        bench._reset(rig)
        state = px.pose_press_full(res, i / 40)
        drives.drive(rig, body)
        vertices, _ = bench._evaluated(body)
        m = bench.frame_metrics(v0, vertices, faces, dom, floor)
        rows.append({"t": i / 40, "ht": state["humerothoracic_elevation"],
                     "collapse": m["collapse_lt_0_1"], "pairs": m["self_intersecting_pairs"],
                     "stretch": m["stretch_gt_2"], "volume_pct": m["body_volume_change_pct"]})
    fit = {}
    with np.load(CAND / "claude_review_r33_20261016/stages/r33_targets.npz") as z:
        for ht in (120.0, 145.0, 156.0, 166.0):
            bench._reset(rig)
            sculpt.press_pose(res, ht)
            drives.drive(rig, body)
            vertices, _ = bench._evaluated(body)
            p = np.array([tuple(v) for v in vertices])
            err = np.linalg.norm(p - z[str(ht)], axis=1) * 1000
            fit[str(ht)] = {"max_mm": float(err.max()), "p99_mm": float(np.percentile(err, 99)),
                            "v18633_mm": float(err[18633]), "over_5mm": int((err > 5).sum())}
    report = {"press": rows, "fit": fit}
    dest.write_text(json.dumps(report, indent=2) + "\n")
    print("FULL_PRESS", source.name, json.dumps(report), flush=True)
else:
    raise ValueError(mode)
