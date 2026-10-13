"""Reference-constrained W1/W2 shoulder/thorax guide correction on the original male runtime rig.

Builds on PR110 (build_functional_original_coupled_motion_blender): the coupled 0/90/160 runtime motion, clavicle
semantics, absolute humeral direction and F-SIDE-001 are reused unchanged.  This module only
  * replaces the 24 rib guides with Holcombe-shaped guides on the frozen a003 endpoints,
  * replaces the two scapula bowls with RIGID (Lee-sized) outlines anchored at the a003 glenoid and rotated about it
    so the medial border sits on the rib guides at an authored clearance,
  * adds an authored humeral external-rotation channel measured in an anatomical-style humeral frame,
  * measures original-mesh shoulder/axilla deformation (volume, collapse, stretch, self-intersection) at 0/90/160.
Diagnostic evidence only; no anatomy, motion, deformation, GLB, clinical or production approval.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_functional_original_attachment_blender as attachment
import build_functional_original_coupled_motion_blender as coupled
import functional_shoulder_correction as corr
from functional_shoulder_shapes import scapula_bowl_mesh

RIB_RADIUS_M = 0.004
SCAPULA_TARGET_CLEARANCE_M = 0.012      # authored costal clearance (subscapularis/serratus space), not a measurement
SCAPULA_MEDIAL_LANDMARKS_1BASED = (3, 4, 5, 6, 7)
SCAPULA_PERIMETER_1BASED = (3, 4, 5, 6, 7, 8, 9, 12, 13, 15, 18, 1, 2)   # PR109 outline order, unchanged
REGION_GROUPS = ("upperarm_r", "upperarm_l", "clavicle_r", "clavicle_l", "scapula_r", "scapula_l")
REGION_WEIGHT = 0.05
SHOULDER_VIEWS = {"front": (0.0, -3.0, 0.0), "side": (3.0, 0.0, 0.0), "rear": (0.0, 3.0, 0.0)}
# anatomical side -> runtime upper-arm bone (F-SIDE-001 preserved: native _r drives anatomical left)
HUMERI = (("left", "upperarm_r"), ("right", "upperarm_l"))


def _remove(obj):
    bpy.data.objects.remove(obj, do_unlink=True)


def _thorax_axis_y(anatomy):
    ys = [b.head_local.y for b in anatomy.data.bones if b.name.startswith("anat_rib_")]
    ys += [b.tail_local.y for b in anatomy.data.bones if b.name.startswith("anat_rib_")
           and int(b.name.split("_")[2]) <= 10]
    return sum(ys) / len(ys)


def _rib_sampler(rib_points, axis_y):
    tree = KDTree(len(rib_points))
    for i, p in enumerate(rib_points):
        tree.insert(p, i)
    tree.balance()

    def signed_clearance(q):
        q = Vector(q)
        r, _, dist = tree.find(q)
        centre = Vector((0.0, axis_y, r.z))
        outward = (r - centre)
        outward.z = 0.0
        sign = 1.0 if (q - r).dot(outward) >= 0 else -1.0
        return sign * dist - RIB_RADIUS_M
    return signed_clearance


def build_corrected_scene():
    result = coupled.build_coupled_scene()
    anatomy, runtime = result["anatomy"], result["runtime"]
    collection = bpy.data.collections[attachment.COLLECTION_NAME]
    objects = result["objects"]
    model = corr.load_holcombe()
    thorax = attachment._material("HGPT_ATTACHMENT_THORAX_TMP", (0.65, 0.78, 0.52))
    scap_mat = attachment._material("HGPT_ATTACHMENT_SCAPULA_TMP", (0.15, 0.65, 0.85))
    rib_world = []
    rib_report = {}
    for number in range(1, 13):
        params = corr.rib_level_parameters(model, number)
        for side in ("left", "right"):
            key = f"rib_{number:02d}_{side}"
            _remove(objects[key])
            name = f"anat_rib_{number:02d}_{side}"
            bone = anatomy.data.bones[name]
            pts = corr.rib_points_reference(tuple(bone.head_local), tuple(bone.tail_local), side, params)
            rib = attachment._tube(f"HGPT_reference_rib_{number:02d}_{side}_TMP", pts, RIB_RADIUS_M, thorax, collection)
            attachment._attach(rib, runtime, name, "Holcombe distal spiral + authored proximal bridge")
            rib["rib_scope"] = corr.RIB_SCOPE
            objects[key] = rib
            rib_world.extend(Vector(p) for p in pts)
            if side == "left":
                rib_report[number] = {"chord_mm": round((bone.tail_local - bone.head_local).length * 1000, 1),
                                      "holcombe_Sx_mean_mm": params["Sx_mm"], "Ypk": params["Ypk"],
                                      "phi_pia_deg": params["phi_pia_deg"]}
    axis_y = _thorax_axis_y(anatomy)
    clearance = _rib_sampler(rib_world, axis_y)
    record = json.loads(attachment.RECORD.read_text(encoding="utf-8"))
    scap_report = {}
    for side in ("left", "right"):
        key = f"scapula_{side}"
        _remove(objects[key])
        landmarks = [tuple(v / 1000.0 for v in p) for p in record["candidate"]["scapula_landmarks_world_mm"][side]]
        rb = record["bones"][f"scapula_{side}"]
        bone = anatomy.data.bones[f"anat_scapula_{side}"]
        rigid = corr.fit_segment_rigid(landmarks, rb["head_m"], rb["tail_m"], tuple(bone.head_local), tuple(bone.tail_local))
        medial = [i - 1 for i in SCAPULA_MEDIAL_LANDMARKS_1BASED]
        before = [round(clearance(rigid[i]) * 1000, 1) for i in medial]
        yaw, tilt, rms, placed = corr.place_on_thorax(rigid, tuple(bone.head_local), clearance, medial,
                                                     SCAPULA_TARGET_CLEARANCE_M)
        perimeter = [placed[i - 1] for i in SCAPULA_PERIMETER_1BASED]
        vertices, faces = scapula_bowl_mesh(perimeter, 0.008)
        scap = attachment._mesh(f"HGPT_reference_scapula_bowl_{side}_TMP", vertices, faces, scap_mat, collection)
        attachment._attach(scap, runtime, f"anat_scapula_{side}", "rigid Lee-sized outline placed on rib guides")
        scap["fit_source"] = "c004 Lee-consistent landmarks, rigid (scale 1) at the a003 glenoid, rotated about it"
        objects[key] = scap
        scap_report[side] = {"landmarks": placed, "rotation_about_glenoid_deg": {"yaw_z": yaw, "tilt_x": tilt},
                             "medial_clearance_mm_before": before,
                             "medial_clearance_mm_after": [round(clearance(placed[i]) * 1000, 1) for i in medial],
                             "placement_rms_error_mm": round(rms * 1000, 2)}
    bpy.context.scene["functional_shoulder_correction_approved"] = False
    result["rib_report"] = rib_report
    result["scapula_report"] = scap_report
    result["thorax_axis_y"] = axis_y
    for side, runtime_name in HUMERI:
        b = runtime.data.bones[runtime_name]
        result.setdefault("humeral_rest_axial_deg", {})[runtime_name] = corr.humeral_axial_angle_deg(
            tuple(b.tail_local - b.head_local), tuple(b.matrix_local.col[0].xyz), 40.0, side)
    apply_corrected_pose(result, 0)
    return result


def apply_corrected_pose(result, ht_elevation_deg, axial=True):
    external = corr.humeral_external_rotation_deg(ht_elevation_deg)   # validates before any mutation
    if not axial:
        external = 0.0
    profile = coupled.apply_coupled_pose(result, ht_elevation_deg)
    runtime = result["runtime"]
    realized, pr110_axial, applied = {}, {}, {}
    for side, name in HUMERI:
        bone = runtime.pose.bones[name]
        d = (bone.tail - bone.head).normalized()
        current = corr.humeral_axial_angle_deg(tuple(d), tuple(bone.x_axis), profile["plane_deg"], side)
        target = result["humeral_rest_axial_deg"][name] + corr.external_rotation_sign(side) * external
        delta_deg = ((target - current + 180.0) % 360.0) - 180.0
        delta = math.radians(delta_deg)
        pr110_axial[side] = current - result["humeral_rest_axial_deg"][name]
        applied[side] = delta_deg
        pivot = bone.head.copy()
        rot = Matrix.Rotation(delta, 4, d)
        bone.matrix = Matrix.Translation(pivot) @ rot @ Matrix.Translation(-pivot) @ bone.matrix
        bpy.context.view_layer.update()
        d2 = (bone.tail - bone.head).normalized()
        realized[side] = corr.humeral_axial_angle_deg(tuple(d2), tuple(bone.x_axis), profile["plane_deg"], side) - \
            result["humeral_rest_axial_deg"][name]
    profile = dict(profile, humeral_external_rotation_deg=external, humeral_axial_scope="project-authored hypothesis",
                   humeral_axial_realized_rel_rest_deg=realized,
                   humeral_axial_pr110_implicit_rel_rest_deg=pr110_axial, humeral_axial_applied_delta_deg=applied, humeral_axial_cohort_fit=False)
    return profile


def _evaluated(body):
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    verts = [ev.matrix_world @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return verts, polys


def _assert_triangles(F):
    if any(len(f) != 3 for f in F):
        raise RuntimeError("deformation metrics require a triangulated body mesh")


def _area(V, f):
    a, b, c = V[f[0]], V[f[1]], V[f[2]]
    return (b - a).cross(c - a).length / 2.0


def _volume(V, F):
    return sum(V[f[0]].dot(V[f[1]].cross(V[f[2]])) for f in F) / 6.0


def region_faces(body):
    idx = {g.index for g in body.vertex_groups if g.name in REGION_GROUPS}
    inreg = [any(e.group in idx and e.weight > REGION_WEIGHT for e in v.groups) for v in body.data.vertices]
    return [i for i, p in enumerate(body.data.polygons) if any(inreg[v] for v in p.vertices)], inreg


def _dominant_groups(body):
    names = {g.index: g.name for g in body.vertex_groups}
    dom = []
    for v in body.data.vertices:
        best = max(v.groups, key=lambda e: e.weight, default=None)
        dom.append(names[best.group] if best is not None else "none")
    return dom


def _zones(face_ids, F, dom):
    out = {}
    for i in face_ids:
        names = [dom[v] for v in F[i]]
        key = max(set(names), key=names.count)
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def deformation_metrics(body, rest, posed, faces_in_region, dom=None):
    V0, F = rest
    V1, _ = posed
    _assert_triangles(F)
    ratios = [_area(V1, F[i]) / _area(V0, F[i]) for i in faces_in_region if _area(V0, F[i]) > 1e-12]
    vol0, vol1 = _volume(V0, F), _volume(V1, F)
    tree = BVHTree.FromPolygons(V1, F, all_triangles=True)
    pairs = tree.overlap(tree)
    reg = set(faces_in_region)
    fsets = [set(f) for f in F]
    hits = [(a, b) for a, b in pairs if a < b and (a in reg or b in reg) and not (fsets[a] & fsets[b])]
    involved = sorted({i for p in hits for i in p})
    collapsed = [i for i in faces_in_region if _area(V0, F[i]) > 1e-12 and _area(V1, F[i]) / _area(V0, F[i]) < 0.1]
    dom = dom or _dominant_groups(body)
    return {
        "collapse_zones_by_dominant_group": _zones(collapsed, F, dom),
        "self_intersection_zones_by_dominant_group": _zones(involved, F, dom),
        "region_faces": len(faces_in_region),
        "area_ratio_min": round(min(ratios), 4), "area_ratio_max": round(max(ratios), 4),
        "collapse_faces_ratio_lt_0_1": sum(r < 0.1 for r in ratios),
        "compressed_faces_ratio_lt_0_5": sum(r < 0.5 for r in ratios),
        "stretched_faces_ratio_gt_2": sum(r > 2.0 for r in ratios),
        "body_volume_l": round(vol1 * 1000, 4), "body_volume_change_pct": round((vol1 - vol0) / vol0 * 100, 4),
        "self_intersecting_face_pairs_in_region": len(hits), "self_intersecting_faces_in_region": len(involved),
        "self_intersection_face_sample": involved[:20],
    }


def guide_skin_report(result, body_verts, body_faces):
    tree = BVHTree.FromPolygons(body_verts, body_faces, all_triangles=True)

    def inside(p):
        hits, o = 0, Vector(p)
        for _ in range(64):
            loc, *_ = tree.ray_cast(o, Vector((0.0, 0.0, 1.0)))
            if loc is None:
                break
            hits += 1
            o = loc + Vector((0.0, 0.0, 1e-6))
        return hits % 2 == 1
    out = {}
    for key, obj in result["objects"].items():
        if key.startswith(("rib_", "scapula_")):
            pts = attachment._world_points(obj)
            out[key] = sum(not inside(p) for p in pts)
    return out


def measure(result, angles=(0, 90, 160)):
    body = result["body"]
    faces, _ = region_faces(body)
    reset_correctives(result)
    if any(abs(kb.value) > 0 for kb in body.data.shape_keys.key_blocks[1:]):
        raise RuntimeError("corrective keys must start at zero")
    apply_corrected_pose(result, 0)
    rest = _evaluated(body)
    rows = []
    for angle in angles:
        profile = apply_corrected_pose(result, angle)
        posed = _evaluated(body)
        row = {"ht_elevation_deg": angle, "humeral_external_rotation_deg": profile["humeral_external_rotation_deg"],
               "humeral_axial_realized_rel_rest_deg": profile["humeral_axial_realized_rel_rest_deg"],
               "humeral_axial_pr110_implicit_rel_rest_deg": profile["humeral_axial_pr110_implicit_rel_rest_deg"],
               "humeral_axial_applied_delta_deg": profile["humeral_axial_applied_delta_deg"],
               "deformation": deformation_metrics(body, rest, posed, faces),
               "deformation_pr110_unchanged_pose": (deformation_metrics(body, rest, _posed_pr110(result, angle), faces)
                                                    if angle else None),
               "guide_vertices_outside_skin": guide_skin_report(result, *posed)}
        if angle:
            with_keys, applied = _posed_with_correctives(result, angle)
            row["existing_corrective_values_diagnostic"] = {k: round(v, 4) for k, v in applied.items()}
            row["deformation_with_existing_correctives_diagnostic"] = deformation_metrics(body, rest, with_keys, faces)
        rows.append(row)
    apply_corrected_pose(result, 0)
    return rows


def _smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def activate_existing_correctives(result):
    """Diagnostic only: set the body's undriven CORR (abduction, r93) and SCAP (r95) shape keys by their recorded
    activation formulas for the current pose.  FLEX is left at 0: its flexion-fraction definition is not used here.
    Returns the applied values; the caller must reset them (nothing is saved)."""
    runtime, body = result["runtime"], result["body"]
    keys = body.data.shape_keys.key_blocks
    spine = runtime.pose.bones["spine_03"]
    down = -(spine.tail - spine.head).normalized()
    rest_spine = runtime.data.bones["spine_03"].matrix_local.to_3x3()
    applied = {}
    for suffix in ("l", "r"):
        arm = runtime.pose.bones[f"upperarm_{suffix}"]
        theta = math.degrees((arm.tail - arm.head).normalized().angle(down))
        applied[f"HGPT_SHOULDER_CORR_{suffix.upper()}"] = _smooth01((theta - 40.0) / 110.0)
        scap = runtime.pose.bones[f"scapula_{suffix}"]
        r_sp = spine.matrix.to_3x3() @ rest_spine.inverted()
        r_sc = scap.matrix.to_3x3() @ runtime.data.bones[f"scapula_{suffix}"].matrix_local.to_3x3().inverted()
        u = math.degrees((r_sp.transposed() @ r_sc).to_quaternion().angle)
        applied[f"HGPT_SHOULDER_SCAP_{suffix.upper()}"] = _smooth01((u - 25.0) / 50.0)
    for name, value in applied.items():
        keys[name].value = value
    bpy.context.view_layer.update()
    return applied


def reset_correctives(result):
    for kb in result["body"].data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    bpy.context.view_layer.update()


def _posed_with_correctives(result, angle):
    apply_corrected_pose(result, angle)
    applied = activate_existing_correctives(result)
    out = _evaluated(result["body"])
    reset_correctives(result)
    return out, applied


def _posed_pr110(result, angle):
    """The reviewed PR110 pose (shortest-arc humeral swing, no axial channel) for attribution."""
    coupled.apply_coupled_pose(result, angle)
    out = _evaluated(result["body"])
    apply_corrected_pose(result, angle)
    return out


def render_evidence(output_directory):
    output = Path(output_directory).resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    result = build_corrected_scene()
    metrics = measure(result)
    scene = bpy.context.scene
    body = result["body"]
    guides = list(result["objects"].values())
    for obj in scene.objects:
        if obj.type == "MESH" and obj is not body and obj not in guides:
            obj.hide_render = True
    body.data.materials.clear()
    body.data.materials.append(attachment._material("HGPT_CORRECTION_SKIN_TMP", (0.64, 0.44, 0.36)))
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light, shading.color_type = "STUDIO", "MATERIAL"
    shading.show_cavity = shading.show_shadows = shading.show_xray = True
    shading.xray_alpha = 0.28
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.image_settings.file_format = "PNG"
    cam_data = bpy.data.cameras.new("HGPT_CORRECTION_CAMERA_TMP")
    cam_data.type = "ORTHO"
    cam = bpy.data.objects.new("HGPT_CORRECTION_CAMERA_TMP", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    written = []
    for angle in (0, 90, 160):
        apply_corrected_pose(result, angle)
        pts = [p for g in guides for p in attachment._world_points(g)]
        lo = tuple(min(p[i] for p in pts) for i in range(3))
        hi = tuple(max(p[i] for p in pts) for i in range(3))
        target, scale = attachment.bridge.frame_from_bounds(lo, hi, padding=1.22)
        cam_data.ortho_scale = scale
        for view, offset in SHOULDER_VIEWS.items():
            cam.location = Vector(target) + Vector(offset)
            cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
            path = output / f"ht{angle:03d}__shoulder_{view}.png"
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            written.append(path)
    apply_corrected_pose(result, 0)
    source = Path(bpy.data.filepath).resolve()
    scap = {s: {k: v for k, v in r.items() if k != "landmarks"} for s, r in result["scapula_report"].items()}
    lee = corr.lee_reference_distances()
    for side, r in result["scapula_report"].items():
        L = r["landmarks"]
        scap[side]["lee_distances_mm"] = {k: {"guide": round(math.dist(L[v["pair_1based"][0] - 1], L[v["pair_1based"][1] - 1]) * 1000, 1),
                                              "lee_182_pred": round(v["pred_mm"], 1), "resid_sd": round(v["resid_sd_mm"], 1)}
                                          for k, v in lee.items()}
    manifest = {
        "candidate": "PROVISIONAL_FUNCTIONAL_SHOULDER_CORRECTION_v1",
        "source_blend": source.name, "source_blend_sha256": attachment._sha256(source),
        "source_record_sha256": attachment._sha256(attachment.RECORD),
        "holcombe_model_sha256": attachment._sha256(corr.HOLCOMBE_PATH),
        "lee_model_sha256": attachment._sha256(corr.LEE_PATH),
        "rib_scope": corr.RIB_SCOPE, "ribs": result["rib_report"], "scapulae": scap,
        "scapula_target_clearance_mm": SCAPULA_TARGET_CLEARANCE_M * 1000,
        "humeral_external_rotation_top_deg": corr.HUMERAL_AXIAL_TOP_DEG,
        "humeral_rest_axial_deg": result["humeral_rest_axial_deg"],
        "metrics": metrics, "region_groups": REGION_GROUPS, "region_weight_threshold": REGION_WEIGHT,
        "rendered": [p.name for p in written],
        "anatomy_approved": False, "human_motion_accepted": False, "deformation_approved": False,
        "glb_approved": False, "clinical_approved": False, "production_approved": False,
        "known_limits": [
            "rib proximal segment is an authored bridge; Holcombe proximal branch selection remains blocked",
            "rib plane orientation authored (chord + outward lateral); Holcombe PH/LS/BH convention not mapped",
            "scapula clearance is an authored 12 mm target to the rib-guide tube surface (centreline minus 4 mm radius); no contact solver",
            "posed guide-outside-skin counts use +Z ray parity, approximate on self-intersecting posed skin",
            "PR110 shortest-arc swing already carries implicit axial rotation; see humeral_axial_pr110_implicit_rel_rest_deg",
            "humeral external rotation magnitude is a project-authored hypothesis, not a cohort fit",
            "deformation figures are diagnostics on the unchanged 17,946-vertex original, not acceptance",
        ],
        "files_sha256": {p.name: attachment._sha256(p) for p in written},
    }
    (output / "functional_shoulder_correction_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("FUNCTIONAL_SHOULDER_CORRECTION_EVIDENCE", json.dumps({"output": str(output), "images": len(written)}))
    return manifest


if __name__ == "__main__":
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if arguments:
        render_evidence(attachment.output_argument(arguments))
    else:
        res = build_corrected_scene()
        print("FUNCTIONAL_SHOULDER_CORRECTION", json.dumps(measure(res), default=str)[:4000])
