#!/usr/bin/env python3
"""Blender scene setup for the independent pelvic CT window review (NON-DESTRUCTIVE).

Run inside Blender, arguments after `--`:

  blender -b [accepted_skeleton.blend] --python scripts/anatomy_fit/ct_pelvis_review_scene_blender.py -- \
      --ct-dir  <PRIVATE dir with cvm1749f.png/.txt ... cvm1803f.png/.txt> \
      --cache-dir <PRIVATE dir for windowed 8-bit display copies> \
      --report-out <new report .json> [--save-as <new private .blend>] [--fresh] [--skip-ct]

What it does
  * validates the six PNG + six scanner headers against the SHA-256 pins (fail closed);
  * shows each frame as a textured plane whose four corners are the header's scanner-RAS
    corners (so orientation comes from the header, not from guesswork), mapped to the
    project axes by a FIXED display rotation and placed in a separate display bay;
  * adds clearly labelled review markers/sticks at the a003/c004 skeleton pelvis, S1,
    L4/L5, acetabular/hip-centre records and the provisional P1 S1 frame;
  * if an accepted-skeleton armature (HGPT_ANATOMICAL_MASTER) is open, reports each
    pelvic bone/marker position difference against the record (read-only).

What it never does
  * never moves, edits, deletes or re-parents any pre-existing object (snapshot compared
    before/after; any change aborts with an error);
  * never packs an image (CT pixels stay external in the private directories);
  * never saves over the opened file, never writes inside the repository worktree;
  * never registers scanner space to the skeleton: the display offset is arbitrary and
    every CT object carries display_only_not_registered=True, region_status=UNVERIFIED.

`bpy` is imported only inside main(); everything else is pure Python and unit tested.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ct_pelvis_window_geometry as geo  # noqa: E402
import ct_pelvis_skeleton_vs_source_report as skel  # noqa: E402

REPO_ROOT = geo.REPO_ROOT
DEFAULT_MANIFEST = (REPO_ROOT / "ORIGINAL_V1_WORK/anatomy/audit/claude_pelvis_ct_review_20261009/"
                    "pinned_six_frames_from_pr15_4680b49.json")
CT_COLLECTION = "CT_REVIEW_PRIVATE__DISPLAY_ONLY_NOT_REGISTERED"
SKEL_COLLECTION_PREFIX = "SKELETON_INSPECTION__"
P1_COLLECTION = "SKELETON_INSPECTION__P1_PROVISIONAL"
MASTER_ARMATURE = "HGPT_ANATOMICAL_MASTER"
# Arbitrary display bay beside the skeleton. It deliberately aligns with no hip/pelvis level
# (a guard test enforces >0.4 m clearance from the hip axis) so it cannot read as registration.
DEFAULT_DISPLAY_OFFSET_M = (1.2, 0.0, 2.0)


class SceneSafetyError(RuntimeError):
    """A post-condition (no change to existing objects, no packing, ...) failed."""


# --------------------------------------------------------------------------
# Pure plan building
# --------------------------------------------------------------------------
def build_ct_plan(manifest, geoms, display_records, offset_m):
    """Plane + corner-marker specs for the six frames.  No file or bpy access."""
    planes, markers = [], []
    pins = manifest["by_id"]
    disp = {d["source_id"]: d for d in display_records}
    for sid in geo.ALL_IDS:
        g = geoms[sid]
        tl, tr, br, bl = geo.plane_corners_display_m(g, offset_m)
        s = g["scanner_S_mm"]
        name = f"CT_REVIEW_PRIVATE__{geo.frame_name(sid, 'png')[:-4]}__S{int(s)}"
        props = {
            "source_id": sid,
            "png_filename": geo.frame_name(sid, "png"),
            "png_sha256": pins[sid]["png_sha256"],
            "header_sha256": pins[sid]["scanner_header_sha256"],
            "scanner_S_mm": float(s),
            "slab_S_min_mm": float(s) - 1.5,
            "slab_S_max_mm": float(s) + 1.5,
            "pixel_spacing_mm": g["pixel_spacing_mm"][0],
            "slice_thickness_mm": g["slice_thickness_mm"],
            "increasing_column_toward": g["increasing_column_points_toward_scanner_axis"],
            "increasing_row_toward": g["increasing_row_points_toward_scanner_axis"],
            "window_stored_low": disp[sid]["window_stored_low"],
            "window_stored_high": disp[sid]["window_stored_high"],
            "region_status": "UNVERIFIED",
            "display_only_not_registered": True,
            "stored_values_are_calibrated_HU": False,
            "image_laterality_verified": False,
        }
        planes.append({
            "name": name,
            "corners_m": {"TL": tl, "TR": tr, "BR": br, "BL": bl},
            "uv": {"TL": (0.0, 1.0), "TR": (1.0, 1.0), "BR": (1.0, 0.0), "BL": (0.0, 0.0)},
            "image_path": str(Path(disp[sid]["_cache_dir"]) / disp[sid]["display_filename"]),
            "props": props,
        })
        for tag, point, rc in (("TL", tl, (0, 0)), ("TR", tr, (0, geo.GRID)), ("BR", br, (geo.GRID, geo.GRID))):
            markers.append({"name": f"{name}__corner_{tag}", "location_m": point,
                            "props": {"corner": tag,
                                      "image_row_col_if_outer_edge_convention": list(rc),
                                      "display_only_not_registered": True}})
    return {"planes": planes, "corner_markers": markers}


def _stick(name, head_m, tail_m, props):
    return {"name": name, "head_m": head_m, "tail_m": tail_m, "props": props}


def build_skeleton_plan(record, label, p1_doc=None):
    """Review points/sticks from a003 or c004 plus the provisional P1 S1 frame."""
    s = skel.extract_pelvic_set(record)
    d = skel.derive(record)
    to_m = lambda p: [v / 1000.0 for v in p]
    base = {"source_record": label, "status": "SOURCE_SKELETON_RECORD_NOT_CT_VERIFIED",
            "geometry_governs": True}
    points, sticks = [], []
    for k, m in s["markers"].items():
        points.append({"name": f"SKELINSP_{label}__{k}", "location_m": to_m(m["centre_mm"]),
                       "props": {**base, "kind": "joint_marker", "key": k,
                                 "frame_bone": m["frame_bone"]}})
    points.append({"name": f"SKELINSP_{label}__HJC_midpoint",
                   "location_m": to_m(d["HJC_midpoint_mm"]),
                   "props": {**base, "kind": "derived", "key": "HJC_midpoint"}})
    for k, b in s["bones"].items():
        sticks.append(_stick(f"SKELINSP_{label}__bone_{k}", to_m(b["head_mm"]), to_m(b["tail_mm"]),
                             {**base, "kind": "bone", "key": k, "confidence": b["confidence"]}))
    sticks.append(_stick(f"SKELINSP_{label}__HA_to_S1_sacrum_tail",
                         to_m(d["HJC_midpoint_mm"]), to_m(s["bones"]["sacrum"]["tail_mm"]),
                         {**base, "kind": "derived", "key": "HA_to_S1",
                          "distance_mm": d["HA_to_S1_via_sacrum_tail"]["distance_mm"]}))
    p1 = []
    if p1_doc is not None:
        e = p1_doc["derived_S1_superior_endplate"]
        c = e["centre_m"]
        axes = e["local_axes_world"]
        pbase = {"source_record": "canonical_s1_pelvic_frame_p1.json",
                 "status": "PROVISIONAL_P1_NOT_ACCEPTED_NOT_CT_VERIFIED", "geometry_governs": False}
        p1.append({"name": "SKELINSP_P1__S1_endplate_centre", "location_m": c,
                   "props": {**pbase, "kind": "P1_S1_centre"}})
        ha = p1_doc["retained_hip_axis"]["HA_midpoint_m"]
        sticks.append(_stick("SKELINSP_P1__HA_to_S1_centre", ha, c,
                             {**pbase, "kind": "P1_HA_to_S1",
                              "distance_mm": e["distance_HA_to_S1_mm"]}))
        for axis_name, key in (("X_left", "X_left"), ("Y_AP", "Y_anterior_to_posterior_along_endplate"),
                               ("Z_normal", "Z_superior_endplate_normal")):
            v = axes[key]
            sticks.append(_stick(f"SKELINSP_P1__axis_{axis_name}", c,
                                 [c[i] + 0.02 * v[i] for i in range(3)],
                                 {**pbase, "kind": "P1_axis", "axis": axis_name}))
    return {"points": points, "sticks": sticks, "p1_points": p1}


def compare_existing_skeleton(record, bone_world, marker_world):
    """Differences (mm) between the record and an opened accepted skeleton.

    `bone_world[id] = (head_m, tail_m)` and `marker_world[id] = centre_m` are read
    from the open scene by the caller.  Read-only; returns a report dict.
    """
    s = skel.extract_pelvic_set(record)
    rows, worst = [], 0.0
    for k, b in s["bones"].items():
        if k not in bone_world:
            rows.append({"kind": "bone", "key": k, "found_in_scene": False})
            continue
        h, t = bone_world[k]
        dh = math.dist(h, [v / 1000 for v in b["head_mm"]]) * 1000
        dt = math.dist(t, [v / 1000 for v in b["tail_mm"]]) * 1000
        worst = max(worst, dh, dt)
        rows.append({"kind": "bone", "key": k, "found_in_scene": True,
                     "head_delta_mm": dh, "tail_delta_mm": dt})
    for k, m in s["markers"].items():
        if k not in marker_world:
            rows.append({"kind": "marker", "key": k, "found_in_scene": False})
            continue
        dm = math.dist(marker_world[k], [v / 1000 for v in m["centre_mm"]]) * 1000
        worst = max(worst, dm)
        rows.append({"kind": "marker", "key": k, "found_in_scene": True, "centre_delta_mm": dm})
    found = sum(1 for r in rows if r["found_in_scene"])
    return {"items_found": found, "items_missing": len(rows) - found,
            "max_delta_mm": worst if found else None, "rows": rows,
            "reading": "scene-versus-record agreement only; says nothing about CT"}


# --------------------------------------------------------------------------
# Snapshot of pre-existing objects (non-destruction guard)
# --------------------------------------------------------------------------
def _round_seq(seq, nd=9):
    return tuple(round(float(v), nd) for v in seq)


def snapshot_objects(bpy):
    snap = {}
    for ob in bpy.data.objects:
        mw = tuple(_round_seq(row) for row in ob.matrix_world)
        entry = {"type": ob.type, "matrix_world": mw, "parent": getattr(ob.parent, "name", None)}
        data = getattr(ob, "data", None)
        if ob.type == "MESH" and data is not None:
            entry["verts"] = hashlib.sha256(repr([_round_seq(v.co) for v in data.vertices]).encode()).hexdigest()
        elif ob.type == "ARMATURE" and data is not None:
            entry["bones"] = hashlib.sha256(repr(sorted(
                (b.name, _round_seq(b.head_local), _round_seq(b.tail_local)) for b in data.bones)).encode()).hexdigest()
        snap[ob.name] = entry
    return snap


def assert_unchanged(before, after):
    changed = [n for n in before if n not in after or before[n] != after[n]]
    if changed:
        raise SceneSafetyError(f"pre-existing objects changed: {sorted(changed)[:10]}")
    return True


# --------------------------------------------------------------------------
# bpy application (bpy is passed in so tests can supply a fake)
# --------------------------------------------------------------------------
def _set_props(obj, props):
    for k, v in props.items():
        obj[k] = v


def _new_collection(bpy, name):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def _add_empty(bpy, coll, spec, display="SPHERE", size=0.006):
    obj = bpy.data.objects.new(spec["name"], None)
    obj.empty_display_type = display
    obj.empty_display_size = size
    obj.location = tuple(spec["location_m"])
    _set_props(obj, spec["props"])
    coll.objects.link(obj)
    return obj


def _add_stick(bpy, coll, spec):
    mesh = bpy.data.meshes.new(spec["name"] + "_mesh")
    mesh.from_pydata([tuple(spec["head_m"]), tuple(spec["tail_m"])], [(0, 1)], [])
    mesh.update()
    obj = bpy.data.objects.new(spec["name"], mesh)
    _set_props(obj, spec["props"])
    coll.objects.link(obj)
    return obj


def _add_plane(bpy, coll, spec):
    c = spec["corners_m"]
    order = ("TL", "TR", "BR", "BL")
    mesh = bpy.data.meshes.new(spec["name"] + "_mesh")
    mesh.from_pydata([tuple(c[k]) for k in order], [], [(0, 1, 2, 3)])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for loop_index, key in enumerate(order):          # one polygon: loops follow vertex order
        uv_layer.data[loop_index].uv = spec["uv"][key]
    image = bpy.data.images.load(spec["image_path"], check_existing=True)
    image.colorspace_settings.name = "Non-Color"
    mat = bpy.data.materials.new(spec["name"] + "_mat")
    try:
        mat.use_nodes = True
    except Exception:                                  # deprecated/removed in newer Blender
        pass
    nt = mat.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = image
    emit = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(spec["name"], mesh)
    _set_props(obj, spec["props"])
    coll.objects.link(obj)
    return obj, image


def apply_plan(bpy, ct_plan, skel_plans, skel_label):
    """Create ONLY new objects/collections.  Returns names created."""
    created = {"collections": [], "objects": [], "images": []}
    if ct_plan is not None:
        coll = _new_collection(bpy, CT_COLLECTION)
        created["collections"].append(coll.name)
        for spec in ct_plan["planes"]:
            obj, image = _add_plane(bpy, coll, spec)
            created["objects"].append(obj.name)
            created["images"].append(image.name)
        for spec in ct_plan["corner_markers"]:
            created["objects"].append(_add_empty(bpy, coll, spec, "PLAIN_AXES", 0.012).name)
    coll = _new_collection(bpy, SKEL_COLLECTION_PREFIX + skel_label)
    created["collections"].append(coll.name)
    for spec in skel_plans["points"]:
        created["objects"].append(_add_empty(bpy, coll, spec).name)
    for spec in skel_plans["sticks"]:
        created["objects"].append(_add_stick(bpy, coll, spec).name)
    if skel_plans["p1_points"]:
        pcoll = _new_collection(bpy, P1_COLLECTION)
        created["collections"].append(pcoll.name)
        for spec in skel_plans["p1_points"]:
            created["objects"].append(_add_empty(bpy, pcoll, spec, "CUBE", 0.008).name)
    return created


def verify_images_external(bpy, image_names, cache_dir):
    cache = Path(cache_dir).resolve()
    for name in image_names:
        im = bpy.data.images[name]
        if im.packed_file is not None:
            raise SceneSafetyError(f"image {name} is packed; CT pixels must stay external")
        p = Path(bpy.path.abspath(im.filepath)).resolve()
        if cache not in p.parents:
            raise SceneSafetyError(f"image {name} is not under the private cache directory")
    return True


def read_existing_skeleton(bpy, record):
    """World-space head/tail and marker centres of the opened accepted skeleton, if present."""
    bones, markers = {}, {}
    arm = bpy.data.objects.get(MASTER_ARMATURE)
    if arm is not None and arm.type == "ARMATURE":
        by_name = {b.name: b for b in arm.data.bones}
        for key in skel.BONES:
            b = by_name.get("anat_" + key)
            if b is not None:
                h, t = arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local
                bones[key] = (tuple(h), tuple(t))
    for key in skel.MARKERS:
        ob = bpy.data.objects.get("HGPT_JOINT_" + key)
        if ob is not None:
            markers[key] = tuple(ob.matrix_world.translation)
    return bones, markers


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--ct-dir", type=Path)
    p.add_argument("--cache-dir", type=Path)
    p.add_argument("--skip-ct", action="store_true", help="skeleton inspection only; no CT access")
    p.add_argument("--skeleton-label", choices=("a003", "c004"), default="a003")
    p.add_argument("--display-offset", type=float, nargs=3, default=list(DEFAULT_DISPLAY_OFFSET_M),
                   metavar=("X_M", "Y_M", "Z_M"))
    p.add_argument("--window-low", type=int)
    p.add_argument("--window-high", type=int)
    p.add_argument("--fresh", action="store_true", help="start from an empty factory scene")
    p.add_argument("--report-out", type=Path, required=True)
    p.add_argument("--save-as", type=Path, help="new private .blend (create-only, outside the repo)")
    a = p.parse_args(argv)
    if not a.skip_ct and (a.ct_dir is None or a.cache_dir is None):
        p.error("--ct-dir and --cache-dir are required unless --skip-ct is given")
    return a


def prepare_ct(args, manifest):
    """Validate pins, parse headers, write display copies.  Returns (geoms, display_records)."""
    display = geo.write_display_copies(args.ct_dir, manifest, args.cache_dir,
                                       args.window_low, args.window_high)
    cache = str(Path(args.cache_dir).resolve())
    for d in display:
        d["_cache_dir"] = cache
    geoms = {}
    base = Path(args.ct_dir).resolve()
    for sid in geo.ALL_IDS:
        geoms[sid] = geo.parse_scanner_header((base / geo.frame_name(sid, "txt")).read_bytes())
    for ids in geo.TRIPLETS:
        geo.check_contiguity([geoms[i] for i in ids])
    for sid in geo.ALL_IDS:
        if abs(geoms[sid]["scanner_S_mm"] - manifest["by_id"][sid]["scanner_S_mm"]) > 1e-9:
            raise geo.PinError(f"cvm{sid}f: header scanner S differs from the pin")
    return geoms, display


def run(bpy, args):
    manifest = geo.load_pinned_manifest(args.manifest)
    docs, _ = skel.load_inputs(REPO_ROOT)
    record = docs[args.skeleton_label]
    out_path = Path(args.report_out)          # hashes/geometry only, so it may live in the repo
    if out_path.exists():
        raise FileExistsError(f"{out_path} exists; reports are create-only")
    if args.save_as is not None:
        geo.assert_private_location(args.save_as)
        if Path(args.save_as).exists():
            raise FileExistsError("--save-as target exists; refusing to overwrite")
        if bpy.data.filepath and Path(bpy.data.filepath).resolve() == Path(args.save_as).resolve():
            raise SceneSafetyError("refusing to overwrite the opened .blend")
    ct_plan, geoms, display = None, {}, []
    if not args.skip_ct:
        geoms, display = prepare_ct(args, manifest)
        ct_plan = build_ct_plan(manifest, geoms, display, tuple(args.display_offset))
    skel_plans = build_skeleton_plan(record, args.skeleton_label, docs["s1_frame_p1"])
    if args.fresh:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    before = snapshot_objects(bpy)
    existing_bones, existing_markers = read_existing_skeleton(bpy, record)
    created = apply_plan(bpy, ct_plan, skel_plans, args.skeleton_label)
    after = snapshot_objects(bpy)
    assert_unchanged(before, after)
    if ct_plan is not None:
        verify_images_external(bpy, created["images"], args.cache_dir)
    comparison = (compare_existing_skeleton(record, existing_bones, existing_markers)
                  if (existing_bones or existing_markers) else
                  {"items_found": 0, "reading": "no accepted-skeleton armature or markers open in this scene"})
    saved = None
    if args.save_as is not None:
        bpy.ops.wm.save_as_mainfile(filepath=str(args.save_as), copy=True)
        saved = {"path": str(args.save_as),
                 "sha256": hashlib.sha256(Path(args.save_as).read_bytes()).hexdigest(),
                 "contains_packed_ct_pixels": False,
                 "must_stay_private_and_untracked": True}
    report = {
        "schema_version": 1,
        "kind": "CT_PELVIS_REVIEW_SCENE_SETUP_REPORT",
        "blender_version": getattr(getattr(bpy, "app", None), "version_string", None),
        "skeleton_label": args.skeleton_label,
        "ct_included": ct_plan is not None,
        "private_inputs_validated_against_pins": ct_plan is not None,
        "display_offset_m": list(args.display_offset),
        "display_axis_signs_RAS_to_project": list(geo.DISPLAY_AXIS_SIGNS),
        "created": created,
        "preexisting_object_count": len(before),
        "preexisting_objects_unchanged": True,
        "ct_images_packed": False,
        "existing_skeleton_comparison": comparison,
        "planes": ([{"name": p["name"], "scanner_S_mm": p["props"]["scanner_S_mm"],
                     "png_sha256": p["props"]["png_sha256"],
                     "corners_display_m": p["corners_m"]} for p in ct_plan["planes"]]
                   if ct_plan else []),
        "saved_blend": saved,
        "anatomical_region_identified": False,
        "HomeGymPT_world_transform_applied": False,
        "canonical_promotion_allowed": False,
        "skeleton_geometry_modified": False,
    }
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main():
    import bpy  # noqa: WPS433 - only available inside Blender
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    report = run(bpy, parse_args(argv))
    print(json.dumps({k: report[k] for k in ("kind", "ct_included", "preexisting_objects_unchanged",
                                              "ct_images_packed")}))


if __name__ == "__main__":
    main()
