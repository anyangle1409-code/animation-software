"""Neck-to-shoulder weight gradient for ORIGINAL_v1 review candidates (bpy; weights only).  R14 (Claude, 15 Oct 2026).

Owner, comparing the press with a 7-view reference photo series: at the top of the press the skin across the top of the
shoulder formed a flat shelf from the neck to the raised arm (back view) where the reference shows the trapezius sloping up
into the arm.  Cause: across the top of the shoulder the skin switched from following the head/neck (static in a press) to
following the clavicle/scapula (elevated ~26 deg + the lockout shrug) within ~3 cm, x 90 -> 120 mm from the midline.

Here the girdle share of each vertex on top of the shoulder (clavicle + scapula, against head + neck + spine_03) is set to a
smoothstep of its distance from the midline, X0 -> X1, faded in from ZLO below the AC joint height and out towards ZHI above
it and towards +-YW front/back; only vertices that already carry some girdle weight change; the clavicle:scapula and
head:neck:spine_03 splits are kept.  No bones, no influences added.
"""
from __future__ import annotations

X0, X1 = 0.03, 0.20          # m from the midline: girdle share 0 -> 1
ZLO, ZHI = -0.05, 0.14       # m relative to the AC joint height
YW = 0.12                    # m front/back of the AC joint
SIDES = ("l", "r")


def _smooth(t, a, b):
    x = min(1.0, max(0.0, (t - a) / (b - a)))
    return x * x * (3 - 2 * x)


def assign_weights(body, rig, x0=X0, x1=X1, zlo=ZLO, zhi=ZHI, yw=YW):
    changed = {}
    for s in SIDES:
        names = {g.index: g.name for g in body.vertex_groups}
        sign = 1.0 if s == "r" else -1.0                       # F-SIDE-001: runtime _r is +X
        ac = rig.data.bones[f"clavicle_{s}"].tail_local
        gird, neck = (f"clavicle_{s}", f"scapula_{s}"), ("head", "neck", "spine_03")
        n = 0
        for v in body.data.vertices:
            p = v.co
            x = p.x * sign
            if x <= 0.0 or x > x1 + 0.02 or abs(p.y - ac.y) > yw:
                continue
            dz = p.z - ac.z
            if dz < zlo or dz > zhi:
                continue
            w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
            tot = sum(w.values())
            w = {k: x_ / tot for k, x_ in w.items()}
            G = sum(w.get(k, 0.0) for k in gird)
            N = sum(w.get(k, 0.0) for k in neck)
            M = G + N
            if M < 0.3 or G < 1e-4:
                continue
            u = _smooth(x, x0, x1)
            fade = _smooth(dz, zlo, zlo + 0.03) * (1 - _smooth(dz, zhi - 0.04, zhi)) * (1 - _smooth(abs(p.y - ac.y), yw - 0.04, yw))
            g_new = G + fade * (M * u - G)
            n_new = M - g_new
            for k in gird:
                if k in w:
                    body.vertex_groups[k].add([v.index], g_new * w[k] / G, "REPLACE")
            for k in neck:
                if k in w and N > 1e-9:
                    body.vertex_groups[k].add([v.index], n_new * w[k] / N, "REPLACE")
            n += 1
        changed[s] = n
    rig["hgpt_trap_gradient"] = {"x_m": [x0, x1], "z_m": [zlo, zhi], "y_m": yw}
    return changed
