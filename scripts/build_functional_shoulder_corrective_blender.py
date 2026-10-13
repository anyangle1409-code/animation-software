"""Provisional W2 pose-space shoulder correctives solved against the coupled 0-160 motion (diagnostic candidate).

Stacked on build_functional_shoulder_correction_blender (PR111).  For each key pose (100..160 deg, 10 deg apart,
warm-started) the posed original skin is relaxed in posed space only where it fails (edge-length springs with volume
pressure, light fairing, separation of self-intersecting faces, push-out of torso skin that sinks inside a closed
convex thorax hull built from the rib guides), then mapped back to a rest-space delta by DAMPED least squares through
each vertex's linear-blend skinning matrix (plain LBS, normalized, at most four influences; the forward matrix is
verified against Blender's own evaluation).  Near 160 deg some blended matrices are nearly singular (smallest singular
value ~0.003), so an undamped inverse produced metre-scale rest deltas that exploded between keys; the damping and a
hard per-vertex cap bound every rest delta.  Deltas are made bilaterally symmetric and added as seven in-memory shape
keys driven by functional_coupled_corrective.key_weights.
Nothing is saved to the source blend.  No anatomy, deformation, GLB, clinical or production approval.
"""

from __future__ import annotations

import json
import math
import sys
from collections import deque
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_functional_shoulder_correction_blender as correction
import functional_coupled_corrective as contract

attachment = correction.attachment
KEY_PREFIX = "HGPT_W_COUPLED_CORR_"
ZONE_RINGS = 6
MAX_ITERATIONS = 300
PUSH_STEP_M = 0.0006
SMOOTHING = "springs"         # "springs" (rest edge lengths + volume pressure), "taubin" or "laplacian"
SPRING_K = 0.5
PRESSURE_GAIN = 0.5
FAIRING_LAMBDA = 0.15
LAPLACIAN_LAMBDA = 0.5
USE_PUSH = True
PUSH_FIELD_RINGS = 6
PUSH_FIELD_PASSES = 10
DAMPING = 0.01                # Tikhonov lambda for the rest-delta solve (|sigma|^2 + lambda), dimensionless
DELTA_CAP_M = 0.030           # hard cap on any rest-space corrective delta
RIB_CLEARANCE_M = contract.TARGETS["rib_guide_clearance_min_mm"] / 1000.0


# ----------------------------------------------------------------------------------------------- skinning inverse
def skin_matrices(runtime, body):
    deform = {b.name for b in runtime.data.bones if b.use_deform}
    names = {g.index: g.name for g in body.vertex_groups}
    bone_m = {n: runtime.pose.bones[n].matrix @ runtime.data.bones[n].matrix_local.inverted() for n in deform}
    out = []
    for v in body.data.vertices:
        m = Matrix(((0.0,) * 4,) * 4)
        total = 0.0
        for g in v.groups:
            n = names[g.group]
            if n in bone_m and g.weight > 0.0:
                m = m + bone_m[n] * g.weight
                total += g.weight
        if total <= 0.0:
            raise RuntimeError(f"vertex {v.index} has no deforming weight")
        out.append(m * (1.0 / total))
    return out


def verify_lbs(result, matrices, posed):
    body = result["body"]
    err = max((matrices[i] @ v.co - posed[i]).length for i, v in enumerate(body.data.vertices))
    if err > 1e-5:
        raise RuntimeError(f"linear-blend inverse does not reproduce Blender evaluation ({err} m)")
    return err


# ----------------------------------------------------------------------------------------------- mesh helpers
def _adjacency(n, faces):
    adj = [set() for _ in range(n)]
    for a, b, c in faces:
        adj[a].update((b, c)); adj[b].update((a, c)); adj[c].update((a, b))
    return [list(s) for s in adj]


def _normal(V, f):
    a, b, c = V[f[0]], V[f[1]], V[f[2]]
    n = (b - a).cross(c - a)
    return n.normalized() if n.length > 1e-14 else Vector((0.0, 0.0, 0.0))


def _vertex_faces(n, faces):
    out = [[] for _ in range(n)]
    for i, f in enumerate(faces):
        for v in f:
            out[v].append(i)
    return out


def _spring_step(T, V0, F, adj, zone, vertex_faces, vol_target, lam_fair):
    """One Jacobi step: pull zone edges toward rest length, add volume pressure along vertex normals, light fairing."""
    acc = {}
    for v, w in zone.items():
        if w <= 0.0:
            continue
        total = Vector()
        for n in adj[v]:
            d = T[n] - T[v]
            L = d.length
            if L > 1e-12:
                L0 = (V0[n] - V0[v]).length
                total += d * ((L - L0) / L) * 0.5
        acc[v] = total / len(adj[v]) * (SPRING_K * w)
    vol = correction._volume(T, F)
    zone_area = 0.0
    normals = {}
    for v in acc:
        nrm = Vector()
        for f in vertex_faces[v]:
            a, b, c = T[F[f][0]], T[F[f][1]], T[F[f][2]]
            cr = (b - a).cross(c - a)
            nrm += cr
            zone_area += cr.length / 6.0
        normals[v] = nrm.normalized() if nrm.length > 1e-14 else Vector()
    pressure = PRESSURE_GAIN * (vol_target - vol) / max(zone_area, 1e-9)
    for v, d in acc.items():
        T[v] = T[v] + d + normals[v] * (pressure * zone[v])
    if lam_fair > 0.0:
        new = {}
        for v, w in zone.items():
            if w > 0.0:
                avg = sum((T[n] for n in adj[v]), Vector()) / len(adj[v])
                new[v] = T[v] + (avg - T[v]) * (lam_fair * w)
        for v, p in new.items():
            T[v] = p


def _intersections(V, F, region_faces):
    tree = BVHTree.FromPolygons(V, F, all_triangles=True)
    reg = region_faces
    out = []
    for a, b in tree.overlap(tree):
        if a < b and (a in reg or b in reg) and not (set(F[a]) & set(F[b])):
            out.append((a, b))
    return out


def _problem_zone(V0, V, F, adj, movable, region_faces, pairs):
    bad_vertices = set()
    for i in region_faces:
        a0 = correction._area(V0, F[i])
        if a0 <= 1e-12:
            continue
        r = correction._area(V, F[i]) / a0
        if r < 0.5 or r > 2.5:
            bad_vertices.update(F[i])
    for a, b in pairs:
        bad_vertices.update(F[a]); bad_vertices.update(F[b])
    weight = {}
    queue = deque((v, 0) for v in bad_vertices if movable[v])
    seen = {v for v, _ in queue}
    while queue:
        v, d = queue.popleft()
        weight[v] = contract.zone_falloff(d, ZONE_RINGS)
        if d < ZONE_RINGS:
            for w in adj[v]:
                if movable[w] and w not in seen:
                    seen.add(w); queue.append((w, d + 1))
    return weight


TORSO_GROUP_PREFIXES = ("spine_", "clavicle_", "scapula_", "pelvis", "chest")   # neck skin is excluded


def _torso_vertices(body, movable, rest_V, z_span):
    """Movable vertices whose dominant deforming group is a trunk/girdle group (not arm or neck skin) and whose rest
    height lies within the rib-guide span."""
    dom = correction._dominant_groups(body)
    lo, hi = z_span
    return [movable[i] and dom[i].startswith(TORSO_GROUP_PREFIXES) and lo <= rest_V[i].z <= hi for i in range(len(dom))]


def _rib_field(result):
    """Signed distance to a closed convex thorax hull built from the rib-guide points (positive outside)."""
    import bmesh
    pts = []
    for key, obj in result["objects"].items():
        if key.startswith("rib_"):
            pts.extend(attachment._world_points(obj))
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    tree = BVHTree.FromBMesh(bm)
    centre = sum(pts, Vector()) / len(pts)
    z_span = (min(p.z for p in pts), max(p.z for p in pts))

    def clearance(q):
        loc, normal, _, dist = tree.find_nearest(q)
        if (loc - centre).dot(normal) < 0:          # guard: hull normals must point away from the hull centre
            normal = -normal
        sign = 1.0 if (q - loc).dot(normal) >= 0 else -1.0
        return sign * dist, normal
    clearance.z_span = z_span
    clearance.hull_faces = len(bm.faces)
    return clearance


# ----------------------------------------------------------------------------------------------- solve
def solve_key(result, angle, rest, faces_in_region, movable, adj, rest_clear_ok, log, warm=None):
    """Solve the total rest-space delta for one key pose; `warm` (previous key's total delta) seeds the posed start."""
    body = result["body"]
    correction.apply_corrected_pose(result, angle)
    correction.reset_correctives(result)
    V, F = correction._evaluated(body)
    matrices = skin_matrices(result["runtime"], body)
    lbs_err = verify_lbs(result, matrices, V)
    V0 = rest[0]
    rest_mesh = [v.co.copy() for v in body.data.vertices]
    T = [v.copy() for v in V]
    for i, d in (warm or {}).items():
        T[i] = matrices[i] @ (rest_mesh[i] + d)
    lam, mu = contract.taubin_coefficients()
    clearance = _rib_field(result)
    region = set(faces_in_region)
    zone = {}
    edges_of = _vertex_faces(len(V0), F)
    vol_target = correction._volume(V0, F)          # rest body volume: the pressure term restores it
    history = []
    for it in range(MAX_ITERATIONS):
        pairs = _intersections(T, F, region)
        if it % 5 == 0 or pairs:
            zone = _problem_zone(V0, T, F, adj, movable, faces_in_region, pairs)
        if SMOOTHING == "springs":
            _spring_step(T, V0, F, adj, zone, edges_of, vol_target, lam_fair=FAIRING_LAMBDA)
        else:
            for coef in ((lam, mu) if SMOOTHING == "taubin" else (LAPLACIAN_LAMBDA,)):
                new = {}
                for v, w in zone.items():
                    if w <= 0.0:
                        continue
                    avg = sum((T[n] for n in adj[v]), Vector()) / len(adj[v])
                    new[v] = T[v] + (avg - T[v]) * (coef * w)
                for v, p in new.items():
                    T[v] = p
        acc = {}
        for a, b in (pairs if USE_PUSH else ()):
            na, nb = _normal(T, F[a]), _normal(T, F[b])
            ca = sum((T[i] for i in F[a]), Vector()) / 3.0
            cb = sum((T[i] for i in F[b]), Vector()) / 3.0
            da = nb if (ca - cb).dot(nb) >= 0 else -nb
            db = na if (cb - ca).dot(na) >= 0 else -na
            for face, d in ((F[a], da), (F[b], db)):
                for i in face:
                    if movable[i]:
                        s_, n_ = acc.get(i, (Vector(), 0))
                        acc[i] = (s_ + d, n_ + 1)
        for i, (s_, n_) in acc.items():               # averaged per vertex: no runaway sums over many pairs
            if s_.length > 1e-12:
                T[i] = T[i] + (s_ / n_).normalized() * PUSH_STEP_M
        push = {}
        for v in range(len(T)):
            if rest_clear_ok[v]:
                c, outward = clearance(T[v])
                if c < RIB_CLEARANCE_M:
                    push[v] = outward * (RIB_CLEARANCE_M - c)
        pushed = len(push)
        if push:
            # smooth the push as a displacement field over the torso (avoids ridges over discrete rib tubes)
            field = dict(push)
            frontier = set(push)
            for _ in range(PUSH_FIELD_RINGS):
                frontier = {n for v in frontier for n in adj[v] if rest_clear_ok[n]} - set(field)
                for v in frontier:
                    field[v] = Vector()
            for _ in range(PUSH_FIELD_PASSES):
                field = {v: (d + sum((field.get(n, Vector()) for n in adj[v] if n in field), Vector()))
                         / (1 + sum(1 for n in adj[v] if n in field)) for v, d in field.items()}
                for v, d in push.items():                 # keep at least the required push where it is needed
                    if field[v].dot(d) < d.length_squared:
                        field[v] = field[v] + d.normalized() * (d.length - field[v].dot(d.normalized()))
            for v, d in field.items():
                T[v] = T[v] + d
        history.append({"iteration": it, "pairs": len(pairs), "zone_vertices": len(zone), "rib_pushed": pushed})
        if it % 20 == 0:
            print("SOLVE", int(angle), it, len(pairs), len(zone), pushed, flush=True)
        collapsed = sum(1 for i in faces_in_region
                        if correction._area(V0, F[i]) > 1e-12 and correction._area(T, F[i]) / correction._area(V0, F[i]) < 0.1)
        history[-1]["collapsed"] = collapsed
        if not pairs and pushed == 0 and collapsed == 0 and it >= 10:
            break
    deltas = {}
    sigma_min, capped, residual = 1.0, 0, 0.0
    for v in range(len(T)):
        if movable[v] and (T[v] - V[v]).length > 1e-9:
            d, s_min, was_capped, res = damped_rest_delta(matrices[v], T[v], V[v], rest_mesh[v])
            deltas[v] = d
            sigma_min = min(sigma_min, s_min)
            capped += was_capped
            residual = max(residual, res)
    log[str(int(angle))] = {"iterations": len(history), "final": history[-1] if history else None,
                            "skin_matrix_min_singular_value": round(sigma_min, 5), "capped_deltas": capped,
                            "max_rest_delta_m": round(max((d.length for d in deltas.values()), default=0.0), 5),
                            "max_posed_residual_m": round(residual, 5),
                            "pairs_trace": [h["pairs"] for h in history[::10]],
                            "lbs_inverse_max_error_m": lbs_err, "moved_vertices": len(deltas)}
    return deltas


def damped_rest_delta(M, target, posed, rest):
    """Rest-space delta d (total, relative to the basis) with A(rest + d) + t ~ target, by damped least squares about
    the posed position without any key, then capped.  Returns (d, smallest singular value, capped?, posed residual)."""
    A = M.to_3x3()
    r = target - posed                                    # posed-space correction requested
    AtA = A.transposed() @ A
    reg = AtA + Matrix.Identity(3) * DAMPING
    d = reg.inverted() @ (A.transposed() @ r)
    capped = d.length > DELTA_CAP_M
    if capped:
        d = d * (DELTA_CAP_M / d.length)
    import numpy as np
    s = np.linalg.svd(np.array([list(row) for row in A]), compute_uv=False)
    residual = (A @ d - r).length
    return d, float(s.min()), int(capped), residual


def symmetrize(deltas, rest_V):
    tree = KDTree(len(rest_V))
    for i, p in enumerate(rest_V):
        tree.insert(p, i)
    tree.balance()
    mirror = {}
    worst = 0.0
    for i, p in enumerate(rest_V):
        _, j, d = tree.find(Vector((-p.x, p.y, p.z)))
        mirror[i] = j
        worst = max(worst, d)
    if worst > 1e-5:
        raise RuntimeError(f"rest mesh is not mirror-symmetric ({worst} m)")
    out = {}
    for i in set(deltas) | {mirror[i] for i in deltas}:
        a = deltas.get(i, Vector())
        m = deltas.get(mirror[i], Vector())
        out[i] = 0.5 * (a + Vector((-m.x, m.y, m.z)))
    return out, worst


def add_keys(result, solved):
    body = result["body"]
    keys = body.data.shape_keys.key_blocks
    basis = keys["Basis"]
    for label, deltas in solved.items():
        name = KEY_PREFIX + label
        kb = keys.get(name) or body.shape_key_add(name=name, from_mix=False)
        for i, p in enumerate(basis.data):
            kb.data[i].co = p.co
        for i, d in deltas.items():
            kb.data[i].co = basis.data[i].co + d          # body and armature transforms are identity (asserted)
        kb.value = 0.0
    bpy.context.view_layer.update()


def apply_pose_with_correctives(result, ht_elevation_deg, use_correctives=True):
    weights = contract.key_weights(ht_elevation_deg)            # validates before mutation
    profile = correction.apply_corrected_pose(result, ht_elevation_deg)
    keys = result["body"].data.shape_keys.key_blocks
    for kb in keys[1:]:
        if not kb.name.startswith(KEY_PREFIX):
            kb.value = 0.0                                # legacy correctives never leak into this pose
    for label, w in weights.items():
        kb = keys.get(KEY_PREFIX + label)
        if kb is not None:
            kb.value = w if use_correctives else 0.0
    bpy.context.view_layer.update()
    return dict(profile, corrective_weights=weights if use_correctives else {k: 0.0 for k in weights})


def build_corrective_scene():
    result = correction.build_corrected_scene()
    body = result["body"]
    correction.reset_correctives(result)
    correction.apply_corrected_pose(result, 0)
    rest = correction._evaluated(body)
    faces_in_region, inreg = correction.region_faces(body)
    adj = _adjacency(len(rest[0]), rest[1])
    movable = inreg
    if not (body.matrix_world.is_identity and result["runtime"].matrix_world.is_identity):
        raise RuntimeError("body and runtime armature must have identity transforms")
    clearance = _rib_field(result)
    torso = _torso_vertices(body, movable, rest[0], clearance.z_span)
    rest_clear_ok = [torso[i] and clearance(p)[0] >= RIB_CLEARANCE_M for i, p in enumerate(rest[0])]
    log = {}
    solved = {}
    warm = None
    for angle in contract.KEY_POSES_DEG:
        raw = solve_key(result, angle, rest, faces_in_region, movable, adj, rest_clear_ok, log, warm)
        label = contract.key_label(angle)
        solved[label], sym_err = symmetrize(raw, rest[0])
        log[str(int(angle))]["mirror_map_max_error_m"] = sym_err
        warm = solved[label]
    add_keys(result, solved)
    correction.apply_corrected_pose(result, 0)
    bpy.context.scene["functional_coupled_corrective_approved"] = False
    result.update({"rest": rest, "faces_in_region": faces_in_region, "rest_clear_ok": rest_clear_ok,
                   "solve_log": log, "rib_clearance": clearance, "torso": torso})
    return result


def _rib_clearance_min_mm(result, V):
    ok = result["rest_clear_ok"]
    clear = result["rib_clearance"]
    vals = [clear(V[i])[0] for i in range(len(V)) if ok[i]]
    return round(min(vals) * 1000, 2) if vals else None


def measure(result, angles=(0, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160)):
    body = result["body"]
    rest = result["rest"]
    faces = result["faces_in_region"]
    rows = []
    for angle in angles:
        row = {"ht_elevation_deg": angle}
        posed_by = {}
        for label, use in (("without_correctives", False), ("with_correctives", True)):
            profile = apply_pose_with_correctives(result, angle, use)
            posed = correction._evaluated(body)
            posed_by[label] = posed[0]
            m = correction.deformation_metrics(body, rest, posed, faces)
            m.pop("self_intersection_face_sample", None)
            rib = _rib_clearance_min_mm(result, posed[0])
            m["torso_thorax_hull_clearance_min_mm"] = rib
            m["unmet_targets"] = contract.meets_targets(m, rib)
            m["corrective_weights"] = profile["corrective_weights"]
            row[label] = m
        row["max_posed_correction_mm"] = round(max((a - b).length for a, b in zip(posed_by["with_correctives"],
                                                                                   posed_by["without_correctives"])) * 1000, 3)
        rows.append(row)
    apply_pose_with_correctives(result, 0)
    return rows


def render_evidence(output_directory):
    output = Path(output_directory).resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    result = build_corrective_scene()
    metrics = measure(result)
    scene = bpy.context.scene
    body = result["body"]
    guides = list(result["objects"].values())
    for obj in scene.objects:
        if obj.type == "MESH" and obj is not body and obj not in guides:
            obj.hide_render = True
    body.data.materials.clear()
    body.data.materials.append(attachment._material("HGPT_COUPLED_CORRECTIVE_SKIN_TMP", (0.64, 0.44, 0.36)))
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light, shading.color_type = "STUDIO", "MATERIAL"
    shading.show_cavity = shading.show_shadows = shading.show_xray = True
    shading.xray_alpha = 0.28
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.image_settings.file_format = "PNG"
    cam_data = bpy.data.cameras.new("HGPT_COUPLED_CORRECTIVE_CAMERA_TMP")
    cam_data.type = "ORTHO"
    cam = bpy.data.objects.new("HGPT_COUPLED_CORRECTIVE_CAMERA_TMP", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    written = []
    for angle in (120, 145, 160):                 # 0/90 unchanged (keys inactive); 145 is the worst between-key blend
        apply_pose_with_correctives(result, angle)
        pts = [p for g in guides for p in attachment._world_points(g)]
        lo = tuple(min(p[i] for p in pts) for i in range(3))
        hi = tuple(max(p[i] for p in pts) for i in range(3))
        target, scale = attachment.bridge.frame_from_bounds(lo, hi, padding=1.22)
        cam_data.ortho_scale = scale
        for view, offset in correction.SHOULDER_VIEWS.items():
            cam.location = Vector(target) + Vector(offset)
            cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
            path = output / f"ht{angle:03d}__corrective_shoulder_{view}.png"
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            written.append(path)
    apply_pose_with_correctives(result, 0)
    source = Path(bpy.data.filepath).resolve()
    manifest = {
        "candidate": "PROVISIONAL_FUNCTIONAL_COUPLED_SHOULDER_CORRECTIVE_v1",
        "source_blend": source.name, "source_blend_sha256": attachment._sha256(source),
        "key_poses_deg": list(contract.KEY_POSES_DEG), "activation": "piecewise-linear hat per key over 90..160",
        "targets": contract.TARGETS, "solve": result["solve_log"], "metrics": metrics,
        "rendered": [p.name for p in written],
        "anatomy_approved": False, "deformation_approved": False, "glb_approved": False,
        "clinical_approved": False, "production_approved": False,
        "known_limits": [
            "engineering relaxation (smoothing, face separation, rib push-out), not muscle or tissue simulation",
            "keys solved only at 100..160 (10 deg) in the authored 40-degree plane; other planes and poses are untested",
            "in-memory shape keys; the source blend, weights and legacy keys are unchanged",
            "rib guides are static on spine_02; thorax hull is the convex hull of the guides; no breathing or contact solver",
            "rest deltas are damped and capped at 30 mm; the requested posed correction is clipped where skinning is ill-conditioned",
        ],
        "files_sha256": {p.name: attachment._sha256(p) for p in written},
    }
    (output / "functional_coupled_corrective_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    print("FUNCTIONAL_COUPLED_CORRECTIVE_EVIDENCE", json.dumps({"output": str(output), "images": len(written)}))
    return manifest


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if arguments:
        render_evidence(attachment.output_argument(arguments))
    else:
        res = build_corrective_scene()
        print("FUNCTIONAL_COUPLED_CORRECTIVE", json.dumps(measure(res), default=str)[:4000])
