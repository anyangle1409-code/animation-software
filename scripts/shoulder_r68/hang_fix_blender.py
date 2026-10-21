"""R75: dead-hang shoulder/armpit fix in posed space, mapped back to the dense S7 controls above the press top (Claude).

Owner (21 Oct): next is the pull-up dead hang, matching the owner's photo from behind ("Match the photo": about 170 deg
elevation, slightly wide grip, straight elbows, shoulders shrugged up).  First look (R75, R74c and R52 alike): crumpled
skin on the inner upper arm at the armpit, the chest pulled into thin straps to the arms, sharp creases down the lats.

The S7 dense correctives are keyed by elevation only.  The locked press path stops at 150 deg, so the controls 151..166
are used only by straight-arm poses (Work's benchmark press above 150 and the hang, which reads the 166 control).
This tool:
  1. installs a candidate's dense increments on the immutable R41 (Claude's R61 installer, in memory) and poses the hang
     (Work's px.apply_pose, 0..180 deg coupled shoulder + shrug, elevation plane overridden, elbows straight);
  2. measures each vertex's exact linear map from a rest-space shape offset to the posed skin (probe key);
  3. builds the posed-space fix: Taubin (volume-preserving) relaxation of the armpit / chest / lat region, weighted
     smoothly to zero at the region's edge, arm and head excluded;
  4. maps it back to rest space per vertex (d = M^-1 delta) and adds it to the dense controls 151..166 with a smoothstep
     ramp (0 at 151, full at 166), so the press path (<= 150) is untouched;
  5. checks that the native skin with the new increments reproduces the posed target at the hang (linearity).
  blender python: hang_fix_blender.py -- <R57 root> <dense npz in> <dense npz out> [iters] [radius_m] [ramp_from]
Env: R70_TOP (the press path, for the installer), R75_HANG "ht:plane:shrug" (default 170:10:12).
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
root, src, dst = args[:3]
iters = int(args[3]) if len(args) > 3 else 40
radius = float(args[4]) if len(args) > 4 else 0.15
ramp_from = float(args[5]) if len(args) > 5 else 151.0
ROOT = Path(root).resolve()
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "shoulder_r61"), str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit")]
os.environ["S7_LOCKOUT_HT"] = "166"
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
from claude_r61_native import install

zd = np.load(src)
dense = (zd["dense"] if "dense" in zd.files else zd["dense_delta"]).astype(float)
res = r17._setup(ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend")
body, rig = res["body"], res["runtime"]
install(res, dense)
blocks = body.data.shape_keys.key_blocks
nv = len(body.data.vertices)
rest = np.empty(nv * 3); blocks[0].data.foreach_get("co", rest); rest = rest.reshape(-1, 3)
faces = np.array([p.vertices[:] for p in body.data.polygons if len(p.vertices) == 3] +
                 [p.vertices[:3] for p in body.data.polygons if len(p.vertices) == 4] +
                 [(p.vertices[0], p.vertices[2], p.vertices[3]) for p in body.data.polygons if len(p.vertices) == 4])
ht, plane, shrug = (float(x) for x in os.environ.get("R75_HANG", "170:10:12").split(":"))


def native():
    pp, _ = bench._evaluated(body)
    return np.array([tuple(v) for v in pp])


def pose_hang():
    name = px._PATH["name"]; base_plane = px.PATHS[name]["plane_deg"]
    bench._reset(rig); px.PATHS[name]["plane_deg"] = plane
    try:
        px.apply_pose(res, ht, shrug)
    finally:
        px.PATHS[name]["plane_deg"] = base_plane
    drives.drive(rig, body); bpy.context.view_layer.update()


pose_hang()
P = native()
# probe: exact linear map rest offset -> posed skin at the hang
probe = body.shape_key_add(name="R75_PROBE", from_mix=False); H = 0.01; cols = []
for ax in range(3):
    off = rest.copy(); off[:, ax] += H
    probe.data.foreach_set("co", off.ravel()); probe.value = 1.0; bpy.context.view_layer.update()
    cols.append((native() - P) / H); probe.value = 0.0
probe.data.foreach_set("co", rest.ravel()); body.shape_key_remove(probe)
M = np.stack(cols, axis=2)                                            # (nv,3,3)

# region: both armpits / chest / lats, smooth falloff; arm below the elbow side and the head excluded
w = np.zeros(nv)
# centres "x,y,z,r/..." (right side, mirrored); default: the armpit, plus (measured with the hang mode's crease list on
# R74c) the shoulder top where deltoid meets trapezius under the shrug (rest (0.28,0.04,1.45), up to 115 deg) and the
# front of the armpit (rest (0.19,-0.02,1.36), 121 deg)
CENTRES = os.environ.get("R75_CENTRES", f"0.17,0.03,1.36,{radius}")
for cs in CENTRES.split("/"):
    cx, cy, cz, cr = (float(v) for v in cs.split(","))
    for sg in (-1.0, 1.0):
        d_ = np.linalg.norm(rest - np.array([sg * cx, cy, cz]), axis=1)
        x = np.clip((cr - d_) / (0.5 * cr), 0, 1); w = np.maximum(w, x * x * (3 - 2 * x))
w[(rest[:, 2] > 1.58) & (np.abs(rest[:, 0]) < 0.12)] = 0.0             # neck / head

# Taubin relaxation in posed space (lambda 0.5, mu -0.53), weighted
nb = [[] for _ in range(nv)]
for a_, b_, c_ in faces:
    nb[a_] += [b_, c_]; nb[b_] += [a_, c_]; nb[c_] += [a_, b_]
nb = [np.unique(n) for n in nb]
rows = np.repeat(np.arange(nv), [len(n) for n in nb]); cols_ = np.concatenate(nb)
deg = np.array([len(n) for n in nb], float)


def lap(X):
    acc = np.zeros_like(X); np.add.at(acc, rows, X[cols_]); return acc / deg[:, None] - X


Q = P.copy()
for _ in range(iters):
    Q = Q + (0.5 * w)[:, None] * lap(Q)
    Q = Q - (0.53 * w)[:, None] * lap(Q)
# optional fill "x,y,z,r,mm/..." (right side, mirrored): push outward along the normals of a heavily smoothed copy of the
# skin (so a folded flap gets the direction of the surface it should be, not its own), then relax the push
if os.environ.get("R75_INFLATE"):
    S_ = P.copy()
    for _ in range(60):
        S_ = S_ + 0.5 * lap(S_)
    tri = S_[faces]; fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    vn = np.zeros_like(P); np.add.at(vn, faces.ravel(), np.repeat(fn, 3, axis=0))
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    push = np.zeros(nv)
    for cs in os.environ["R75_INFLATE"].split("/"):
        cx, cy, cz, cr, mm = (float(v) for v in cs.split(","))
        for sg in (-1.0, 1.0):
            d_ = np.linalg.norm(rest - np.array([sg * cx, cy, cz]), axis=1)
            x = np.clip((cr - d_) / (0.5 * cr), 0, 1); push = np.maximum(push, x * x * (3 - 2 * x) * mm / 1000.0)
    Dp = vn * push[:, None]
    for _ in range(20):
        Dp = Dp + 0.5 * lap(Dp)
    Q = Q + Dp
    for _ in range(30):
        Q = Q + (0.5 * w)[:, None] * lap(Q); Q = Q - (0.53 * w)[:, None] * lap(Q)
delta = Q - P
dr = np.linalg.solve(M, delta[..., None])[..., 0]                    # rest-space offset at the 166 control
ramp = {e: float(np.clip((e - ramp_from) / (166.0 - ramp_from), 0, 1)) for e in range(int(ramp_from), 167)}
ramp = {e: r_ * r_ * (3 - 2 * r_) for e, r_ in ramp.items()}
out = dense.copy()
for e, r_ in ramp.items():
    out[e - 95] += r_ * dr
cap = float(np.linalg.norm(out, axis=2).max())
if cap > 0.045:
    out *= np.minimum(1.0, 0.0449 / np.maximum(np.linalg.norm(out, axis=2), 1e-12))[..., None]   # installer cap 45 mm (float32-safe)
# linearity check: re-install and pose
# (a second install on the same scene would read back the already-installed keys, so reload the immutable R41 first)
res = r17._setup(ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend")
body, rig = res["body"], res["runtime"]
install(res, out); pose_hang(); P2 = native()
err = float(np.linalg.norm(P2 - Q, axis=1).max() * 1000)
report = {"hang": [ht, plane, shrug], "centres": CENTRES, "inflate": os.environ.get("R75_INFLATE", ""), "iters": iters, "radius": radius, "ramp_from": ramp_from,
          "max_posed_change_mm": round(float(np.linalg.norm(delta, axis=1).max() * 1000), 2),
          "max_rest_offset_mm": round(float(np.linalg.norm(dr, axis=1).max() * 1000), 2),
          "dense_cap_mm": round(cap * 1000, 2), "native_vs_target_max_err_mm": round(err, 3),
          "region_vertices": int((w > 0).sum())}
np.savez_compressed(dst, dense=out.astype(np.float32))
Path(dst + ".json").write_text(json.dumps(report, indent=1))
print("R75_FIX", json.dumps(report), flush=True)
