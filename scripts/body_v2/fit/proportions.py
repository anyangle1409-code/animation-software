"""Body v2 proportion check against ANSUR II male (Claude, 21 Oct 2026).

Measures the bind-pose surface (R41 rest + a body v2 offsets file) with exact horizontal mesh sections and compares each
landmark with ANSUR II male (n = 4,082) predicted at the model's own stature (OLS on stature), as z-scores.

  python3 proportions.py <rest.npy> <tris.npy> <landmarks.json> <ANSUR_II_MALE_Public.csv> [offsets.npz] [out.json]
rest / tris / landmarks are dumped from the R41 blend (body vertices, triangulated faces, LM_* empties in world space).
"""
import csv
import json
import sys

import numpy as np


def plane_loops(V, T, z):
    d = V[:, 2] - z
    d = np.where(np.abs(d) < 1e-12, 1e-12, d)
    s = np.sign(d)[T]
    hit = np.nonzero(~((s[:, 0] == s[:, 1]) & (s[:, 1] == s[:, 2])))[0]
    pts, adj = {}, {}
    for t in hit:
        tri = T[t]; keys = []
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            if np.sign(d[a]) != np.sign(d[b]):
                k = (min(a, b), max(a, b))
                if k not in pts:
                    w = d[a] / (d[a] - d[b]); pts[k] = V[a] + w * (V[b] - V[a])
                keys.append(k)
        if len(keys) == 2:
            adj.setdefault(keys[0], []).append(keys[1]); adj.setdefault(keys[1], []).append(keys[0])
    seen, loops = set(), []
    for k0 in adj:
        if k0 in seen:
            continue
        loop, k, prev = [], k0, None
        while k is not None and k not in seen:
            seen.add(k); loop.append(pts[k])
            nxt = [n for n in adj[k] if n != prev and n not in seen]
            prev, k = k, (nxt[0] if nxt else None)
        if len(loop) >= 8:
            loops.append(np.array(loop))
    return loops


def perim(l):
    return float(np.linalg.norm(np.roll(l, -1, 0) - l, axis=1).sum())


def main():
    rest = np.load(sys.argv[1]); T = np.load(sys.argv[2]); LM = json.load(open(sys.argv[3]))
    rows = list(csv.DictReader(open(sys.argv[4], encoding="latin-1")))
    V = rest + (np.load(sys.argv[5])["offsets"] if len(sys.argv) > 5 and sys.argv[5] != "-" else 0)
    floor = V[:, 2].min(); H = V[:, 2].max() - floor
    S = np.array([float(r["stature"]) for r in rows])

    def ansur(col):
        y = np.array([float(r[col]) for r in rows]); A = np.vstack([S, np.ones_like(S)]).T
        c = np.linalg.lstsq(A, y, rcond=None)[0]
        return (c[0] * H * 1000 + c[1]) / 1000, float(np.std(y - A @ c)) / 1000

    def near(name):
        p = np.array(LM[name]); return V[np.argmin(np.linalg.norm(rest - p, axis=1))]

    m = {}
    m["acromialheight"] = np.mean([near(f"LM_scapula_{s}__acromion_lateral_skin")[2] for s in ("left", "right")]) - floor
    m["suprasternaleheight"] = near("LM_sternum__ij_skin")[2] - floor
    m["wristheight"] = np.mean([near(f"LM_humerus_{s}__styloid_radial_skin")[2] for s in ("left", "right")]) - floor
    # axilla: highest section where the right arm is its own loop
    for z in np.arange(1.50, 1.20, -0.001):
        if any(l[:, 0].min() > 0.12 for l in plane_loops(V, T, z)):
            m["axillaheight"] = z - floor; break
    # crotch: highest section where the right leg no longer crosses the midline
    for z in np.arange(1.05, 0.60, -0.001):
        ls = [l for l in plane_loops(V, T, z) if np.abs(l[:, 0]).max() < 0.30]
        if ls and not any(l[:, 0].min() < -0.01 and l[:, 0].max() > 0.01 for l in ls):
            m["crotchheight"] = z - floor; break
    # dactylion: follow the right arm loop down from z 1.00
    prev = next(l.mean(0) for l in plane_loops(V, T, 1.00) if l[:, 0].min() > 0.12); z = 1.00
    while z > 0.40:
        c = [l for l in plane_loops(V, T, z - 0.002) if np.linalg.norm(l.mean(0)[:2] - prev[:2]) < 0.04 and l[:, 0].min() > 0.10]
        if not c:
            break
        z -= 0.002; prev = c[0].mean(0)
    dact = z - floor
    # trunk sections: waist at the ANSUR omphalion height, the narrowest trunk section 0.95-1.30, hips (max 0.85-1.05)
    def trunk(z):
        ls = [l for l in plane_loops(V, T, floor + z) if l[:, 0].min() < -0.01 and l[:, 0].max() > 0.01]
        return max(ls, key=perim) if ls else None
    wz, _ = ansur("waistheightomphalion")
    tw = trunk(wz)
    m["waistheightomphalion"] = wz
    m["waistcircumference"] = perim(tw); m["waistbreadth"] = float(np.ptp(tw[:, 0])); m["waistdepth"] = float(np.ptp(tw[:, 1]))
    prof = [(z, trunk(z)) for z in np.arange(0.50, 0.72, 0.005) * H]
    prof = [(z, float(np.ptp(l[:, 0])), perim(l)) for z, l in prof if l is not None]
    zmin = min(prof, key=lambda r: r[1])
    m["min_trunk_breadth"] = zmin[1]
    hips = [(z, trunk(z)) for z in np.arange(0.44, 0.58, 0.005) * H]
    hips = [(z, float(np.ptp(l[:, 0])), perim(l)) for z, l in hips if l is not None and np.ptp(l[:, 0]) < 0.50]
    hb = max(hips, key=lambda r: r[1]); m["hipbreadth"] = hb[1]; m["buttockcircumference"] = max(r[2] for r in hips)
    chest = [(z, trunk(z)) for z in np.arange(0.70, 0.76, 0.005) * H]
    chest = [l for z, l in chest if l is not None]
    chest = [l for l in chest if np.ptp(l[:, 0]) < 0.45]          # in the bind pose the arms can touch the chest: skip merged loops
    if chest:
        m["chestcircumference"] = max(perim(l) for l in chest); m["chestbreadth"] = max(float(np.ptp(l[:, 0])) for l in chest)

    out = {"stature_m": round(float(H), 4), "rows": {}}
    for k, v in m.items():
        if k in ("min_trunk_breadth",):
            out["rows"][k] = {"model_m": round(float(v), 4), "z_m": round(float(zmin[0]), 3)}; continue
        if k == "waistheightomphalion":
            continue
        p, sd = ansur(k)
        out["rows"][k] = {"model_m": round(float(v), 4), "ansur_m": round(p, 4), "sd_m": round(sd, 4), "z": round((float(v) - p) / sd, 2)}
    # arm length acromion -> dactylion against ANSUR (acromion-radiale + radiale-stylion + hand length)
    y = np.array([float(r["acromionradialelength"]) + float(r["radialestylionlength"]) + float(r["handlength"]) for r in rows])
    A = np.vstack([S, np.ones_like(S)]).T; c = np.linalg.lstsq(A, y, rcond=None)[0]; p = (c[0] * H * 1000 + c[1]) / 1000; sd = np.std(y - A @ c) / 1000
    arm = m["acromialheight"] - dact
    out["rows"]["acromion_to_dactylion"] = {"model_m": round(float(arm), 4), "ansur_m": round(float(p), 4), "sd_m": round(float(sd), 4), "z": round(float((arm - p) / sd), 2)}
    out["rows"]["dactylion_height"] = {"model_m": round(float(dact), 4)}
    print(json.dumps(out, indent=1))
    if len(sys.argv) > 6:
        open(sys.argv[6], "w").write(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
