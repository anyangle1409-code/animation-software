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
    a = ap.parse_args()
    rep = {}
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
