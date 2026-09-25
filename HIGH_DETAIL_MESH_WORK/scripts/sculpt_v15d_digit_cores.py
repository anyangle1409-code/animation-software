"""Candidate-only V15d finger-shaft reconstruction in the prepared Blender file.

Keeps every original vertex and all fixed anchor positions. Rebuilds the radial
cross-section of each four-finger shaft and redirects triangulation along the
shaft where a safe, entirely internal triangle pair permits it.
"""
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15d_deep_hand_rebuild.blend"
REPORT = ROOT / "reports" / "sculpt_v15d_digit_cores.json"
body = bpy.data.objects["Mike_Freeman"]
arm = bpy.data.objects["HomeGymPT_Male_Rig"]
mesh = body.data
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
deform = bm.verts.layers.deform.active
group_ids = {g.name: g.index for g in body.vertex_groups}


def members(name):
    gid = group_ids[name]
    return {v for v in bm.verts if v[deform].get(gid, 0.0) > 0.5}


def chain_for(digit, side):
    p = f"DEF-f_{digit}."
    bones = arm.data.bones
    return [bones[p + "01." + side].head_local.copy()] + [
        bones[p + f"{i:02d}." + side].tail_local.copy() for i in (1, 2, 3)
    ]


def projection(point, chain):
    best = None
    arc = 0.0
    for a, b in zip(chain[:-1], chain[1:]):
        axis = b - a
        length = axis.length
        if length < 1e-9:
            continue
        t = max(0.0, min(1.0, (point - a).dot(axis) / (length * length)))
        foot = a + t * axis
        d = (point - foot).length_squared
        item = (d, arc + t * length, axis.normalized())
        if best is None or d < best[0]:
            best = item
        arc += length
    return best[1], best[2]


def frame(tangent):
    guide = Vector((0, 0, 1))
    if abs(tangent.dot(guide)) > 0.9:
        guide = Vector((1, 0, 0))
    u = tangent.cross(guide).normalized()
    v = tangent.cross(u).normalized()
    return u, v


def gaussian(x, sigma):
    return math.exp(-0.5 * (x / sigma) ** 2)


results = {}
initial = {v: v.co.copy() for v in bm.verts}
all_cores = {}
for digit in ("index", "middle", "ring", "pinky"):
    for side in ("L", "R"):
        key = f"{digit.upper()}_{side}"
        owned = members("V15_" + key)
        core = members("V15_" + key + "_CORE")
        anchor = members("V15_" + key + "_ANCHOR")
        chain = chain_for(digit, side)
        all_cores[key] = core
        projected = {v: projection(v.co, chain) for v in owned}
        max_arc = max(projected[v][0] for v in owned)
        pip_arc = (chain[1] - chain[0]).length
        dip_arc = pip_arc + (chain[2] - chain[1]).length

        # Cross-sectional centres are estimated from the actual skin surface,
        # not the bone tail, which can extend well past the visible fingertip.
        stations = []
        step = 0.002
        for i in range(int(max_arc / step) + 2):
            arc = i * step
            neighbours = [(v, gaussian(projected[v][0] - arc, 0.0035))
                          for v in owned if abs(projected[v][0] - arc) < 0.010]
            neighbours = [(v, w) for v, w in neighbours if w > 0.02]
            if len(neighbours) < 7:
                stations.append(None)
                continue
            total = sum(w for _, w in neighbours)
            centre = sum((v.co * w for v, w in neighbours), Vector()) / total
            tangent = min(projected.items(), key=lambda item: abs(item[1][0] - arc))[1][1]
            u, w_axis = frame(tangent)
            # RMS -> surface radius for a reasonably sampled elliptical ring.
            ru = math.sqrt(2 * sum(w * ((v.co - centre).dot(u)) ** 2
                                   for v, w in neighbours) / total)
            rv = math.sqrt(2 * sum(w * ((v.co - centre).dot(w_axis)) ** 2
                                   for v, w in neighbours) / total)
            stations.append((centre, tangent, u, w_axis, ru, rv))

        # Smooth the sampled radius along the shaft, removing angular bands.
        # Keep a modest knuckle swell, taper the terminal phalanx. The 0.70
        # radial blend deliberately changes the visible silhouette while
        # retaining V13e's positional identity and contact envelope.
        targets = {}
        for vertex in core:
            arc, tangent = projected[vertex]
            candidates = [(j, gaussian(j * step - arc, 0.005)) for j, s in enumerate(stations)
                          if s is not None and abs(j * step - arc) < 0.014]
            if not candidates:
                continue
            total = sum(w for _, w in candidates)
            centre = sum((stations[j][0] * w for j, w in candidates), Vector()) / total
            u, v_axis = frame(tangent)
            ru = sum(stations[j][4] * w for j, w in candidates) / total
            rv = sum(stations[j][5] * w for j, w in candidates) / total
            # Minimise the swollen joint band while retaining real PIP/DIP
            # articulation volumes and a gentle distal taper.
            joint = 1.0 + 0.035 * gaussian(arc - pip_arc, 0.0045) \
                         + 0.02 * gaussian(arc - dip_arc, 0.0035)
            tip = max(0.75, min(1.0, (max_arc - arc) / 0.012))
            ru *= joint * tip
            rv *= joint * tip
            rel = vertex.co - centre
            cu = rel.dot(u)
            cv = rel.dot(v_axis)
            theta = math.atan2(cv / max(rv, 1e-6), cu / max(ru, 1e-6))
            target = centre + ru * math.cos(theta) * u + rv * math.sin(theta) * v_axis
            # Preserve lengthwise location. Anchor transition is fixed by
            # membership; neighbouring core vertices are tapered by graph
            # distance so there is no newly visible boundary ridge.
            delta = target - vertex.co
            delta -= tangent * delta.dot(tangent)
            boundary_gap = min((vertex.co - a.co).length for a in anchor) if anchor else 1.0
            feather = min(1.0, boundary_gap / 0.006)
            delta *= 0.52 * feather
            if delta.length > 0.0018:
                delta.length = 0.0018
            targets[vertex] = vertex.co + delta
        for vertex, pos in targets.items():
            vertex.co = pos
        results[key] = {"owned": len(owned), "core": len(core), "moved": len(targets),
                        "max_move_mm": max(((initial[v] - v.co).length * 1000 for v in targets), default=0.0)}

# Insert PIP/DIP control stations along longitudinal shaft edges. Original
# vertices remain in the mesh; export prep interpolates new UVs and weights.
sid = bm.verts.layers.int.get("v8_source_id")
tracking = bm.verts.layers.int.get("v15_baseline_vertex_id")
added_total = 0
for key, core in all_cores.items():
    chain = chain_for(key.rsplit("_", 1)[0].lower(), key[-1])
    pip = (chain[1] - chain[0]).length
    dip = pip + (chain[2] - chain[1]).length
    selected = []
    for edge in bm.edges:
        if len(edge.link_faces) != 2 or any(v not in core for v in edge.verts):
            continue
        mid = (edge.verts[0].co + edge.verts[1].co) / 2
        arc, tangent = projection(mid, chain)
        if min(abs(arc - pip), abs(arc - dip)) > 0.008:
            continue
        length = edge.calc_length()
        if length < 0.0025:
            continue
        axial = abs((edge.verts[1].co - edge.verts[0].co).normalized().dot(tangent))
        if axial < 0.62:
            continue
        selected.append((length, edge))
    edges = [e for _, e in sorted(selected, key=lambda row: row[0], reverse=True)[:160]]
    if not edges:
        results[key]["joint_control_vertices"] = 0
        continue
    operation = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=False)
    new = [item for item in operation["geom_inner"] if isinstance(item, bmesh.types.BMVert)]
    targets = {}
    for vertex in new:
        neighbours = [e.other_vert(vertex) for e in vertex.link_edges]
        if not neighbours:
            continue
        mean = sum((v.co for v in neighbours), Vector()) / len(neighbours)
        move = (mean - vertex.co) * 0.28
        if move.length > 0.00055:
            move.length = 0.00055
        targets[vertex] = vertex.co + move
    for vertex, pos in targets.items():
        vertex.co = pos
        if sid is not None:
            vertex[sid] = 0
        if tracking is not None:
            vertex[tracking] = 0
    results[key]["joint_control_vertices"] = len(new)
    added_total += len(new)

# Redirect internal diagonals from broad cross-shaft cuts toward longitudinal
# flow. Only rotate a well-conditioned pair of core-owned triangles, retaining
# all existing vertices, UV loops and skin rows.
bm.normal_update()
flips = 0
for key, core in all_cores.items():
    chain = chain_for(key.rsplit("_", 1)[0].lower(), key[-1])
    candidates = []
    for edge in list(bm.edges):
        if not edge.is_valid or len(edge.link_faces) != 2 or any(v not in core for v in edge.verts):
            continue
        f1, f2 = edge.link_faces
        if len(f1.verts) != 3 or len(f2.verts) != 3 or f1.normal.dot(f2.normal) < 0.72:
            continue
        opp = [v for f in (f1, f2) for v in f.verts if v not in edge.verts]
        if len(opp) != 2 or any(v not in core for v in opp):
            continue
        if bm.edges.get((opp[0], opp[1])) is not None:
            continue
        mid = (edge.verts[0].co + edge.verts[1].co) / 2
        tangent = projection(mid, chain)[1]
        old_axis = (edge.verts[1].co - edge.verts[0].co).normalized()
        new_axis = (opp[1].co - opp[0].co).normalized()
        gain = abs(new_axis.dot(tangent)) - abs(old_axis.dot(tangent))
        if gain < 0.18 or (opp[1].co - opp[0].co).length > edge.calc_length() * 1.65:
            continue
        a, b = edge.verts
        c, d = opp
        n1 = (d.co - c.co).cross(a.co - c.co)
        n2 = (d.co - c.co).cross(b.co - c.co)
        if n1.length < 1e-8 or n2.length < 1e-8:
            continue
        # Only redirect the diagonal if the resulting two triangles are more
        # coplanar than the inherited pair. This rejects V15a's sharp folds.
        prospective = abs(n1.normalized().dot(n2.normalized()))
        previous = abs(f1.normal.dot(f2.normal))
        if prospective < previous + 0.06 or prospective < 0.94:
            continue
        candidates.append((gain, edge))
    local = 0
    used = set()
    for _, edge in sorted(candidates, key=lambda row: row[0], reverse=True):
        if local >= 45 or not edge.is_valid or any(f in used for f in edge.link_faces):
            continue
        old_faces = tuple(edge.link_faces)
        try:
            result = bmesh.ops.rotate_edges(bm, edges=[edge], use_ccw=False)
        except (RuntimeError, ValueError):
            continue
        if result.get("edges"):
            local += 1
            used.update(old_faces)
    results[key]["longitudinal_edge_flips"] = local
    flips += local

bm.to_mesh(mesh)
bm.free()
mesh.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
REPORT.parent.mkdir(exist_ok=True)
REPORT.write_text(json.dumps({"digits": results, "total_edge_flips": flips,
                              "new_joint_control_vertices": added_total}, indent=2))
print("V15_SCULPT", json.dumps({"digits": results, "total_edge_flips": flips,
                               "new_joint_control_vertices": added_total}), flush=True)
