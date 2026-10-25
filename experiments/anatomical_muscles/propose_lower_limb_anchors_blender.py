"""PROPOSED (unreviewed) origin / insertion anchors for the hip, thigh and calf muscles of ONE anatomical side - the
muscles of Work's squat contract - computed on a hash-checked copy of the pinned ORIGINAL_v1 R41 blend from its own
landmark empties (LM_*) and anatomical bones (anat_*), by explicit textbook rules.  Read-only: the blend is never saved.
Companion of propose_upper_limb_anchors_blender.py; same output format and status (review empty, wrap_reviewed false,
PROPOSED_UNREVIEWED), so registry.binding_errors() keeps every one of them as not ready.

R41 has no landmarks for PSIS, AIIS, the ischial tuberosity, the tibial tuberosity or the femoral condyles, so those
are rule-of-thumb offsets from the landmarks it does have (HJC, ASIS, trochanterion, KJC, epicondyles, AJC, tibial
plateau) and from the bone segments; each anchor records its rule.  Skin landmarks are inset towards the bone (SKIN mm).
Each muscle may carry a `wrap` hint (joint, side, radius) for the path check - a cylinder about the joint's flexion axis
that the path must pass around (quadriceps over the front of the knee, hamstrings / gastrocnemius behind it, gluteus
maximus behind the hip: without it the straight line runs through the hip joint and barely changes with flexion).

usage: python3.13 propose_lower_limb_anchors_blender.py -- COPY.blend SHA256 OUT.json [left|right]
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
SKIN = 0.012
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
HJC, ASIS, TROC = LM(f"hip_bone_{S}__HJC"), LM(f"hip_bone_{S}__asis_skin"), LM(f"hip_bone_{S}__trochanterion_skin")
KJC, EL, EM = LM(f"femur_{S}__KJC"), LM(f"femur_{S}__epicondyle_lateral_skin"), LM(f"femur_{S}__epicondyle_medial_skin")
AJC, PLAT = LM(f"tibia_{S}__AJC"), LM(f"tibia_{S}__tibial_plateau")
lat_sign = 1.0 if HJC.x > 0 else -1.0
LAT, ANT, UP = Vector((lat_sign, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))


def fem(f):
    return HJC.lerp(KJC, f)


def tib(f):
    return PLAT.lerp(AJC, f)


def head(name):
    return anat.matrix_world @ B[name].head_local


def tail(name):
    return anat.matrix_world @ B[name].tail_local


ISCH = HJC - UP * 0.050 + ANT * -0.035 - LAT * 0.015          # ischial tuberosity (no native landmark)
TT = tib(0.08) + ANT * 0.030                                   # tibial tuberosity (no native landmark)
EMb, ELb = EM + LAT * SKIN, EL - LAT * SKIN                    # epicondyles, inset from the skin
CALC = tail(f"anat_calcaneus_{S}")                             # posterior calcaneal tuberosity end of the bone
PSIS_ = head(f"anat_hip_bone_{S}") - ANT * 0.020              # posterior ilium near the PSIS
QUAD_WRAP = {"joint": "knee", "side": "anterior", "radius_m": 0.040}
HAM_WRAP = {"joint": "knee", "side": "posterior", "radius_m": 0.025}
GMAX_WRAP = {"joint": "hip", "side": "posterior", "radius_m": 0.050}   # over the ischium / greater trochanter bulk

R_ = {  # muscle: ([(role, bone, point, rule)], wrap)
    "gluteus_maximus": ([("origin", "anat_sacrum", PSIS_ - LAT * 0.015, "posterior ilium / dorsal sacrum: hip-bone head (posterior ilium) + 20 mm posterior, 15 mm medial (broad origin - a fan is required)"),
                         ("insertion", f"anat_femur_{S}", fem(0.20) - ANT * 0.012 + LAT * 0.010, "gluteal tuberosity: 20 % HJC->KJC, 12 mm posterior, 10 mm lateral (ITT part not represented)")], GMAX_WRAP),
    "gluteus_medius": ([("origin", f"anat_hip_bone_{S}", HJC + UP * 0.075 + LAT * 0.010 - ANT * 0.010, "outer ilium between the gluteal lines: HJC + 75 mm up, 10 mm lateral, 10 mm posterior (broad origin - a fan is required)"),
                        ("insertion", f"anat_femur_{S}", TROC - LAT * 0.015 + UP * 0.010, "greater trochanter, lateral facet: trochanterion skin inset 15 mm, 10 mm up")], None),
    "rectus_femoris": ([("origin", f"anat_hip_bone_{S}", HJC + ANT * 0.030 + UP * 0.030, "AIIS (no native landmark): HJC + 30 mm anterior, 30 mm up"),
                        ("insertion", f"anat_tibia_{S}", TT, "tibial tuberosity via the patella: 8 % plateau->AJC, 30 mm anterior")], QUAD_WRAP),
    "vastus_lateralis": ([("origin", f"anat_femur_{S}", fem(0.15) + LAT * 0.025, "proximal lateral femur / greater trochanter base: 15 % HJC->KJC, 25 mm lateral"),
                          ("insertion", f"anat_tibia_{S}", TT, "tibial tuberosity via the patella")], QUAD_WRAP),
    "vastus_medialis": ([("origin", f"anat_femur_{S}", fem(0.40) - LAT * 0.015 - ANT * 0.010, "medial linea aspera: 40 % HJC->KJC, 15 mm medial, 10 mm posterior"),
                         ("insertion", f"anat_tibia_{S}", TT, "tibial tuberosity via the patella")], QUAD_WRAP),
    "vastus_intermedius": ([("origin", f"anat_femur_{S}", fem(0.35) + ANT * 0.015, "anterior femoral shaft: 35 % HJC->KJC, 15 mm anterior"),
                            ("insertion", f"anat_tibia_{S}", TT, "tibial tuberosity via the patella")], QUAD_WRAP),
    "adductor_magnus_hamstring": ([("origin", f"anat_hip_bone_{S}", ISCH, "ischial tuberosity (no native landmark): HJC - 50 mm, 35 mm posterior, 15 mm medial"),
                                   ("insertion", f"anat_femur_{S}", EMb + UP * 0.020, "adductor tubercle: medial epicondyle (skin inset 12 mm) + 20 mm up")], None),
    "biceps_femoris_long": ([("origin", f"anat_hip_bone_{S}", ISCH, "ischial tuberosity"),
                             ("insertion", f"anat_fibula_{S}", head(f"anat_fibula_{S}"), "fibular head: head of the anat_fibula bone")], HAM_WRAP),
    "semitendinosus": ([("origin", f"anat_hip_bone_{S}", ISCH, "ischial tuberosity"),
                        ("insertion", f"anat_tibia_{S}", tib(0.12) - LAT * 0.020 + ANT * 0.010, "pes anserinus: 12 % plateau->AJC, 20 mm medial, 10 mm anterior")], HAM_WRAP),
    "semimembranosus": ([("origin", f"anat_hip_bone_{S}", ISCH, "ischial tuberosity"),
                         ("insertion", f"anat_tibia_{S}", tib(0.03) - LAT * 0.022 - ANT * 0.012, "posteromedial medial tibial condyle: 3 % plateau->AJC, 22 mm medial, 12 mm posterior")], HAM_WRAP),
    "gastrocnemius_medial": ([("origin", f"anat_femur_{S}", EMb - ANT * 0.020 + UP * 0.010, "posterior medial femoral condyle: medial epicondyle (inset) + 20 mm posterior, 10 mm up"),
                              ("insertion", f"anat_calcaneus_{S}", CALC, "calcaneal tuberosity via the Achilles tendon: posterior end of anat_calcaneus")], HAM_WRAP),
    "soleus": ([("origin", f"anat_tibia_{S}", tib(0.22) - ANT * 0.020 + LAT * 0.010, "soleal line / posterior tibia and fibula: 22 % plateau->AJC, 20 mm posterior, 10 mm lateral"),
                ("insertion", f"anat_calcaneus_{S}", CALC, "calcaneal tuberosity via the Achilles tendon")], None),
}


# broad (fan) muscles: extra fibre origins sharing the muscle's insertion.  The main origin is the middle fibre; the check
# judges the muscle by its mean fibre change and reports each fibre.
FIBRES = {
    "gluteus_medius": [
        ("anterior", f"anat_hip_bone_{S}", HJC + UP * 0.065 + LAT * 0.015 + ANT * 0.030, "anterior fibres: outer ilium below the iliac crest, behind the ASIS: HJC + 65 mm up, 15 mm lateral, 30 mm anterior"),
        ("middle", None, None, "the main origin"),
        ("posterior", f"anat_hip_bone_{S}", HJC + UP * 0.060 - ANT * 0.050, "posterior fibres: in front of the posterior gluteal line: HJC + 60 mm up, 50 mm posterior"),
    ],
}


def local(bone_name, p):
    b = B[bone_name]
    return list((anat.matrix_world @ b.matrix_local).inverted() @ p)


sid = "L" if SIDE == "left" else "R"
props = {}
for m, (items, wrap) in R_.items():
    anchors = [{"role": role, "bone": bone, "local_m": [round(x, 6) for x in local(bone, p)],
                "world_rest_m": [round(x, 5) for x in p], "rule": rule} for role, bone, p, rule in items]
    o, i = anchors[0]["world_rest_m"], anchors[-1]["world_rest_m"]
    props[f"hgpt.muscle.{m}.{sid}"] = {"anchors": anchors, "rest_straight_length_m": round(sum((a - b) ** 2 for a, b in zip(o, i)) ** 0.5, 4),
                                       "wrap_hint": wrap, "source_sha256": before, "anatomical_side": SIDE,
                                       "anatomical_side_x_sign": lat_sign, "review": {"reviewer": None, "evidence": None},
                                       "wrap_reviewed": False, "status": "PROPOSED_UNREVIEWED"}
    if m in FIBRES:
        props[f"hgpt.muscle.{m}.{sid}"]["fibres"] = [
            {"name": n, "origin": anchors[0] if b_ is None else
             {"role": "origin", "bone": b_, "local_m": [round(x, 6) for x in local(b_, p_)],
              "world_rest_m": [round(x, 5) for x in p_], "rule": r_}} for n, b_, p_, r_ in FIBRES[m]]
if hashlib.sha256(src.read_bytes()).hexdigest() != before:
    raise RuntimeError("source changed")
with out.open("x") as f:
    json.dump({"status": "proposal_only", "blender_version": bpy.app.version_string, "source_sha256": before,
               "source_unchanged": True, "side": SIDE, "region": "lower_limb", "proposals": props}, f, indent=1)
print("PROPOSED", len(props), "muscles;", json.dumps({k: v["rest_straight_length_m"] for k, v in props.items()}))
