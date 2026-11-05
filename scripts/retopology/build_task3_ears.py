"""Task 3 ears (first pass): close each ear-base opening of the Task-3 body with a quad grid on the ear's outer relief.

The opening is the shell's ear rectangle (columns JE0..JE1, loops I_EAR0..I_EAR1, tagged t3_row / t3_col). Three rings run
inside the opening (the helix band), then a Coons-patch grid of the same column / row counts closes it (all quads, no poles), laid out in the side (y, z) plane and
projected onto the source by rays from outside the head towards the midline, so the vertices land on the helix,
antihelix, concha and lobe as seen from the side.  Limitation (documented): the gap behind the ear is not modelled -
seen from behind, the ear reads as solid. A separate ear mesh with the undercut is a later refinement.

usage: python3.13 build_task3_ears.py -- <face checkpoint .blend (03i)> <out NEW .blend> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
SRC = bpy.data.objects["HGPT_SOURCE_PROXY_Mesh_0"]; body = bpy.data.objects["HGPT_Male_Task3_Body"]
SV = np.array([v.co[:] for v in SRC.data.vertices]); bvh = BVHTree.FromPolygons([tuple(v) for v in SV], [tuple(p.vertices) for p in SRC.data.polygons])
D = json.loads(body["TASK3_SHELL_DESIGN"]); I0, I1 = D["ear_rows"]
DD = json.loads(json.dumps(D))
NSEG = D["segments_per_half_loop"]
me = body.data; bm = bmesh.new(); bm.from_mesh(me)
LR = bm.verts.layers.int["t3_row"]; LC = bm.verts.layers.int["t3_col"]
# ear columns: the boundary columns of the ear opening (from the tagged boundary vertices)
cols = sorted({v[LC] for v in bm.verts if v.is_boundary and I0 <= v[LR] <= I1 and 0 < v[LC] < NSEG})
JE0, JE1 = cols[0], cols[-1]
rep = {"ear_rows": [I0, I1], "ear_cols": [JE0, JE1], "sides": {}}
EAR_RING_SCALES = (0.86, 0.73, 0.60)                                   # rings inside the opening (helix band)


def side_hit(y, z, sg):
    """first surface hit of a ray from outside the head (x = sg * 0.30) towards the midline"""
    h = bvh.ray_cast(Vector((sg * 0.30, y, z)), Vector((-sg, 0.0, 0.0)))[0]
    if h is None:
        raise RuntimeError(f"no ear surface at y {y} z {z}")
    return h


for sg in (1.0, -1.0):
    S = {}
    for v in bm.verts:
        if v.is_boundary and I0 <= v[LR] <= I1 and JE0 <= v[LC] <= JE1 and v.co.x * sg > 0.03:
            S[v[LR], v[LC]] = v
    R_, C_ = I1 - I0, JE1 - JE0
    need = [(I0, c) for c in range(JE0, JE1 + 1)] + [(I1, c) for c in range(JE0, JE1 + 1)] + [(r, JE0) for r in range(I0, I1 + 1)] + [(r, JE1) for r in range(I0, I1 + 1)]
    missing = [k for k in need if k not in S]
    if missing:
        raise RuntimeError(f"ear boundary incomplete on side {sg}: {missing[:5]}")
    yz = lambda v: np.array([v.co.y, v.co.z])
    B = [yz(S[I0, c]) for c in range(JE0, JE1 + 1)]; T = [yz(S[I1, c]) for c in range(JE0, JE1 + 1)]
    L = [yz(S[r, JE0]) for r in range(I0, I1 + 1)]; Rr = [yz(S[r, JE1]) for r in range(I0, I1 + 1)]
    # concentric rings inside the opening (the helix runs just inside the ear base), then a C_ x R_ grid on the
    # innermost ring for the concha / antihelix; all quads, no poles
    loop = [(I0, c) for c in range(JE0, JE1)] + [(r, JE1) for r in range(I0, I1)] + [(I1, c) for c in range(JE1, JE0, -1)] + [(r, JE0) for r in range(I1, I0, -1)]
    P0 = np.array([yz(S[k]) for k in loop]); ctr = P0.mean(0); nl = len(loop)
    rings = [[S[k] for k in loop]]; ring2 = [P0]
    for k, f in enumerate(EAR_RING_SCALES):
        Pk = ctr + (P0 - ctr) * f; ring2.append(Pk)
        rings.append([bm.verts.new(side_hit(p[0], p[1], sg)) for p in Pk])
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for i in range(nl):
            bm.faces.new([a_[i], a_[(i + 1) % nl], b_[(i + 1) % nl], b_[i]])
    inner = rings[-1]; P2 = ring2[-1]; idx = {k: i for i, k in enumerate(loop)}
    B = [P2[idx[I0, c]] for c in range(JE0, JE1 + 1)] if (I0, JE1) in idx else None
    Bk = [(I0, c) for c in range(JE0, JE1 + 1)]; Tk = [(I1, c) for c in range(JE0, JE1 + 1)]
    Lk = [(r, JE0) for r in range(I0, I1 + 1)]; Rk = [(r, JE1) for r in range(I0, I1 + 1)]
    B = [P2[idx[k]] for k in Bk]; T = [P2[idx[k]] for k in Tk]; L = [P2[idx[k]] for k in Lk]; Rr = [P2[idx[k]] for k in Rk]
    g = {}
    for i in range(R_ + 1):
        for j in range(C_ + 1):
            if i == 0:
                g[i, j] = inner[idx[Bk[j]]]; continue
            if i == R_:
                g[i, j] = inner[idx[Tk[j]]]; continue
            if j == 0:
                g[i, j] = inner[idx[Lk[i]]]; continue
            if j == C_:
                g[i, j] = inner[idx[Rk[i]]]; continue
            u, w = j / C_, i / R_
            p = ((1 - w) * B[j] + w * T[j] + (1 - u) * L[i] + u * Rr[i]
                 - ((1 - u) * (1 - w) * B[0] + u * (1 - w) * B[-1] + (1 - u) * w * T[0] + u * w * T[-1]))
            g[i, j] = bm.verts.new(side_hit(p[0], p[1], sg))
    new = [g[i, j] for i in range(1, R_) for j in range(1, C_)] + [v for rg in rings[1:] for v in rg]
    for i in range(R_):
        for j in range(C_):
            bm.faces.new([g[i, j], g[i, j + 1], g[i + 1, j + 1], g[i + 1, j]])
    for _ in range(4):                                        # light relax in the side plane, re-projected sideways
        upd = {}
        for v in new:
            nb = [e.other_vert(v) for e in v.link_edges]; avg = sum((w_.co for w_ in nb), Vector()) / len(nb)
            p = v.co.lerp(avg, 0.4); upd[v] = side_hit(p.y, p.z, sg)
        for v, p in upd.items():
            v.co = p
    rep["sides"]["right" if sg > 0 else "left"] = {"grid": [C_, R_], "new_vertices": len(new), "rings": len(EAR_RING_SCALES), "faces": C_ * R_ + len(EAR_RING_SCALES) * nl}
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); me.update()
body["TASK3_EARS"] = json.dumps({**rep, "method": "Coons grid on the ear rectangle, lateral-ray projection; no back-of-ear undercut"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
bnd = sum(e.is_boundary for e in bm.edges)
rep.update({"out": str(OUT), "faces": len(bm.faces), "non_quads": sum(len(f.verts) != 4 for f in bm.faces), "boundary_edges": bnd})
REP.write_text(json.dumps(rep, indent=1)); print("EARS", json.dumps(rep))
