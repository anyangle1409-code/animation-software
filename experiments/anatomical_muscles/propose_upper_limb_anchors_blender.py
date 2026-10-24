"""PROPOSED (unreviewed) origin / insertion anchors for the shoulder and arm muscles of ONE anatomical side, computed on a
hash-checked copy of the pinned ORIGINAL_v1 R41 blend from its own landmark empties (LM_*) and anatomical bones
(anat_*), by explicit textbook rules.  Read-only: the blend is never saved.

Output: a proposal file (NOT merged into the registry).  Every anchor carries the rule it came from and the landmark /
bone inputs; `review` stays empty so registry.binding_errors() keeps reporting these muscles as unreviewed - a computed
point is not anatomical proof.  Side: the landmark/bone names carry the anatomical side; on R41 anatomical left is +X
(runtime V4 '_l' is -X, so anatomical left drives runtime '_r'), checked here from the landmark positions.

Rules (attachment descriptions per the seed records - Gray's Anatomy / StatPearls; positions are rule-of-thumb
fractions along the native segments, recorded per anchor so a reviewer can replace any of them):
  humerus fractions are from the GH centre (LM GH) to the elbow joint centre (LM EJC); clavicle fractions from SC to AC;
  scapular spine from TS to AA; offsets in the body frame (anterior = -Y, up = +Z, lateral = +X on the left).

usage: python3.13 propose_upper_limb_anchors_blender.py -- COPY.blend SHA256 OUT.json [left|right] [render_dir]
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
src, expected, out = Path(args[0]), args[1], Path(args[2])
SIDE = args[3] if len(args) > 3 else "left"
RENDER = Path(args[4]) if len(args) > 4 else None
if out.exists():
    raise ValueError("output must be new")
before = hashlib.sha256(src.read_bytes()).hexdigest()
if before != expected:
    raise ValueError("copy hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
B = anat.data.bones


def LM(name):
    return bpy.data.objects[f"LM_{name}"].matrix_world.translation.copy()


S = SIDE
lat_sign = 1.0 if LM(f"scapula_{S}__GH").x > 0 else -1.0
LAT, ANT, UP = Vector((lat_sign, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))
GH, EJC = LM(f"scapula_{S}__GH"), LM(f"humerus_{S}__EJC")
SC, AC = LM(f"clavicle_{S}__SC"), LM(f"clavicle_{S}__AC")
AA, TS, AI = LM(f"scapula_{S}__AA"), LM(f"scapula_{S}__TS"), LM(f"scapula_{S}__AI")
IJ, PX = LM("sternum__ij_skin"), LM("sternum__px_skin")
RS = LM(f"humerus_{S}__styloid_radial_skin")


def hum(f):
    return GH.lerp(EJC, f)


def bone_pt(name, f):
    b = B[name]
    return (anat.matrix_world @ b.head_local).lerp(anat.matrix_world @ b.tail_local, f)


def spinous(v):
    """posterior tip of a vertebra: bone head pushed 4 cm posteriorly (spinous process length, rule of thumb)"""
    return (anat.matrix_world @ B[f"anat_{v}"].head_local) + Vector((0, 0.04, 0))


R_ = {  # muscle: [(role, bone, point, rule)]
    "deltoid_anterior": [("origin", f"anat_clavicle_{S}", SC.lerp(AC, 0.80) + ANT * 0.008, "anterior border, lateral third of clavicle: 80 % SC->AC, 8 mm anterior"),
                         ("insertion", f"anat_humerus_{S}", hum(0.45) + LAT * 0.012, "deltoid tuberosity: 45 % GH->EJC, 12 mm lateral")],
    "deltoid_middle": [("origin", f"anat_scapula_{S}", AA.lerp(AC, 0.4) + LAT * 0.005, "lateral margin of acromion: 40 % AA->AC, 5 mm lateral"),
                       ("insertion", f"anat_humerus_{S}", hum(0.45) + LAT * 0.012, "deltoid tuberosity")],
    "deltoid_posterior": [("origin", f"anat_scapula_{S}", TS.lerp(AA, 0.70) - UP * 0.008, "inferior lip of the spine of the scapula: 70 % TS->AA, 8 mm below"),
                          ("insertion", f"anat_humerus_{S}", hum(0.45) + LAT * 0.012, "deltoid tuberosity")],
    "supraspinatus": [("origin", f"anat_scapula_{S}", TS.lerp(AA, 0.30) + UP * 0.03, "supraspinous fossa, medial two-thirds: 30 % TS->AA, 30 mm above the spine"),
                      ("insertion", f"anat_humerus_{S}", GH + LAT * 0.022 + UP * 0.012, "greater tubercle, superior facet: GH + 22 mm lateral, 12 mm up")],
    "infraspinatus": [("origin", f"anat_scapula_{S}", (TS + AI + TS.lerp(AA, 0.5)) / 3.0, "infraspinous fossa: centroid of TS, AI and mid-spine"),
                      ("insertion", f"anat_humerus_{S}", GH + LAT * 0.022 - ANT * 0.010, "greater tubercle, middle facet: GH + 22 mm lateral, 10 mm posterior")],
    "teres_major": [("origin", f"anat_scapula_{S}", AI + LAT * 0.012, "dorsal surface of the inferior angle: AI + 12 mm lateral"),
                    ("insertion", f"anat_humerus_{S}", hum(0.20) + ANT * 0.010 - LAT * 0.006, "medial lip of the intertubercular sulcus: 20 % GH->EJC, anterior-medial")],
    "latissimus_dorsi": [("origin", "anat_t9", spinous("t9"), "spinous processes T7-L5 / thoracolumbar fascia (represented at T9 spinous; broad origin - a fan is required)"),
                         ("insertion", f"anat_humerus_{S}", hum(0.15) + ANT * 0.012, "floor of the intertubercular sulcus: 15 % GH->EJC, 12 mm anterior")],
    "pectoralis_major_clavicular": [("origin", f"anat_clavicle_{S}", SC.lerp(AC, 0.30) + ANT * 0.008, "anterior surface, medial half of clavicle: 30 % SC->AC"),
                                    ("insertion", f"anat_humerus_{S}", hum(0.18) + ANT * 0.012 + LAT * 0.006, "lateral lip of the intertubercular sulcus: 18 % GH->EJC")],
    "pectoralis_major_sternocostal": [("origin", "anat_sternum", IJ.lerp(PX, 0.5) + LAT * 0.015, "anterior sternum and costal cartilages 1-6: mid-sternum, 15 mm lateral (broad origin - a fan is required)"),
                                      ("insertion", f"anat_humerus_{S}", hum(0.20) + ANT * 0.012 + LAT * 0.006, "lateral lip of the intertubercular sulcus, below the clavicular head")],
    "biceps_brachii_long": [("origin", f"anat_scapula_{S}", GH + UP * 0.020, "supraglenoid tubercle: 20 mm above the GH centre (tendon runs in the intertubercular groove)"),
                            ("insertion", f"anat_radius_{S}", bone_pt(f"anat_radius_{S}", 0.12) + ANT * 0.008, "radial tuberosity: 12 % along the radius, 8 mm anterior")],
    "biceps_brachii_short": [("origin", f"anat_scapula_{S}", GH + ANT * 0.030 - LAT * 0.020 + UP * 0.010, "coracoid process tip (no native PC landmark): GH + 30 mm anterior, 20 mm medial, 10 mm up"),
                             ("insertion", f"anat_radius_{S}", bone_pt(f"anat_radius_{S}", 0.12) + ANT * 0.008, "radial tuberosity")],
    "brachialis": [("origin", f"anat_humerus_{S}", hum(0.55) + ANT * 0.010, "distal half of the anterior humerus: 55 % GH->EJC, 10 mm anterior"),
                   ("insertion", f"anat_ulna_{S}", bone_pt(f"anat_ulna_{S}", 0.08) + ANT * 0.010, "ulnar tuberosity / coronoid: 8 % along the ulna, 10 mm anterior")],
    "triceps_long": [("origin", f"anat_scapula_{S}", GH - UP * 0.025 - ANT * 0.008, "infraglenoid tubercle: 25 mm below, 8 mm posterior to GH"),
                     ("insertion", f"anat_ulna_{S}", EJC - ANT * 0.022, "olecranon: 22 mm posterior to the elbow joint centre")],
    "triceps_lateral": [("origin", f"anat_humerus_{S}", hum(0.30) - ANT * 0.010 + LAT * 0.008, "posterior humerus above the radial groove: 30 % GH->EJC"),
                        ("insertion", f"anat_ulna_{S}", EJC - ANT * 0.022, "olecranon")],
    "triceps_medial": [("origin", f"anat_humerus_{S}", hum(0.60) - ANT * 0.010 - LAT * 0.004, "posterior humerus below the radial groove: 60 % GH->EJC"),
                       ("insertion", f"anat_ulna_{S}", EJC - ANT * 0.022, "olecranon")],
    "brachioradialis": [("origin", f"anat_humerus_{S}", hum(0.75) + LAT * 0.015, "lateral supracondylar ridge: 75 % GH->EJC, 15 mm lateral"),
                        ("insertion", f"anat_radius_{S}", bone_pt(f"anat_radius_{S}", 0.97) + LAT * 0.004, "radial styloid base: 97 % along the radius")],
    "trapezius_upper": [("origin", "anat_c4", spinous("c4"), "ligamentum nuchae / C1-C6 (represented at C4 spinous)"),
                        ("insertion", f"anat_clavicle_{S}", SC.lerp(AC, 0.80) - ANT * 0.008, "posterior border, lateral third of clavicle")],
    "trapezius_middle": [("origin", "anat_t2", spinous("t2"), "spinous processes C7-T3 (represented at T2)"),
                         ("insertion", f"anat_scapula_{S}", AA + UP * 0.005, "acromion medial margin / superior lip of the spine (at AA)")],
    "trapezius_lower": [("origin", "anat_t9", spinous("t9"), "spinous processes T4-T12 (represented at T9)"),
                        ("insertion", f"anat_scapula_{S}", TS + LAT * 0.010, "root of the spine of the scapula (TS + 10 mm lateral)")],
    "serratus_anterior": [("origin", f"anat_rib_05_{S}", bone_pt(f"anat_rib_05_{S}", 0.55), "lateral surfaces of ribs 1-8/9 (represented at rib 5, 55 % along; digitations required)"),
                          ("insertion", f"anat_scapula_{S}", TS.lerp(AI, 0.5) + ANT * 0.010, "costal surface of the medial border: mid TS->AI, 10 mm anterior")],
}


def local(bone_name, p):
    b = B[bone_name]
    return list((anat.matrix_world @ b.matrix_local).inverted() @ p)


sid = "L" if SIDE == "left" else "R"
props = {}
for m, items in R_.items():
    anchors = []
    for role, bone, p, rule in items:
        anchors.append({"role": role, "bone": bone, "local_m": [round(x, 6) for x in local(bone, p)],
                        "world_rest_m": [round(x, 5) for x in p], "rule": rule})
    o, i = anchors[0]["world_rest_m"], anchors[-1]["world_rest_m"]
    L = sum((a - b) ** 2 for a, b in zip(o, i)) ** 0.5
    props[f"hgpt.muscle.{m}.{sid}"] = {"anchors": anchors, "rest_straight_length_m": round(L, 4),
                                       "source_sha256": before, "anatomical_side": SIDE, "anatomical_side_x_sign": lat_sign,
                                       "review": {"reviewer": None, "evidence": None}, "wrap_reviewed": False,
                                       "status": "PROPOSED_UNREVIEWED"}
after = hashlib.sha256(src.read_bytes()).hexdigest()
if after != before:
    raise RuntimeError("source changed")
report = {"status": "proposal_only", "blender_version": bpy.app.version_string, "source_sha256": before,
          "source_unchanged": True, "side": SIDE, "proposals": props}
with out.open("x") as f:
    json.dump(report, f, indent=1)
print("PROPOSED", len(props), "muscles;", json.dumps({k: v["rest_straight_length_m"] for k, v in props.items()}))

# ------------------------------------------------------------------ review renders (lines over the skeleton guide)
if RENDER:
    RENDER.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
    for ob in sc.objects:
        ob.hide_render = ob.type not in ("MESH", "CURVE", "ARMATURE") or (ob.type == "MESH" and ob is not body)
    mat_b = bpy.data.materials.new("BODY"); mat_b.diffuse_color = (0.8, 0.7, 0.6, 0.18)
    body.data.materials.clear(); body.data.materials.append(mat_b)
    cols = {"deltoid": (0.9, 0.2, 0.2, 1), "biceps": (0.2, 0.4, 0.95, 1), "brachialis": (0.2, 0.7, 0.9, 1), "triceps": (0.95, 0.6, 0.1, 1),
            "pectoralis": (0.7, 0.2, 0.8, 1), "latissimus": (0.2, 0.7, 0.3, 1), "trapezius": (0.6, 0.6, 0.1, 1), "default": (0.3, 0.3, 0.3, 1)}
    for mid, pr in props.items():
        name = mid.split(".")[2]
        cd = bpy.data.curves.new(name, "CURVE"); cd.dimensions = "3D"; cd.bevel_depth = 0.004
        sp = cd.splines.new("POLY"); sp.points.add(1)
        for k, a in enumerate((pr["anchors"][0], pr["anchors"][-1])):
            sp.points[k].co = (*a["world_rest_m"], 1)
        ob = bpy.data.objects.new(name, cd); sc.collection.objects.link(ob)
        m_ = bpy.data.materials.new(name); m_.diffuse_color = next((c for k, c in cols.items() if name.startswith(k)), cols["default"])
        cd.materials.append(m_)
    # bones as thin sticks
    for b in B:
        if any(k in b.name for k in ("clavicle", "scapula", "humerus", "radius", "ulna", "sternum", "rib", "anat_t", "anat_c", "anat_l")):
            cd = bpy.data.curves.new(b.name, "CURVE"); cd.dimensions = "3D"; cd.bevel_depth = 0.003
            sp = cd.splines.new("POLY"); sp.points.add(1)
            sp.points[0].co = (*(anat.matrix_world @ b.head_local), 1); sp.points[1].co = (*(anat.matrix_world @ b.tail_local), 1)
            ob = bpy.data.objects.new(b.name + "_stick", cd); sc.collection.objects.link(ob)
            mb = bpy.data.materials.new("bone"); mb.diffuse_color = (0.95, 0.95, 0.9, 1); cd.materials.append(mb)
    camd = bpy.data.cameras.new("C"); camd.type = "ORTHO"; camd.ortho_scale = 0.75
    cam = bpy.data.objects.new("C", camd); sc.collection.objects.link(cam); sc.camera = cam
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_xray = False
    sc.render.resolution_x = 800; sc.render.resolution_y = 1000
    c = (GH + EJC) / 2.0; c.x *= 0.6
    for view, dv in {"front": (0, -1, 0), "back": (0, 1, 0), "side": (lat_sign, 0, 0)}.items():
        d = Vector(dv); cam.location = c + d * 3; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        sc.render.filepath = str(RENDER / f"anchors_{SIDE}_{view}.png"); bpy.ops.render.render(write_still=True)
    print("RENDERED", RENDER)
