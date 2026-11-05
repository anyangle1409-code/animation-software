"""Phase 2: bind the manual-retopology male (05a, geometry-proxy fit) to the canonical Home Gym PT skeleton.

* The canonical rig comes from the earlier Meshy bind (MESHY_RIG: canonical bone lengths and joint definitions, A-pose
  rest, at the canonical stature 1.856 m). It is scaled UNIFORMLY to the model's 1.82 m (proportions unchanged) and
  moved front-back so its trunk sits in the retopology trunk.
* Limbs are aimed rigidly (whole subtrees rotate about the joint; no bone length changes) at joints MEASURED on this
  mesh; arms and legs as two-bone chains (end on the measured wrist / ankle as far as the canonical lengths reach,
  elbow / knee on the side of the measured one) and stored on it by the builders: elbow / wrist (TASK4_ARMS), hand frame and finger / thumb tips (t4_part
  tags), knee / ankle / ball / toe tip (TASK5_LEGS). Residuals between the canonical joints and the measured ones are
  reported, not hidden.
* Weights: Blender bone-heat, then rule-based clean-up driven by the builders' part tags:
    - each finger's vertices only follow that finger's chain, its metacarpal and the hand;
    - thumb root / thumb only the thumb chain, the index metacarpal and the hand; palm only hand-region bones;
    - foot only shin / foot / toe, toes only foot / toe;
    - no left / right bleed (vertices off the midline never follow the other side's bones);
    - any vertex bone-heat left unweighted takes its nearest weighted neighbour's weights;
    - at most 4 influences per vertex, normalised.
  Output objects are named MESHY_RIG / MESHY_BODY so scripts/meshy/meshy_pose_test_blender.py runs on it unchanged.

usage: python3.13 bind_retopo_blender.py -- <retopo .blend (05a)> <meshy_bound.blend (canonical rig fit)> <out NEW .blend> <report .json>
"""
import json
import math
import sys
from collections import deque
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Matrix, Vector

a = sys.argv[sys.argv.index("--") + 1:]
RETOPO, RIGSRC, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]), Path(a[3])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
STATURE = 1.82
bpy.ops.wm.open_mainfile(filepath=str(RETOPO), load_ui=False)
body_src = bpy.data.objects["HGPT_Male_Task3_Body"]
ARMS = json.loads(body_src["TASK4_ARMS"]); HANDS = json.loads(body_src["TASK4_HANDS"])["sides"]; LEGS = json.loads(body_src["TASK5_LEGS"])
with bpy.data.libraries.load(str(RIGSRC), link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n in ("MESHY_RIG", "MESHY_BODY")]
sc = bpy.context.scene
rig = next(o for o in dst.objects if o.name.startswith("MESHY_RIG")); glb = next(o for o in dst.objects if o.name.startswith("MESHY_BODY"))
sc.collection.objects.link(rig)
body = body_src.copy(); body.data = body_src.data.copy(); body.name = "MESHY_BODY_RETOPO"; sc.collection.objects.link(body)
for o in list(sc.objects):
    if o not in (rig, body):
        bpy.data.objects.remove(o, do_unlink=True)
rep = {"method": __doc__.split("usage")[0].strip(), "rig_source": RIGSRC.name}

# ---- uniform scale to 1.82 m, front-back placement from the trunk
GV = np.array([glb.matrix_world @ v.co for v in glb.data.vertices]) if glb.data else None
k = STATURE / float(GV[:, 2].max() - GV[:, 2].min())
BV = np.array([v.co[:] for v in body.data.vertices])


def trunk_mid_y(V, kk=1.0):
    out = []
    for z in np.arange(1.0, 1.40, 0.02):
        s = V[(np.abs(V[:, 2] - z) < 0.006) & (np.abs(V[:, 0]) < 0.12)]
        if len(s) > 10:
            out.append((s[:, 1].min() + s[:, 1].max()) / 2)
    return float(np.mean(out))


dy = trunk_mid_y(BV) - trunk_mid_y(GV * k)
gm = glb.data; bpy.data.objects.remove(glb, do_unlink=True); bpy.data.meshes.remove(gm)   # the earlier GLB mesh: only its trunk was used
body.name = "MESHY_BODY"; rig.name = "MESHY_RIG"
rig.matrix_world = Matrix.Translation((0, dy, 0)) @ Matrix.Diagonal((k, k, k, 1.0))
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = rig; rig.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
rep.update(scale=round(k, 5), trunk_shift_y_m=round(dy, 4))
pb = rig.pose.bones; MW = rig.matrix_world; W2A = MW.to_3x3().inverted(); wp = lambda v: MW @ v
for p in pb:
    p.matrix_basis = Matrix()
bpy.context.view_layer.update()


def subtree(root):
    return [root] + [c.name for c in pb[root].children_recursive]


def rot_rigid(names, piv_w, R3):
    piv = Vector(piv_w); D = Matrix.Translation(piv) @ R3.to_4x4() @ Matrix.Translation(-piv)
    mats = {n: pb[n].matrix.copy() for n in names}
    for n in names:                                   # parents first; each assignment needs the updated parent pose
        pb[n].matrix = D @ mats[n]; bpy.context.view_layer.update()


def aim(root, bone, target_w, head=None):
    b = pb[bone]; h = wp(b.head) if head is None else head; cur = (wp(b.tail) - h).normalized(); tgt = (Vector(target_w) - h).normalized()
    ang = cur.angle(tgt); ax = cur.cross(tgt)
    if ax.length > 1e-8:
        rot_rigid(subtree(root), wp(b.head), Matrix.Rotation(ang, 3, ax.normalized()))
    return round(math.degrees(ang), 1)


def roll_to(root, axis_w, cur_w, tgt_w, piv_w):
    """rotate subtree about axis so that cur (projected) turns onto tgt (projected)"""
    ax = Vector(axis_w).normalized(); c = Vector(cur_w) - ax * Vector(cur_w).dot(ax); t = Vector(tgt_w) - ax * Vector(tgt_w).dot(ax)
    ang = c.angle(t); sgn = 1 if c.cross(t).dot(ax) > 0 else -1
    rot_rigid(subtree(root), piv_w, Matrix.Rotation(sgn * ang, 3, ax)); return round(math.degrees(sgn * ang), 1)


def two_bone(upper, lower, end_w, mid_w):
    """aim upper / lower so the chain ends as near end_w as the canonical lengths allow, the middle joint on the side of
    the measured one (mid_w); returns the middle joint actually used"""
    H = wp(pb[upper].head); a_ = (wp(pb[upper].tail) - H).length; b_ = (wp(pb[lower].tail) - wp(pb[lower].head)).length
    T = Vector(end_w); M = Vector(mid_w); d = min((T - H).length, a_ + b_ - 1e-4); u = (T - H).normalized()
    x = (a_ * a_ - b_ * b_ + d * d) / (2 * d); r = math.sqrt(max(a_ * a_ - x * x, 0.0))
    v = (M - H) - u * (M - H).dot(u); v = v.normalized() if v.length > 1e-6 else Vector((0, 0, 0))
    J = H + u * x + v * r
    aim(upper, upper, J); aim(lower, lower, T)
    return J


# tagged vertex positions
bm = bmesh.new(); bm.from_mesh(body.data); L4 = bm.verts.layers.int["t4_part"]
TAG4 = {}
for v in bm.verts:
    if v[L4]:
        TAG4.setdefault((1 if v.co.x > 0 else -1, v[L4]), []).append(np.array(v.co[:]))
FING = ["index", "middle", "ring", "pinky"]
fit = {}
for sd, sg, side in (("r", 1, "right"), ("l", -1, "left")):
    A = ARMS[side]; H = HANDS[side]; G = LEGS[side]; f = {}
    E, Wr = Vector(A["elbow"]), Vector(A["wrist"])
    two_bone(f"upperarm_{sd}", f"forearm_{sd}", Wr, E)
    f["elbow_vs_measured_mm"] = round((wp(pb[f"forearm_{sd}"].head) - E).length * 1000, 1)
    f["wrist_residual_mm"] = round((wp(pb[f"hand_{sd}"].head) - Wr).length * 1000, 1)
    L, Wd = Vector(H["L"]), Vector(H["Wd"])
    hh = wp(pb[f"hand_{sd}"].head)
    mm = pb[f"metacarpal_middle_{sd}"]
    f["hand_deg"] = aim(f"hand_{sd}", f"metacarpal_middle_{sd}", wp(mm.head) + L, head=wp(mm.head))
    across = wp(pb[f"metacarpal_pinky_{sd}"].head) - wp(pb[f"metacarpal_index_{sd}"].head)
    f["hand_roll_deg"] = roll_to(f"hand_{sd}", L, across, Wd, hh)
    Wc = np.array(A["wrist"])
    for i, nm in enumerate(FING):
        P = np.array(TAG4[(sg, 10 + i)]); tip = P[np.argmax((P - Wc) @ np.array(H["L"]))]
        f[f"{nm}_deg"] = aim(f"{nm}_01_{sd}", f"{nm}_01_{sd}", Vector(tip))
        f[f"{nm}_tip_residual_mm"] = round((wp(pb[f"{nm}_03_{sd}"].tail) - Vector(tip)).length * 1000, 1)
    P = np.array(TAG4[(sg, 21)]); ttip = P[np.argmax(np.linalg.norm(P - Wc, axis=1))]
    f["thumb_deg"] = aim(f"thumb_01_{sd}", f"thumb_01_{sd}", Vector(ttip))
    f["thumb_tip_residual_mm"] = round((wp(pb[f"thumb_03_{sd}"].tail) - Vector(ttip)).length * 1000, 1)
    K, An = Vector(G["knee"]), Vector(G["ankle_corner"]); heel, tip = np.array(G["heel"]), np.array(G["toe_tip"])
    ball = heel + 0.72 * (tip - heel); ball[2] = 0.025
    two_bone(f"thigh_{sd}", f"shin_{sd}", An, K)
    f["knee_vs_measured_mm"] = round((wp(pb[f"shin_{sd}"].head) - K).length * 1000, 1)
    f["ankle_residual_mm"] = round((wp(pb[f"foot_{sd}"].head) - An).length * 1000, 1)
    f["foot_deg"] = aim(f"foot_{sd}", f"foot_{sd}", Vector(ball))
    f["toe_deg"] = aim(f"toe_{sd}", f"toe_{sd}", Vector(tip))
    f["ball_residual_mm"] = round((wp(pb[f"toe_{sd}"].head) - Vector(ball)).length * 1000, 1)
    fit[side] = f
rep["fit"] = fit
bpy.ops.object.mode_set(mode="POSE"); bpy.ops.pose.select_all(action="SELECT"); bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode="OBJECT")
SKIP = ("root", "forearm_tw0", "shoulder_cap", "muscle_", "hip_crease")
for b in rig.data.bones:
    b.use_deform = not any(b.name.startswith(s) for s in SKIP)
# ---- weights: bone heat
for o in bpy.context.selected_objects:
    o.select_set(False)
body.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
me = body.data; NV = len(me.vertices); gi = {g.index: g.name for g in body.vertex_groups}
Wt = [dict() for _ in range(NV)]
for v in me.vertices:
    for g in v.groups:
        if g.weight > 1e-5:
            Wt[v.index][gi[g.group]] = g.weight
unweighted = [i for i in range(NV) if not Wt[i]]
rep["bone_heat_unweighted_vertices"] = len(unweighted)
# ---- clean-up rules
bm.verts.ensure_lookup_table(); L5 = bm.verts.layers.int["t5_part"]
CENTRAL = {"pelvis", "spine_01", "spine_02", "spine_03", "neck", "head"}


def allowed(v):
    t4, t5, x = v[L4], v[L5], v.co.x
    sd = "r" if x > 0 else "l"
    if 10 <= t4 <= 13:
        n = FING[t4 - 10]; return {f"hand_{sd}", f"metacarpal_{n}_{sd}", f"{n}_01_{sd}", f"{n}_02_{sd}", f"{n}_03_{sd}"}
    if t4 in (20, 21):
        return {f"hand_{sd}", f"thumb_01_{sd}", f"thumb_02_{sd}", f"thumb_03_{sd}", f"metacarpal_index_{sd}"}
    if t4 == 1:
        return {f"hand_{sd}", f"forearm_tw1_{sd}", f"thumb_01_{sd}"} | {f"metacarpal_{n}_{sd}" for n in FING} | {f"{n}_01_{sd}" for n in FING}
    if t5 == 8:
        return {f"foot_{sd}", f"toe_{sd}"}
    if t5 == 7:
        return {f"shin_{sd}", f"foot_{sd}", f"toe_{sd}"}
    return None


changed = 0
for v in bm.verts:
    w = Wt[v.index]; al = allowed(v); x = v.co.x
    keep = {}
    for n, val in w.items():
        if al is not None and n not in al:
            continue
        if abs(x) > 0.02 and n not in CENTRAL and n.endswith("_l" if x > 0 else "_r"):
            continue
        keep[n] = val
    if len(keep) != len(w):
        changed += 1
    Wt[v.index] = keep
# fill vertices left empty (bone heat failures, or everything removed) from the nearest weighted neighbours
empty = [i for i in range(NV) if not Wt[i]]; rep["vertices_filled_from_neighbours"] = len(empty)
q = deque(empty); seen = 0
while q and seen < 20 * NV:
    i = q.popleft(); seen += 1
    nb = [e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges]; acc = {}
    for j in nb:
        for n, val in Wt[j].items():
            acc[n] = acc.get(n, 0.0) + val
    al = allowed(bm.verts[i])
    acc = {n: val for n, val in acc.items() if al is None or n in al}
    if acc:
        Wt[i] = acc
    else:
        q.append(i)
for i in range(NV):
    top = sorted(Wt[i].items(), key=lambda kv: -kv[1])[:4]; s = sum(val for _, val in top)
    Wt[i] = {n: val / s for n, val in top} if s > 0 else {}
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
groups = {}
for i in range(NV):
    for n, val in Wt[i].items():
        if n not in groups:
            groups[n] = body.vertex_groups.new(name=n)
        groups[n].add([i], val, "REPLACE")
rep.update(vertices=NV, vertices_changed_by_rules=changed, still_unweighted=sum(1 for w in Wt if not w),
           max_influences=max(len(w) for w in Wt), deform_groups=len(groups))
body["PHASE2_BIND"] = json.dumps({k_: v_ for k_, v_ in rep.items() if k_ != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT)
REP.write_text(json.dumps(rep, indent=1)); print("BIND", json.dumps({k_: v_ for k_, v_ in rep.items() if k_ != "method"}))
