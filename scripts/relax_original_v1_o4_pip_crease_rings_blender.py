"""Relax the PIP crease edge-ring spacing of every finger of an O4 candidate (geometry only).

blender --background --factory-startup <source O4_bind candidate.blend> --python-exit-code 1 \
        --python scripts/relax_original_v1_o4_pip_crease_rings_blender.py -- <new candidate.blend>

Priority 2 minimal local repair. Evidence: three weight solves (o14, o17, o19)
plateaued at ~104 triangle pairs of PIP-crease self-intersection; the colliding
faces sit ~2 mm apart across the unevenly spaced crease rings (e.g. index at
-3/0/+2/+4 mm around the PIP head). Re-spacing the rings evenly removes all of
them in a numpy LBS test with unchanged weights.

For each finger (index/middle/ring/pinky, both hands) the edge rings within
+/-12.5 mm of the PIP head (the mesh's own rings, clustered by axial gaps) are
re-spaced evenly between the fixed first and last ring. Each vertex slides along
its own mesh column (piecewise-linear interpolation between its ring
neighbours), so it stays on the original surface: no topology, weight, UV,
material or rig change. Refuses to overwrite; writes <new>.json with hashes,
displacement statistics and symmetry check.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
new_path = Path(args[0])
if new_path.exists():
    raise SystemExit(f"Refusing to overwrite {new_path}")
scene = bpy.context.scene
if not scene.get("hgpt_not_production") or scene.get("hgpt_candidate") != "O4_bind":
    raise SystemExit("O4_bind candidate files only.")
src_path = Path(bpy.data.filepath)
src_sha = hashlib.sha256(src_path.read_bytes()).hexdigest()
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
if len(rig.data.bones) != 63:
    raise SystemExit("Expected the frozen 63-bone v4 rig.")
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
me = body.data
names = json.loads(scene["hgpt_region_names"])
region = np.array([d.value for d in me.attributes["hgpt_region"].data])
rest = np.array([v.co[:] for v in me.vertices])
mw = np.array(rig.matrix_world)


def head(n):
    return (mw @ np.r_[np.array(rig.data.bones[n].head_local), 1.0])[:3]


R = rest.copy()
moved = {}
for s in "lr":
    for f in ("index", "middle", "ring", "pinky"):
        h1, h2, h3 = (head(f"{f}_0{k}_{s}") for k in (1, 2, 3))
        ax = (h3 - h1) / np.linalg.norm(h3 - h1)
        t = (rest - h2) @ ax
        radial = (rest - h2) - np.outer(t, ax)
        m = np.nonzero((t > -0.0125) & (t < 0.0125) & (np.linalg.norm(radial, axis=1) < 0.013)
                       & (region == names.index("finger")))[0]
        o = np.argsort(t[m])
        ts = t[m][o]
        rings = [m[o][g] for g in np.split(np.arange(len(ts)), np.nonzero(np.diff(ts) > 0.0006)[0] + 1)]
        if len({len(r) for r in rings}) != 1 or len(rings) < 4:
            raise SystemExit(f"{f}_{s}: unexpected ring structure {[len(r) for r in rings]}")
        ref = np.cross(ax, [0, 1.0, 0]) if abs(ax[1]) < 0.9 else np.cross(ax, [1.0, 0, 0])
        ref /= np.linalg.norm(ref)
        ref2 = np.cross(ax, ref)
        cols = [r[np.argsort(np.arctan2(radial[r] @ ref2, radial[r] @ ref))] for r in rings]
        tl = np.array([t[c].mean() for c in cols])
        tnew = np.linspace(tl[0], tl[-1], len(tl))
        for k in range(len(cols[0])):
            col = np.array([c[k] for c in cols])
            P, tc = rest[col], t[col]
            for j in range(1, len(col) - 1):
                x = tnew[j] + (tc[j] - tl[j])
                i = int(np.clip(np.searchsorted(tc, x) - 1, 0, len(col) - 2))
                a = (x - tc[i]) / (tc[i + 1] - tc[i])
                R[col[j]] = P[i] + a * (P[i + 1] - P[i])
        moved[f"{f}_{s}"] = [round(float(x) * 1000, 3) for x in (tnew - tl)]

disp = np.linalg.norm(R - rest, axis=1)
# symmetry check: mirror twins must move mirror-symmetrically
key = {tuple(np.round(p * [-1, 1, 1], 5)): i for i, p in enumerate(rest)}
mirror = np.array([key.get(tuple(np.round(p, 5)), -1) for p in rest])
sym_err = float(np.abs(R[mirror[mirror >= 0]] * [-1, 1, 1] - R[mirror >= 0]).max())
if sym_err > 1e-5:
    raise SystemExit(f"Relaxed geometry is not mirror-symmetric (max {sym_err})")
for i in np.nonzero(disp > 0)[0]:
    me.vertices[i].co = R[i].tolist()
me.update()

scene["hgpt_candidate_revision"] = new_path.stem
scene["hgpt_candidate_parent_sha256"] = src_sha
scene["hgpt_geometry_revision"] = "pip_crease_ring_relax_v1"
bpy.ops.wm.save_as_mainfile(filepath=str(new_path), copy=True)
rec = {"generated_utc": datetime.now(timezone.utc).isoformat(),
       "stage": "O4 candidate first-party local geometry repair: PIP crease ring re-spacing (not production)",
       "source_candidate": src_path.name, "source_sha256": src_sha,
       "candidate": new_path.name, "candidate_sha256": hashlib.sha256(new_path.read_bytes()).hexdigest(),
       "vertices_moved": int((disp > 0).sum()), "max_displacement_mm": round(float(disp.max()) * 1000, 3),
       "ring_axial_shift_mm": moved, "mirror_symmetry_max_error_m": sym_err,
       "topology_changed": False, "weights_changed": False, "rig_bones": len(rig.data.bones),
       "inputs": "this candidate's own ORIGINAL v1 mesh and the v4 rig only"}
new_path.with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("RELAX", json.dumps({k: rec[k] for k in ("candidate", "candidate_sha256", "vertices_moved", "max_displacement_mm",
                                                 "mirror_symmetry_max_error_m")}))
