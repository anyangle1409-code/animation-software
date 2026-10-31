"""CANDIDATE, not adopted (owner decision: it changes the bind): keep forearm rotation out of the elbow crease.  In memory;
nothing is saved to a blend.

Why: the rig's forearm-rotation rule leaves the proximal twist bone (forearm_tw0) untwisted, tw1 at half and the forearm
bone (wrist end) at the full pronation / supination - but skin in the elbow crease also carries tw1 / forearm weight, so it
turns a few degrees with the forearm and crosses the crease the elbow keys were authored for (AX6, elbow 90: pronation
34 deg gives 546 crossing pairs, all forearm_tw0 skin against upper-arm skin; 0 at neutral).  Anatomically the skin by the
elbow barely turns: the radial head spins in place.

What: reweight() moves each forearm-segment vertex's tw1 and forearm weight onto tw0 by g(t), t its position along the
forearm (elbow 0 -> wrist 1): g = 1 below T0, a smoothstep to 0 at T1.  With the forearm at neutral rotation the three
bones pose identically, so every authored movement is unchanged (within float noise); only forearm rotation sees it.
"""
from __future__ import annotations

T0, T1 = 0.15, 0.40
SIDES = ("l", "r")


def reweight(rig, body, t0=T0, t1=T1):
    """move tw1 / forearm weight onto tw0 near the elbow (in memory); returns the number of vertices changed per side"""
    out = {}
    MWr, MWb = rig.matrix_world, body.matrix_world
    for s in SIDES:
        a = MWr @ rig.data.bones[f"forearm_{s}"].head_local; b = MWr @ rig.data.bones[f"hand_{s}"].head_local
        ax = b - a; L2 = ax.length_squared
        g0, g1, gf = (body.vertex_groups[f"forearm_tw0_{s}"], body.vertex_groups[f"forearm_tw1_{s}"],
                      body.vertex_groups[f"forearm_{s}"])
        idx = {g0.index: "tw0", g1.index: "tw1", gf.index: "fa"}
        n = 0
        for v in body.data.vertices:
            w = {idx[g.group]: g.weight for g in v.groups if g.group in idx}
            if not w or (w.get("tw1", 0.0) + w.get("fa", 0.0)) <= 0.0:
                continue
            t = (MWb @ v.co - a).dot(ax) / L2
            if t >= t1:
                continue
            x = min(1.0, max(0.0, (t - t0) / (t1 - t0))); g = 1.0 - x * x * (3.0 - 2.0 * x)
            if g <= 0.0:
                continue
            moved = g * (w.get("tw1", 0.0) + w.get("fa", 0.0))
            g0.add([v.index], w.get("tw0", 0.0) + moved, "REPLACE")
            if "tw1" in w:
                g1.add([v.index], w["tw1"] * (1.0 - g), "REPLACE")
            if "fa" in w:
                gf.add([v.index], w["fa"] * (1.0 - g), "REPLACE")
            n += 1
        out[s] = n
    return out
