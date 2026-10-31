"""Compare three.js playback of the GLB with Blender's evaluated mesh, frame by frame (review only).

usage: python3 compare_playback.py <playback out dir> <blender run dir> [--out report.json]
<playback out dir>: points_<clip>_<frame>.json from run_playback.mjs (CPU-skinned GLB positions, glTF Y-up, a sample of
vertices).  <blender run dir>: positions_<clip>.npy from movement_trajectory_test_blender.py (V2_TRAJ_SAVE_POS=1, the
same run that baked the GLB, so clip frame i is trajectory frame i).  The GLB splits vertices along UV seams, so each
sampled point is matched to its nearest Blender vertex; the distance is the playback error (a lower bound where the
error approaches the vertex spacing, ~3 mm; reported per frame as max / p99 / mean, mm).
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("play"); ap.add_argument("blender"); ap.add_argument("--out", default="")
    ap.add_argument("--lodcheck", default="", help="<glb>.lodcheck.npz from glb_bake_export (LOD evaluated in Blender at "
                    "each clip's first / middle / last frame + its mapping to the full mesh)")
    a = ap.parse_args()
    rep = {}
    if a.lodcheck:
        # (1) the GLB in three.js vs the SAME LOD evaluated in Blender (playback fidelity: same mesh, nearest vertex);
        # (2) the LOD in Blender vs the full mesh at the LOD's own surface points (exact barycentric correspondence)
        z = np.load(a.lodcheck)
        C, Bc = z["corners"], z["bary"]
        for k in z.files:
            if k in ("corners", "bary") or k.startswith(("pose_", "target_")):
                continue
            clip, f = k.rsplit("_", 1); f = int(f)
            Lb = z[k].astype(np.float64)
            P = np.load(Path(a.blender) / f"positions_{clip}.npy")[f].astype(np.float64)
            mapped = np.einsum("nk,nkj->nj", Bc, P[C])
            e2 = np.linalg.norm(Lb - mapped, axis=1) * 1000
            r = {"lod_vs_full_max_mm": round(float(e2.max()), 3), "lod_vs_full_p99_mm": round(float(np.percentile(e2, 99)), 3),
                 "lod_vs_full_mean_mm": round(float(e2.mean()), 4)}
            if f"target_{clip}_{f}" in z.files:                              # the fit's own target vs the harness
                r["fit_target_vs_harness_max_mm"] = round(float(np.linalg.norm(z[f"target_{clip}_{f}"] - mapped, axis=1).max() * 1000), 3)
                r["lod_vs_fit_target_max_mm"] = round(float(np.linalg.norm(Lb - z[f"target_{clip}_{f}"], axis=1).max() * 1000), 3)
            pf = Path(a.play) / f"points_{clip}_{f}.json"
            if pf.exists():
                Q = np.array(json.loads(pf.read_text())["points"], np.float64).reshape(-1, 3)
                Ly = np.stack([Lb[:, 0], Lb[:, 2], -Lb[:, 1]], 1)
                d1, _ = cKDTree(Ly).query(Q); d1 *= 1000
                r.update(three_vs_blender_lod_max_mm=round(float(d1.max()), 3), three_vs_blender_lod_p99_mm=round(float(np.percentile(d1, 99)), 4))
            rep.setdefault(clip, {})[str(f)] = r
        if a.out:
            Path(a.out).write_text(json.dumps(rep, indent=1))
        print(json.dumps(rep, indent=1))
        return
    for f in sorted(Path(a.play).glob("points_*.json")):
        d = json.loads(f.read_text()); clip, i = d["clip"], int(d["frame"])
        P = np.load(Path(a.blender) / f"positions_{clip}.npy")[i].astype(np.float64)
        Py = np.stack([P[:, 0], P[:, 2], -P[:, 1]], 1)                     # Blender Z-up -> glTF Y-up
        Q = np.array(d["points"], np.float64).reshape(-1, 3)
        dist, _ = cKDTree(Py).query(Q)
        dist *= 1000
        rep.setdefault(clip, {})[str(i)] = {"points": int(len(Q)), "max_mm": round(float(dist.max()), 3),
                                            "p99_mm": round(float(np.percentile(dist, 99)), 3),
                                            "mean_mm": round(float(dist.mean()), 4)}
    if a.out:
        Path(a.out).write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
