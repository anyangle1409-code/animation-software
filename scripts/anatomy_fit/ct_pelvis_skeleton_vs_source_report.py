#!/usr/bin/env python3
"""Read-only skeleton-versus-source inspection report for the pelvis/hip/lumbar region.

The SOURCE SKELETON governs geometry.  This tool never writes to any skeleton
record, never produces a corrected coordinate, and never fits a mesh.  It:

  * extracts the pelvic / S1 / L4-L5 / acetabular / hip-centre entries from the
    a003 record and the c004 candidate record and states, byte-for-byte, whether
    c004 changes any of them;
  * recomputes derived skeleton quantities (inter-HJC distance, HJC-midpoint to
    S1, to the pubic symphysis, sacral length, L4/L5 vectors) from the records;
  * checks them against the sourced corridors ALREADY in the repository and
    against the provisional P1 S1 frame, as diagnostics only;
  * lists, for each quantity, what CT observation would test it and whether the
    two pinned 9 mm windows could possibly do so.

No CT-vs-skeleton numerical comparison is made: no CT landmark is verified, the
scanner -> skeleton transform is unverified, and this donor is one cadaver, not
a canonical 182 cm male.  Outputs are create-only.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ANATOMY = Path("ORIGINAL_V1_WORK/anatomy")
INPUTS = {
    "a003": ANATOMY / "character_fit_r95_a003.json",
    "c004": ANATOMY / "audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json",
    "pelvis_targets": ANATOMY / "canonical_pelvis_landmark_targets_v1.json",
    "pelvis_audit": ANATOMY / "canonical_pelvis_geometry_audit_v1.json",
    "s1_frame_p1": ANATOMY / "canonical_s1_pelvic_frame_p1.json",
    "lumbar_frames_p1": ANATOMY / "canonical_lumbar_body_disc_frames_p1.json",
    "freeze_readiness": ANATOMY / "canonical_freeze_readiness_v1.json",
}

BONES = ("sacrum", "coccyx", "l5", "l4", "hip_bone_left", "hip_bone_right",
         "femur_left", "femur_right")
MARKERS = ("hip_left", "hip_right",
           "sacroiliac_anterior_left", "sacroiliac_anterior_right",
           "sacroiliac_posterior_left", "sacroiliac_posterior_right",
           "pubic_symphysis", "sacrococcygeal",
           "disc_l4_l5", "disc_l5_sacrum",
           "facet_l4_l5_left", "facet_l4_l5_right",
           "facet_l5_sacrum_left", "facet_l5_sacrum_right")

STATEMENTS = [
    "The source skeleton governs geometry; nothing here moves, reshapes or re-fits it.",
    "c004 is an unaccepted diagnostic candidate and is not altered; there is no c005.",
    "The CT donor is one cadaver and is not a canonical 182 cm male.",
    "No CT landmark is verified, so no CT-versus-skeleton number is computed.",
    "Scanner RAS is not the Home Gym PT world frame; no transform is applied.",
    "Corridor z-scores are diagnostics against single-source summaries, not acceptance.",
]


def _mm(p):
    return [x * 1000.0 for x in p]


def _sub(a, b):
    return [x - y for x, y in zip(a, b)]


def _len(v):
    return math.sqrt(sum(x * x for x in v))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_inputs(root=REPO_ROOT):
    docs, hashes = {}, {}
    for key, rel in INPUTS.items():
        p = Path(root) / rel
        docs[key] = json.loads(p.read_text())
        hashes[str(rel)] = sha256_file(p)
    return docs, hashes


def extract_pelvic_set(record):
    """Bones/markers of interest from a fit record, converted to millimetres."""
    out = {"bones": {}, "markers": {}}
    for k in BONES:
        b = record["bones"][k]
        out["bones"][k] = {"head_mm": _mm(b["head_m"]), "tail_mm": _mm(b["tail_m"]),
                           "parent": b["parent"], "confidence": b["confidence"],
                           "placement": b["placement"]}
    for k in MARKERS:
        m = record["joint_markers"][k]
        out["markers"][k] = {"centre_mm": _mm(m["centre_m"]), "frame_bone": m["frame_bone"]}
    return out


def pelvic_set_differences(rec_a, rec_b):
    """Names of bones/markers in the set whose records differ at all."""
    diff = []
    for k in BONES:
        if rec_a["bones"][k] != rec_b["bones"][k]:
            diff.append(f"bone:{k}")
    for k in MARKERS:
        if rec_a["joint_markers"][k] != rec_b["joint_markers"][k]:
            diff.append(f"marker:{k}")
    return diff


def derive(record):
    """Skeleton-side geometric quantities (all recomputed, none copied)."""
    s = extract_pelvic_set(record)
    hl = s["markers"]["hip_left"]["centre_mm"]
    hr = s["markers"]["hip_right"]["centre_mm"]
    ha = [(a + b) / 2 for a, b in zip(hl, hr)]
    sacrum = s["bones"]["sacrum"]
    s1_tail = sacrum["tail_mm"]
    s1_disc = s["markers"]["disc_l5_sacrum"]["centre_mm"]
    symph = s["markers"]["pubic_symphysis"]["centre_mm"]

    def from_ha(p):
        v = _sub(p, ha)
        ap, up = v[1], v[2]            # +Y posterior, +Z superior
        return {"vector_mm": v, "distance_mm": _len(v),
                "posterior_tilt_from_vertical_deg": math.degrees(math.atan2(ap, up)),
                "vertical_mm": up, "posterior_mm": ap}

    def bone_vec(name):
        b = s["bones"][name]
        v = _sub(b["tail_mm"], b["head_mm"])
        return {"length_mm": _len(v), "vector_mm": v,
                "posterior_tilt_from_vertical_deg": math.degrees(math.atan2(v[1], v[2]))}

    return {
        "HJC_left_mm": hl, "HJC_right_mm": hr, "HJC_midpoint_mm": ha,
        "inter_HJC_mm": _len(_sub(hl, hr)),
        "HJC_mirror_error_mm": _len([hl[0] + hr[0], hl[1] - hr[1], hl[2] - hr[2]]),
        "HA_to_S1_via_sacrum_tail": from_ha(s1_tail),
        "HA_to_S1_via_disc_l5_sacrum": from_ha(s1_disc),
        "HA_to_pubic_symphysis": from_ha(symph),
        "sacrum_length_mm": _len(_sub(sacrum["tail_mm"], sacrum["head_mm"])),
        "l5_bone_vector": bone_vec("l5"),
        "l4_bone_vector": bone_vec("l4"),
        "disc_l4_l5_centre_mm": s["markers"]["disc_l4_l5"]["centre_mm"],
        "disc_l5_sacrum_centre_mm": s1_disc,
        "disc_l4_l5_above_HA_mm": s["markers"]["disc_l4_l5"]["centre_mm"][2] - ha[2],
        "disc_l5_sacrum_above_HA_mm": s1_disc[2] - ha[2],
    }


def z_score(value, mean, sd):
    return (value - mean) / sd


def corridor_checks(docs, derived):
    t = docs["pelvis_targets"]
    audit = docs["pelvis_audit"]
    p1 = docs["s1_frame_p1"]
    tann = next(s for s in t["sources"] if s["id"] == "TANNENBAUM_2011_PELVIMETRY")
    inter = tann["male_values_mm"]["interacetabular_distance"]
    sac = audit["sacrum_length_crosscheck"]
    pth = p1["source_family"]["pelvic_thickness_mm"]
    p1_pt = p1["derived_S1_superior_endplate"]["distance_HA_to_S1_mm"]
    a003_pt = derived["HA_to_S1_via_sacrum_tail"]["distance_mm"]
    return [
        {"quantity": "inter-HJC distance",
         "skeleton_mm": derived["inter_HJC_mm"],
         "source": "TANNENBAUM_2011_PELVIMETRY interacetabular distance (male 3D CT)",
         "citation": "Tannenbaum 2011 Clin Orthop Relat Res, PMC3018214",
         "source_mean_mm": inter["mean"], "source_sd_mm": inter["sd"],
         "source_range_mm": inter["range"],
         "z": z_score(derived["inter_HJC_mm"], inter["mean"], inter["sd"]),
         "inside_source_range": inter["range"][0] <= derived["inter_HJC_mm"] <= inter["range"][1],
         "reading": "diagnostic only; HJC spacing is retained provisionally in the repo"},
        {"quantity": "sacral length (apex to S1 endplate stick)",
         "skeleton_mm": derived["sacrum_length_mm"],
         "source": "SACRUM_MALE_MORPHOMETRY_2023 via canonical_pelvis_geometry_audit_v1.json",
         "source_mean_mm": sac["source_male_mean_mm"], "source_sd_mm": sac["source_sd_mm"],
         "z": z_score(derived["sacrum_length_mm"], sac["source_male_mean_mm"], sac["source_sd_mm"]),
         "reading": "diagnostic only; a003 sacrum is a low-confidence stick"},
        {"quantity": "HJC-midpoint to S1 centre (pelvic thickness), a003 sacrum tail",
         "skeleton_mm": a003_pt,
         "source": "HASEGAWA_2017_WHOLE_SPINE_MALE pelvic thickness (male n=40) via P1 frame",
         "source_mean_mm": pth["mean"], "source_sd_mm": pth["sd"],
         "z": z_score(a003_pt, pth["mean"], pth["sd"]),
         "reading": ("a003 places its S1 stick end about this many SD from the sourced male mean; "
                     "P1 sets 107 mm by construction. A recipe-level definition match "
                     "('S1 endplate centre') is stated by a003 but is low confidence.")},
    ]


def s1_p1_comparison(docs, derived):
    p1 = docs["s1_frame_p1"]
    d = p1["derived_S1_superior_endplate"]
    return {
        "P1_distance_HA_to_S1_mm": d["distance_HA_to_S1_mm"],
        "P1_posterior_tilt_from_vertical_deg": d["PT_from_vertical_deg"],
        "a003_distance_via_sacrum_tail_mm": derived["HA_to_S1_via_sacrum_tail"]["distance_mm"],
        "a003_tilt_via_sacrum_tail_deg": derived["HA_to_S1_via_sacrum_tail"]["posterior_tilt_from_vertical_deg"],
        "a003_distance_via_disc_l5_sacrum_mm": derived["HA_to_S1_via_disc_l5_sacrum"]["distance_mm"],
        "a003_tilt_via_disc_l5_sacrum_deg": derived["HA_to_S1_via_disc_l5_sacrum"]["posterior_tilt_from_vertical_deg"],
        "distance_difference_a003_minus_P1_mm":
            derived["HA_to_S1_via_sacrum_tail"]["distance_mm"] - d["distance_HA_to_S1_mm"],
        "tilt_difference_a003_minus_P1_deg":
            derived["HA_to_S1_via_sacrum_tail"]["posterior_tilt_from_vertical_deg"] - d["PT_from_vertical_deg"],
        "posture_note": ("P1 is a standing PTh/PT/SS family; the CT donor lay supine. Pelvic tilt and "
                         "sacral slope are posture-dependent; pelvic incidence and HJC-to-S1 distance "
                         "are geometric and are the comparable quantities."),
        "definitions_differ_note": ("a003 'S1' is a stick end; P1 is a derived endplate centre. "
                                    "Differences are diagnostics, not errors."),
    }


def ct_testability(derived, docs):
    """What each skeleton quantity needs from CT, and whether the 9 mm windows can supply it."""
    pi = docs["s1_frame_p1"]["source_family"]["pelvic_incidence_deg"]
    rows = [
        ("inter-HJC / interacetabular distance", derived["inter_HJC_mm"],
         "Circle/sphere fit to both femoral heads on their equatorial slices (same slice or measured z offset)",
         "NEEDS_IDENTIFIED_EQUATORIAL_SLICES_FOR_BOTH_HEADS",
         "A 9 mm window cannot constrain a head's z-centre; only an equatorial in-plane fit is possible, "
         "and only if both heads' equators lie in the windows. Otherwise ~16-18 contiguous 3 mm slices per head."),
        ("HJC-midpoint to S1 endplate centre (pelvic thickness)",
         derived["HA_to_S1_via_sacrum_tail"]["distance_mm"],
         "S1 superior endplate centre (needs sagittal reformat across the S1 body) plus both head centres",
         "NEEDS_ADDITIONAL_RANGES",
         "Endplate orientation and centre cannot be established from two 9 mm axial windows."),
        ("pelvic incidence (posture-independent)",
         pi["mean"],
         "S1 endplate normal and HJC midpoint in a sagittal reformat of the supine donor",
         "NEEDS_ADDITIONAL_RANGES",
         "PI is geometric, so a supine CT can be compared with a standing source; tilt and slope cannot."),
        ("HJC-midpoint to pubic symphysis",
         derived["HA_to_pubic_symphysis"]["distance_mm"],
         "Symphyseal joint centre in the midline and both head centres",
         "NEEDS_ADDITIONAL_RANGES",
         "The symphysis lies caudal and anterior to the heads; coverage of both is not established."),
        ("inter-ASIS breadth", None,
         "Left and right ASIS bony points (small vertical extent, so a few slices each)",
         "TESTABLE_ONLY_IF_ASIS_LEVEL_IS_IN_A_WINDOW",
         "a003 stores only low-confidence ASIS surface proxies (216.6 mm); canonical ASIS must be rebuilt from bone."),
        ("acetabular / femoral-head axial diameter", None,
         "In-plane circle fit on an equatorial axial slice",
         "TESTABLE_ONLY_IF_AN_EQUATORIAL_SLICE_IS_IN_A_WINDOW",
         "The skeleton stores HJC only, not a diameter; the corridor 47-59 mm (cup) is a scale gate, not a skeleton number."),
        ("L4/L5 and L5/S1 disc level above HJC midpoint",
         derived["disc_l4_l5_above_HA_mm"],
         "Disc spaces and endplates across L4-S1",
         "NEEDS_ADDITIONAL_RANGES",
         "Requires contiguous coverage through at least the L4, L5 and S1 bodies; a003 disc markers are low confidence."),
    ]
    return [{"skeleton_quantity": n, "skeleton_value_mm_or_deg": v, "ct_observation_required": o,
             "pinned_windows_suffice": s, "why": w,
             "ct_value": None, "comparison_status": "NOT_COMPUTABLE_CT_UNVERIFIED"}
            for n, v, o, s, w in rows]


def build_report(root=REPO_ROOT, register_path=None):
    docs, hashes = load_inputs(root)
    a, c = docs["a003"], docs["c004"]
    diff = pelvic_set_differences(a, c)
    derived_a, derived_c = derive(a), derive(c)
    rep = {
        "schema_version": 1,
        "kind": "SKELETON_VERSUS_SOURCE_CT_INSPECTION_NO_CT_COMPARISON_POSSIBLE_YET",
        "inputs_sha256": hashes,
        "statements": STATEMENTS,
        "freeze_readiness_overall": docs["freeze_readiness"]["overall_status"],
        "skeleton": {
            "set": {"bones": list(BONES), "markers": list(MARKERS)},
            "a003": extract_pelvic_set(a),
            "c004_pelvic_set_differences_from_a003": diff,
            "c004_pelvic_set_identical_to_a003": not diff,
            "c004_bones_differing_elsewhere": sum(1 for k in a["bones"] if a["bones"][k] != c["bones"][k]),
            "bone_confidence": {k: a["bones"][k]["confidence"] for k in BONES},
        },
        "derived_a003": derived_a,
        "derived_c004_equals_a003": derived_a == derived_c,
        "corridor_checks_diagnostic_only": corridor_checks(docs, derived_a),
        "s1_a003_vs_P1": s1_p1_comparison(docs, derived_a),
        "ct_testability": ct_testability(derived_a, docs),
        "ct_side": {"landmarks_VERIFIED": 0, "landmarks_CANDIDATE": 0,
                    "landmarks_UNVERIFIED": None, "image_review_performed": False},
    }
    if register_path is not None and Path(register_path).exists():
        reg = json.loads(Path(register_path).read_text())
        counts = {"VERIFIED": 0, "CANDIDATE": 0, "UNVERIFIED": 0}
        for lm in reg["landmarks"]:
            counts[lm["status"]] += 1
        rep["ct_side"] = {"landmarks_VERIFIED": counts["VERIFIED"],
                          "landmarks_CANDIDATE": counts["CANDIDATE"],
                          "landmarks_UNVERIFIED": counts["UNVERIFIED"],
                          "image_review_performed": reg.get("image_review_performed", False),
                          "register_sha256": sha256_file(register_path)}
    return rep


def _f(x, nd=2):
    return "n/a" if x is None else f"{x:.{nd}f}"


def render_markdown(rep):
    d = rep["derived_a003"]
    p = rep["s1_a003_vs_P1"]
    L = ["# Skeleton versus source: pelvis / S1 / L4-L5 / acetabula / hip centres", "",
         "Generated by `scripts/anatomy_fit/ct_pelvis_skeleton_vs_source_report.py` from repository "
         "records only. Read-only; no geometry is changed.", ""]
    L += [f"- {s}" for s in rep["statements"]]
    L += ["", f"Canonical readiness (unchanged): `{rep['freeze_readiness_overall']}`.", "",
          "## c004 versus a003 in this region", "",
          f"c004 pelvic/lumbar/hip set identical to a003: **{rep['skeleton']['c004_pelvic_set_identical_to_a003']}**"
          f" (differences: {rep['skeleton']['c004_pelvic_set_differences_from_a003'] or 'none'}). "
          f"c004 differs from a003 in {rep['skeleton']['c004_bones_differing_elsewhere']} other bones "
          "(ribs, sternum, arms), none in this region.", "",
          "## Recomputed skeleton quantities (a003; identical in c004)", "",
          "| Quantity | Value |", "|---|---:|",
          f"| Inter-HJC distance | {_f(d['inter_HJC_mm'])} mm |",
          f"| HJC mirror error | {_f(d['HJC_mirror_error_mm'], 6)} mm |",
          f"| Sacrum stick length | {_f(d['sacrum_length_mm'])} mm |",
          f"| HJC midpoint to S1 (sacrum tail) | {_f(d['HA_to_S1_via_sacrum_tail']['distance_mm'])} mm, "
          f"{_f(d['HA_to_S1_via_sacrum_tail']['posterior_tilt_from_vertical_deg'], 1)} deg posterior of vertical |",
          f"| HJC midpoint to L5/S1 disc marker | {_f(d['HA_to_S1_via_disc_l5_sacrum']['distance_mm'])} mm, "
          f"{_f(d['HA_to_S1_via_disc_l5_sacrum']['posterior_tilt_from_vertical_deg'], 1)} deg |",
          f"| HJC midpoint to pubic symphysis | {_f(d['HA_to_pubic_symphysis']['distance_mm'])} mm |",
          f"| L4/L5 disc above HJC midpoint | {_f(d['disc_l4_l5_above_HA_mm'])} mm |",
          f"| L5/S1 disc above HJC midpoint | {_f(d['disc_l5_sacrum_above_HA_mm'])} mm |",
          f"| L5 bone vector length / tilt | {_f(d['l5_bone_vector']['length_mm'])} mm / "
          f"{_f(d['l5_bone_vector']['posterior_tilt_from_vertical_deg'], 1)} deg |",
          f"| L4 bone vector length / tilt | {_f(d['l4_bone_vector']['length_mm'])} mm / "
          f"{_f(d['l4_bone_vector']['posterior_tilt_from_vertical_deg'], 1)} deg |", "",
          "## Corridor diagnostics (sourced summaries already in the repo)", "",
          "| Quantity | Skeleton | Source mean ± SD | z |", "|---|---:|---:|---:|"]
    for r in rep["corridor_checks_diagnostic_only"]:
        L.append(f"| {r['quantity']} | {_f(r['skeleton_mm'])} mm | "
                 f"{_f(r['source_mean_mm'], 1)} ± {_f(r['source_sd_mm'], 1)} mm | {_f(r['z'])} |")
    L += ["", "## a003 S1 stick versus the provisional P1 S1 frame", "",
          f"- P1: {_f(p['P1_distance_HA_to_S1_mm'], 1)} mm at {_f(p['P1_posterior_tilt_from_vertical_deg'], 1)} deg.",
          f"- a003 (sacrum tail): {_f(p['a003_distance_via_sacrum_tail_mm'])} mm at "
          f"{_f(p['a003_tilt_via_sacrum_tail_deg'], 1)} deg; difference "
          f"{_f(p['distance_difference_a003_minus_P1_mm'])} mm and {_f(p['tilt_difference_a003_minus_P1_deg'], 1)} deg.",
          f"- {p['posture_note']}", f"- {p['definitions_differ_note']}", "",
          "## What CT could test, and whether the two 9 mm windows can", "",
          "| Skeleton quantity | Needs | Pinned windows suffice? |", "|---|---|---|"]
    for r in rep["ct_testability"]:
        L.append(f"| {r['skeleton_quantity']} | {r['ct_observation_required']} | `{r['pinned_windows_suffice']}` |")
    ct = rep["ct_side"]
    L += ["", "## CT side status", "",
          f"VERIFIED {ct['landmarks_VERIFIED']} / CANDIDATE {ct['landmarks_CANDIDATE']} / "
          f"UNVERIFIED {ct['landmarks_UNVERIFIED']}; image review performed: {ct['image_review_performed']}. "
          "Every comparison row is `NOT_COMPUTABLE_CT_UNVERIFIED`.", ""]
    return "\n".join(L)


def write_create_only(path, text):
    with open(path, "x", encoding="utf-8") as f:
        f.write(text)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    p.add_argument("--register", type=Path)
    p.add_argument("--out-json", type=Path)
    p.add_argument("--out-md", type=Path)
    p.add_argument("--check", action="store_true",
                   help="fail if --out-json/--out-md differ from a fresh regeneration")
    a = p.parse_args(argv)
    rep = build_report(a.repo_root, a.register)
    js = json.dumps(rep, indent=2, sort_keys=True) + "\n"
    md = render_markdown(rep) + "\n"
    if a.check:
        for path, text in ((a.out_json, js), (a.out_md, md)):
            if path is None or not Path(path).exists() or Path(path).read_text() != text:
                print(f"DRIFT: {path} differs from regenerated report", file=sys.stderr)
                return 1
        print("report matches regeneration")
        return 0
    if a.out_json:
        write_create_only(a.out_json, js)
    if a.out_md:
        write_create_only(a.out_md, md)
    if not (a.out_json or a.out_md):
        print(js)
    return 0


if __name__ == "__main__":
    sys.exit(main())
