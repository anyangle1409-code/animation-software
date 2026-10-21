"""R70: rebuild Work's affine pose model (source.npz) for the new top-of-press path (Claude, 21 Oct 2026).  Review only.

Work's gates require the native Blender skin to equal posed_s = base_s + mat_s @ blend(dense, decode(weight_s)) to 0.01 mm.
The R70 path (r70_press_path.py) changes main-path samples 26..40 (t > 0.625); 0..25, the benchmark path (41..81) and the
front pose are unchanged.  For every main sample this script poses the immutable R41 with all dense increments = 0:
  base_s   = that native skin (S7 baseline included, as in Work's model)
  mat_s    = each vertex's exact linear map from a shape offset to the posed skin (probe key, unit offsets per axis)
  weight_s = Work's coefficients() of the R41 seven-key weights at the sample's elevation
Self-checks: samples 0..25 must reproduce Work's base/mat/weight (they share the old path), else it stops.
  blender --background --python build_r70_source_blender.py -- <R57 root> source.npz out.npz
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np

root, src, dst = sys.argv[sys.argv.index("--") + 1:][:3]
ROOT = Path(root).resolve()
sys.path[:0] = [str(Path(__file__).resolve().parent), str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit")]
os.environ["S7_LOCKOUT_HT"] = "166"
if not os.environ.get("R70_TOP"):
    raise SystemExit("R70_TOP must be set (elevation:elbow:plane)")
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
from original_review_r43_sampling import hats, KEYS, DENSE
from claude_r61_native import install

z = {k: v for k, v in np.load(src).items()}
res = r17._setup(ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend")
rig, body = res["runtime"], res["body"]
install(res, np.zeros((72, len(z["rest"]), 3)), z["sampling_basis"])
bpy.context.view_layer.update()
blocks = body.data.shape_keys.key_blocks
nv = len(z["rest"])
basis_co = np.empty(nv * 3); blocks[0].data.foreach_get("co", basis_co); basis_co = basis_co.reshape(-1, 3)
probe = body.shape_key_add(name="R70_PROBE", from_mix=False)
H = 0.01


def native():
    pp, ff = bench._evaluated(body)
    return np.array([tuple(v) for v in pp])


def weight_at(e):
    # Work's coefficients(): seven-key weights at elevation e -> e -> hats(e, DENSE) @ basis(); basis() needs scipy (not
    # in Blender's Python), so use the identical basis stored in the model (z["sampling_basis"])
    ev = np.full(nv, float(e))
    return (hats(ev, DENSE) @ z["sampling_basis"]).T


report = {"top": os.environ["R70_TOP"], "samples": []}
for s in range(41):
    t = s / 40
    bench._reset(rig)
    px.pose_press_full(res, t)
    drives.drive(rig, body)
    probe.value = 0.0
    bpy.context.view_layer.update()
    p = native()
    cols = []
    for ax in range(3):
        off = basis_co.copy(); off[:, ax] += H
        probe.data.foreach_set("co", off.ravel()); probe.value = 1.0
        bpy.context.view_layer.update()
        cols.append((native() - p) / H)
        probe.value = 0.0
    probe.data.foreach_set("co", basis_co.ravel())
    mat = np.stack(cols, axis=2)
    e = float(px.press_state(t)[0])
    w = weight_at(e)
    row = {"sample": s, "elevation": round(e, 3), "elbow": round(float(px.press_state(t)[1]), 2)}
    if s <= 25:
        row["base_check_mm"] = round(float(np.linalg.norm(p - z["base"][s], axis=1).max() * 1000), 4)
        row["mat_check"] = round(float(np.abs(mat - z["mat"][s]).max()), 6)
        row["weight_check"] = round(float(np.abs(w - z["weight"][s]).max()), 8)
        if row["base_check_mm"] > 0.01 or row["mat_check"] > 1e-3 or row["weight_check"] > 1e-6:
            raise ValueError(("R70 model does not reproduce Work's unchanged sample", row))
    else:
        z["base"][s] = p.astype(z["base"].dtype)
        z["mat"][s] = mat.astype(z["mat"].dtype)
        z["weight"][s] = w.astype(z["weight"].dtype)
    report["samples"].append(row)
    print("R70_SOURCE", json.dumps(row), flush=True)
body.shape_key_remove(probe)
z["r70_top"] = np.array(os.environ["R70_TOP"])
np.savez_compressed(dst, **z)
Path(dst + ".json").write_text(json.dumps(report, indent=1))
print("R70_SOURCE_DONE", flush=True)
