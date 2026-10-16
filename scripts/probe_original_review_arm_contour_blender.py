"""Read-only diagnosis of the owner's four arm-to-side contour locations."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit")]
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
import build_original_sculpt_corrective_blender as sculpt
MODEL = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r34_20261016/HGPT_ORIGINAL_V1_REVIEW_R34_CODEX.blend"
OUT = Path("/tmp/r35-contour-probe")
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(MODEL))
res = correction.build_corrected_scene()
body, rig = res["body"], res["runtime"]
for kb in body.data.shape_keys.key_blocks[1:]:
    kb.value = 0
drives.setup(res)
px.install()
bench._reset(rig)
v0, faces = bench._evaluated(body)
data = {"rest": np.array([tuple(v) for v in v0]), "faces": np.asarray(faces)}
names = {g.index: g.name for g in body.vertex_groups}
for side in ("l", "r"):
    data[f"arm_weight_{side}"] = np.array([
        sum(g.weight for g in v.groups if names[g.group].endswith("_" + side)
            and names[g.group].startswith(("upperarm", "forearm", "lowerarm")))
        for v in body.data.vertices])
report = {"status": "DIAGNOSTIC_ONLY", "owner_marks": [
    {"x_percent": 7, "y_percent": 32, "note": "point in upper-arm contour"},
    {"x_percent": 25, "y_percent": 29, "note": "upper arm should flow into body"},
    {"x_percent": 78, "y_percent": 29, "note": "same junction in three-quarter"},
    {"x_percent": 90, "y_percent": 27, "note": "same junction opposite side"}], "samples": {}}
for ht in (120.0, 130.0, 135.625, 145.0, 156.0, 166.0):
    bench._reset(rig)
    sculpt.press_pose(res, ht)
    drives.drive(rig, body)
    values = {kb.name: kb.value for kb in body.data.shape_keys.key_blocks}
    bones = {}
    for side in ("l", "r"):
        gh = np.array(tuple(rig.matrix_world @ rig.pose.bones["upperarm_" + side].head))
        elbow = np.array(tuple(rig.matrix_world @ rig.pose.bones["forearm_" + side].head))
        bones[side] = {"gh": gh.tolist(), "elbow": elbow.tolist()}
        data[f"gh_{side}_{ht}"] = gh
        data[f"elbow_{side}_{ht}"] = elbow
    samples = {}
    for mode, off in (("all", ()), ("noS7", ("HGPT_S7_DELT_",)),
                      ("noS5", ("HGPT_S5_BAKE_",)), ("noS5S7", ("HGPT_S5_BAKE_", "HGPT_S7_DELT_"))):
        for kb in body.data.shape_keys.key_blocks:
            kb.value = 0 if kb.name.startswith(off) and off else values[kb.name]
        vertices, _ = bench._evaluated(body)
        p = np.array([tuple(v) for v in vertices])
        data[f"{mode}_{ht}"] = p
        samples[mode] = {}
        for view, d in (("back", (0, 1, 0.02)), ("three_quarter", (0.7, 0.7, 0.05))):
            rotation = (-Vector(d).normalized()).to_track_quat("-Z", "Y").to_matrix()
            right, up = np.array(rotation.col[0]), np.array(rotation.col[1])
            for side in ("l", "r"):
                gh = np.asarray(bones[side]["gh"])
                delta = p - gh
                vertical = delta @ up
                outward = 1 if gh @ right > 0 else -1
                horizontal = (delta @ right) * outward
                region = (np.linalg.norm(delta, axis=1) < 0.22) & (p[:, 0] * (1 if side == "r" else -1) > 0)
                profile = []
                for center in np.arange(-0.12, 0.151, 0.005):
                    sel = np.where(region & (abs(vertical - center) < 0.004))[0]
                    if len(sel):
                        i = int(sel[np.argmax(horizontal[sel])])
                        profile.append({"up_mm": round(float(center * 1000), 2),
                                        "out_mm": round(float(horizontal[i] * 1000), 3), "vertex": i})
                samples[mode][view + "_" + side] = profile
    for kb in body.data.shape_keys.key_blocks:
        kb.value = values[kb.name]
    report["samples"][str(ht)] = {"bones": bones, "profiles": samples}
np.savez_compressed(OUT / "r34_contour_surfaces.npz", **data)
(OUT / "r34_contour_probe.json").write_text(json.dumps(report, indent=2) + "\n")
print("CONTOUR_PROBE_COMPLETE", str(OUT), flush=True)
