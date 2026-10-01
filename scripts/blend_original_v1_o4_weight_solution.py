"""Zero-regression blend of a solver solution with the base weights (numpy only; never touches a Blend).

python scripts/blend_original_v1_o4_weight_solution.py <base dump.npz> <solution.npz> <base report.json> --r2-report <R2.json>
       [--scan] [--alpha-torso A --alpha-other B --out <blended.npz>] [--exempt press_bottom/shoulder/min ...]

Why: a constrained solver can end at a point that buys a gate with a comparator regression elsewhere. Every convex
combination W(alpha) = (1-alpha) W_base + alpha W_solution of two valid weight sets is itself a valid, normalised
weight set, and the base satisfies every guard. This tool evaluates the exact numpy linear-blend-skinning model
(which reproduces Blender to ~1e-6; checked by the dumper) against every comparator tolerance - region min/max,
1st/99th percentile edge ratio, volume deviation - versus BOTH the pinned R2 report and the base candidate's own
report, and selects the largest zero-regression blend. The zone is split into the torso-region vertices and the
rest (pelvis/leg) so each half gets its own factor. Self-intersection counts are NOT modelled here; the real
full-evidence run measures them.

--scan prints the 2-D feasible frontier. With --out it writes the blended solution (top 4 influences, mirror-
averaged for exact left/right symmetry, renormalised) in the same format the apply script reads, plus <out>.json
describing the selection. Tolerances are read from ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def prune4(W):
    order = np.argsort(-W, axis=1)
    keep = np.zeros_like(W, bool)
    keep[np.arange(len(W))[:, None], order[:, :4]] = True
    W = np.where(keep, W, 0.0)
    return W / W.sum(axis=1, keepdims=True)


class Model:
    def __init__(self, dump, base_report, r2_report, tolerances, poses=None):
        d = np.load(dump)
        self.d = d
        self.rest, self.E, self.reg, self.tris = d["rest"], d["edges"], d["region"], d["tris"]
        self.rn = [str(x) for x in d["region_names"]]
        self.bones = [str(x) for x in d["bones"]]
        self.W0 = d["W"]
        self.poses = [str(x) for x in d["poses"]]
        self.eval_poses = poses or self.poses
        self.rh = np.c_[self.rest, np.ones(len(self.rest))]
        self.L0 = np.linalg.norm(self.rest[self.E[:, 0]] - self.rest[self.E[:, 1]], axis=1)
        self.vol0 = self._vol(self.rest)
        self.base = {x["pose"]: x for x in json.loads(Path(base_report).read_text(encoding="utf-8"))}
        self.r2 = {x["pose"]: x for x in json.loads(Path(r2_report).read_text(encoding="utf-8"))}
        self.tol = tolerances
        self.margin = 0.0
        self.volume_margin = 0.0

    def _vol(self, P):
        t = self.tris
        return abs(np.einsum("ti,ti->t", P[t[:, 0]], np.cross(P[t[:, 1]], P[t[:, 2]])).sum() / 6)

    def metrics(self, Z, used, Wz):
        out = {}
        for pn in self.eval_poses:
            p = self.poses.index(pn)
            P = self.d["evaluated"][p].copy()
            T = np.einsum("bij,vj->vbi", self.d["mats"][p][used][:, :3, :], self.rh[Z])
            P[Z] = np.einsum("vb,vbi->vi", Wz, T)
            r = np.linalg.norm(P[self.E[:, 0]] - P[self.E[:, 1]], axis=1) / self.L0
            reg = {}
            for g in self.rn:
                m = self.reg[self.E[:, 0]] == self.rn.index(g)
                if m.any():
                    reg[g] = (float(r[m].min()), float(r[m].max()))
            out[pn] = {"reg": reg, "p01": float(np.percentile(r, 1)), "p99": float(np.percentile(r, 99)),
                       "vol": self._vol(P) / self.vol0}
        return out

    def violations(self, m, ref, label, exempt):
        # Compare exactly as the comparator does: the pose report rounds ratios to 3 decimals and volume to 4,
        # and a breach is a strict '>' against the tolerance. `margin` keeps every accepted blend that far
        # INSIDE each tolerance (a first version stopped on the edge: squat volume +0.005000000000000004).
        t, v, mg = self.tol, [], self.margin
        for pn, x in m.items():
            x = {"reg": {g: (round(a, 3), round(b, 3)) for g, (a, b) in x["reg"].items()},
                 "p01": round(x["p01"], 3), "p99": round(x["p99"], 3), "vol": round(x["vol"], 4)}
            for g, (mn, mx) in x["reg"].items():
                a = ref[pn]["by_region"].get(g)
                if not a:
                    continue
                if mn < a["min_ratio"] - t["region_min_ratio_drop"] + mg and (pn, g, "min") not in exempt:
                    v.append((label, pn, g, "min", a["min_ratio"], round(mn, 3)))
                if mx > a["max_ratio"] + t["region_max_ratio_rise"] - mg and (pn, g, "max") not in exempt:
                    v.append((label, pn, g, "max", a["max_ratio"], round(mx, 3)))
            if x["p99"] > ref[pn]["edge_ratio_p99"] + t["edge_ratio_p99_rise"] - mg:
                v.append((label, pn, "ALL", "p99", ref[pn]["edge_ratio_p99"], round(x["p99"], 3)))
            if x["p01"] < ref[pn]["edge_ratio_p01"] - t["edge_ratio_p01_drop"] + mg:
                v.append((label, pn, "ALL", "p01", ref[pn]["edge_ratio_p01"], round(x["p01"], 3)))
            if abs(x["vol"] - 1) > abs(ref[pn]["volume_ratio"] - 1) + t["volume_deviation_from_1_rise"] - self.volume_margin:
                v.append((label, pn, "ALL", "vol", ref[pn]["volume_ratio"], round(x["vol"], 4)))
        return v

    def all_violations(self, m, exempt):
        return self.violations(m, self.r2, "R2", exempt) + self.violations(m, self.base, "base", set())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dump")
    ap.add_argument("solution")
    ap.add_argument("base_report")
    ap.add_argument("--r2-report", required=True)
    ap.add_argument("--acceptance", default=str(ROOT / "ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json"))
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--alpha-torso", type=float)
    ap.add_argument("--alpha-other", type=float)
    ap.add_argument("--out")
    ap.add_argument("--exempt", nargs="*", default=[], help="pose/region/min|max items inherited from the base, excluded vs R2")
    ap.add_argument("--poses", help="comma-separated poses to evaluate (default: all in the dump)")
    ap.add_argument("--margin", type=float, default=0.001, help="keep every ratio/percentile metric this far inside its tolerance")
    ap.add_argument("--volume-margin", type=float, default=0.0001, help="same for the 4-decimal volume deviation (model-vs-Blender error is ~1e-6)")
    a = ap.parse_args()
    tol = json.loads(Path(a.acceptance).read_text(encoding="utf-8"))["comparison_tolerances"]
    exempt = {tuple(x.split("/")) for x in a.exempt}
    M = Model(a.dump, a.base_report, a.r2_report, tol, a.poses.split(",") if a.poses else None)
    M.margin = a.margin
    M.volume_margin = a.volume_margin
    s = np.load(a.solution)
    Z, ub = s["vertices"], [str(x) for x in s["bones"]]
    used = [M.bones.index(x) for x in ub]
    W0z = M.W0[Z][:, used]
    W0z = W0z / W0z.sum(axis=1, keepdims=True)
    torso = np.array([M.rn[M.reg[v]] == "torso" for v in Z])

    def blend(aT, aO):
        Wz = W0z.copy()
        Wz[torso] = prune4((1 - aT) * W0z[torso] + aT * s["weights"][torso])
        Wz[~torso] = prune4((1 - aO) * W0z[~torso] + aO * s["weights"][~torso])
        return Wz

    if a.scan:
        grid = np.round(np.arange(0, 1.0001, 0.05), 2)
        rows = []
        for aT in grid:
            for aO in grid:
                m = M.metrics(Z, used, blend(aT, aO))
                v = M.all_violations(m, exempt)
                l = m["lunge"]["reg"] if "lunge" in m else {}
                rows.append((len(v), aT, aO, l))
        feas = [r for r in rows if r[0] == 0]
        print(f"zero-regression combinations: {len(feas)} of {len(rows)}")
        for n, aT, aO, l in sorted(feas, key=lambda r: -(r[1] + r[2]))[:8]:
            print(f"  alpha_torso {aT:.2f} alpha_other {aO:.2f}", {k: (round(x, 3), round(y, 2)) for k, (x, y) in l.items() if k in ("pelvis", "torso")})
    if a.out and a.alpha_torso is not None and a.alpha_other is not None:
        Wz = blend(a.alpha_torso, a.alpha_other)
        key = {tuple(np.round(M.rest[v] * [-1, 1, 1], 5)): k for k, v in enumerate(Z)}
        tw = np.array([key.get(tuple(np.round(M.rest[v], 5)), -1) for v in Z])
        if (tw < 0).any():
            raise SystemExit("zone is not mirror-closed")
        sw = [ub.index(n[:-2] + ("_r" if n.endswith("_l") else "_l")) if n[-2:] in ("_l", "_r") else ub.index(n) for n in ub]
        Wz = 0.5 * (Wz + Wz[tw][:, sw])
        Wz = np.where(Wz < 1e-6, 0.0, Wz)
        Wz /= Wz.sum(axis=1, keepdims=True)
        m = M.metrics(Z, used, Wz)
        v = M.all_violations(m, exempt)
        if v:
            raise SystemExit("refusing to write: blend has predicted violations " + json.dumps(v)[:400])
        np.savez_compressed(a.out, vertices=Z, bones=np.array(ub), weights=Wz)
        rec = {"generated_utc": datetime.now(timezone.utc).isoformat(), "tool": "scripts/blend_original_v1_o4_weight_solution.py",
               "source_solution": Path(a.solution).name, "source_solution_sha256": hashlib.sha256(Path(a.solution).read_bytes()).hexdigest(),
               "base_dump": Path(a.dump).name, "base_report": a.base_report, "r2_report": a.r2_report,
               "alpha_torso_region": a.alpha_torso, "alpha_other_region": a.alpha_other, "zone_vertices": int(len(Z)), "bones": ub,
               "exempt_inherited_vs_r2": sorted("/".join(x) for x in exempt), "safety_margin": a.margin, "volume_safety_margin": a.volume_margin,
               "twin_L1_max": float(np.abs(Wz - Wz[tw][:, sw]).sum(1).max()), "max_influences": int((Wz > 0).sum(1).max()),
               "predicted_violations": [], "inputs": "this candidate's own ORIGINAL v1 mesh/weights and the v4 rig only"}
        Path(a.out).with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        print("BLEND WRITTEN", a.out, "predicted violations: none")


if __name__ == "__main__":
    main()
