#!/usr/bin/env python3
"""CT landmark candidate register: schema, blank template and fail-closed validator.

Status vocabulary (nothing else is accepted):
  UNVERIFIED  no image observation recorded.  observation must be null, confidence NONE.
  CANDIDATE   one reviewer recorded a point on a pinned frame, with every provenance field,
              and checked every rejection condition (none triggered).
  VERIFIED    a CANDIDATE that additionally has support on >= 2 contiguous frames of the same
              window, an independent second reviewer who agrees, and confidence MODERATE/HIGH.

Even VERIFIED never promotes anything canonical, applies a scanner -> skeleton transform or
recommends a skeleton change; those flags stay false here by construction.

CLI:
  init      write a blank register (create-only)
  validate  validate a register against the pinned manifest (optionally recompute geometry
            from private headers with --ct-dir)
  observe   print a complete observation block for a reviewed (row, col); a human pastes it in
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ct_pelvis_window_geometry as geo  # noqa: E402

STATUSES = ("VERIFIED", "CANDIDATE", "UNVERIFIED")
CLASSES = ("iliac_blade", "sacrum", "acetabulum", "femoral_head", "pubic_region", "other")
CONFIDENCE = ("NONE", "LOW", "MODERATE", "HIGH")
OBS_REQUIRED = ("source_id", "png_filename", "png_sha256", "header_sha256", "row", "col",
                "pixel_origin_convention", "scanner_RAS_candidate_mm", "uncertainty_envelope",
                "slice_thickness_mm", "window_stored_low", "window_stored_high", "reviewer",
                "review_date", "laterality_cue", "atlas_crosscheck", "rejection_conditions_checked")
LANDMARK_REQUIRED = ("id", "name", "structure_class", "side", "status", "observation",
                     "anatomical_citations", "confidence", "rejection_conditions",
                     "required_to_promote", "what_would_be_labelled", "coverage_needed_for_3d_surface")
FORBIDDEN_TRUE = ("canonical_promotion_allowed", "skeleton_change_recommended",
                  "HomeGymPT_world_transform_applied", "scanner_to_skeleton_registration_verified")

CITATIONS = {
    "ARAND_2019": {"citation": "Arand C et al. 3D statistical model of the pelvic ring - a CT-based statistical evaluation of anatomical variation. J Anat. 2019;234:376-383.",
                   "pmid": "30575034", "pmcid": "PMC6365482", "vetted_in_repo": "canonical_pelvis_landmark_targets_v1.json",
                   "use": "male 3D-CT pelvic ring: inter-ASIS, promontory-to-symphysis, inter-ischial-spine"},
    "MUSIELAK_2019": {"citation": "Musielak B et al. Variation in pelvic shape and size in Eastern European males: a computed tomography comparative study. PeerJ. 2019;7:e6433.",
                      "pmid": "30809442", "pmcid": "PMC6387581", "vetted_in_repo": "canonical_pelvis_landmark_targets_v1.json",
                      "use": "contemporary male 3D-CT: inter-ASIS, intercristal, pelvic height, iliac angles"},
    "TANNENBAUM_2011": {"citation": "Multilevel Measurement of Acetabular Version Using 3-D CT-generated Models: Implications for Hip Preservation Surgery. Clin Orthop Relat Res. 2011.",
                        "pmcid": "PMC3018214", "vetted_in_repo": "canonical_pelvis_landmark_targets_v1.json",
                        "use": "male acetabular cup diameter, interacetabular distance, inter-ASIS"},
    "GRAS_2015": {"citation": "Sex-specific Differences of the Infraacetabular Corridor: A Biomorphometric CT-based Analysis on a Database of 523 Pelves. 2015.",
                  "pmcid": "PMC4390952", "vetted_in_repo": "canonical_pelvis_landmark_targets_v1.json",
                  "use": "large-sample male acetabular diameter corridor"},
    "HASEGAWA_2017": {"citation": "Hasegawa K et al. Standing sagittal alignment of the whole axial skeleton with reference to the gravity line in humans. J Anat. 2017.",
                      "vetted_in_repo": "canonical_proportion_sources_v1.json",
                      "use": "male pelvic incidence 50.1 +/- 11.2 deg, pelvic thickness 107 +/- 8 mm (standing cohort)"},
    "SP_PELVIC_JOINTS": {"citation": "StatPearls: Pelvic Joints.", "url": "https://www.ncbi.nlm.nih.gov/sites/books/NBK538523/",
                         "vetted_in_repo": "anatomy_sources.json (SP_PELVIS, checked 2026-10-07)",
                         "use": "general pelvic joint/sacroiliac and pubic symphysis anatomy"},
    "PELVIC_JOINTS_REVIEW_1991": {"citation": "Anatomy of the pelvic joints: a review.", "url": "https://pubmed.ncbi.nlm.nih.gov/2011709/",
                                  "vetted_in_repo": "anatomy_sources.json (PELVIC_ANATOMY, checked 2026-10-07)",
                                  "use": "general pelvic joint anatomy"},
    "NLM_VISIBLE_HUMAN_NORMAL_CT": {"citation": "US National Library of Medicine Visible Human Male original normalCT PNG and header indexes.",
                                    "url": "https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Male-Images/PNG_format/radiological/normalCT/index.html",
                                    "vetted_in_repo": "docs/CLAUDE_BLENDER_PELVIS_CT_LAPTOP_HANDOFF_20261009.md (PR #15)",
                                    "use": "source custodian only; not an anatomy definition"},
    "ATLAS_FIGURE_REVIEWER_SUPPLIED": {"citation": "A qualified labelled axial pelvic CT atlas figure chosen by the reviewer; record title, edition/URL and figure number in atlas_crosscheck.",
                                       "vetted_in_repo": None,
                                       "use": "REQUIRED for any CANDIDATE or VERIFIED; no atlas page could be opened in the cloud session (reCAPTCHA/permission gates), so none is pre-filled"},
}
_PELVIC_RING = ["ARAND_2019", "MUSIELAK_2019", "TANNENBAUM_2011", "SP_PELVIC_JOINTS", "ATLAS_FIGURE_REVIEWER_SUPPLIED"]

_COMMON_LATERALITY = ("R0: laterality cue absent, or the cue (a recognisable right/left-asymmetric organ or "
                      "marker) contradicts the side recorded")
_COMMON_WINDOW = ("R1: outline or boundary depends on one display window; it must remain stable across at "
                  "least two different stored-value windows (stored values are not verified HU)")
_COMMON_FRAMES = ("R2: structure is inconsistent between adjacent 3 mm frames (appears, vanishes or changes "
                  "shape discontinuously) beyond what its anatomy allows")


def _lm(i, name, cls, side, what, extra_rej, cites, coverage, promote_extra=()):
    rej = [_COMMON_LATERALITY, _COMMON_WINDOW, _COMMON_FRAMES] + list(extra_rej)
    return {
        "id": i, "name": name, "structure_class": cls, "side": side, "status": "UNVERIFIED",
        "observation": None, "anatomical_citations": cites, "confidence": "NONE",
        "what_would_be_labelled": what,
        "rejection_conditions": rej,
        "required_to_promote": ["observation block with every field in OBS_REQUIRED",
                                "atlas figure cross-check recorded in atlas_crosscheck",
                                "every rejection condition checked and none triggered"] + list(promote_extra),
        "coverage_needed_for_3d_surface": coverage,
    }


def build_blank_register(manifest_path, manifest_sha256, created):
    lms = [
        _lm("ILIAC_BLADE_L", "Left iliac blade (ala) cross-section", "iliac_blade", "L",
            "Curved plate of cortical-bounded cancellous bone lateral to the sacrum in axial section",
            ["R3: not mirrored by a comparable plate on the contralateral side within 15 mm in scanner S, "
             "unless the pelvis is clearly asymmetric (record why)"],
            _PELVIC_RING, "Contiguous 3 mm run from the iliac crest to the acetabular roof (pelvic height 152 +/- 17 mm, "
            "range 99-185 mm in Musielak 2019): about 35-65 frames."),
        _lm("ILIAC_BLADE_R", "Right iliac blade (ala) cross-section", "iliac_blade", "R",
            "As ILIAC_BLADE_L on the opposite side",
            ["R3: not mirrored by a comparable plate on the contralateral side within 15 mm in scanner S"],
            _PELVIC_RING, "As ILIAC_BLADE_L."),
        _lm("ASIS_L", "Left anterior superior iliac spine (bony point)", "iliac_blade", "L",
            "Anterior end of the iliac crest in axial section; a bony point, not a skin or groove proxy",
            ["R4: bilateral ASIS separation outside 190-310 mm (review trigger: sourced male ranges 205.5-295.9 mm "
             "widened for donor variation; escalate, do not auto-reject)",
             "R5: the point lies on skin or soft tissue rather than on bone cortex"],
            _PELVIC_RING, "A few frames around the ASIS level on each side; the iliac crest run above also locates it."),
        _lm("ASIS_R", "Right anterior superior iliac spine (bony point)", "iliac_blade", "R",
            "As ASIS_L on the opposite side",
            ["R4: bilateral ASIS separation outside 190-310 mm (review trigger)",
             "R5: the point lies on skin or soft tissue rather than on bone cortex"],
            _PELVIC_RING, "As ASIS_L."),
        _lm("SACRUM_ALA_BODY", "Sacral body and ala with sacroiliac joints", "sacrum", "midline",
            "Midline posterior bone mass flanked by the sacroiliac joints, in axial section",
            ["R6: midline structure is not bisected by the sacroiliac pair symmetrically (asymmetry > 15 mm in "
             "scanner R between left and right joint centres relative to the midline: escalate)"],
            _PELVIC_RING + ["HASEGAWA_2017"],
            "Contiguous run from the L5/S1 disc to the sacral apex: sacral length 107.6 +/- 10 mm in the repo's source "
            "record, about 35-40 frames."),
        _lm("S1_PROMONTORY", "S1 promontory / superior endplate anterior margin", "sacrum", "midline",
            "Anterior-superior margin of the S1 body at the L5/S1 junction",
            ["R7: promontory-to-symphysis 3D distance outside 70-150 mm once the symphysis is recorded "
             "(sourced male mean 107.3 mm, SD about 12; trigger is wide on purpose; escalate)",
             "R8: the endplate orientation cannot be established because the S1 body is not covered by at least "
             "10 contiguous frames"],
            _PELVIC_RING + ["HASEGAWA_2017"],
            "At least a contiguous run through the L5/S1 disc and S1 body (about 12-20 frames) plus a sagittal reformat.",
            ["sagittal reformat across the endplate (needs contiguous coverage; not possible from two 9 mm windows)"]),
        _lm("ACETABULUM_L", "Left acetabulum (cup rim on its equatorial axial slice)", "acetabulum", "L",
            "Cup-shaped articular socket receiving the femoral head; label the rim and cup on a slice through its equator",
            ["R9: circle-fit diameter outside 40-65 mm (review trigger around the repo-sourced 47-59 mm acetabular corridor, "
             "Tannenbaum 51.1 +/- 2.5, Gras 53 [47-59]; widened for CT edge blur; escalate)",
             "R10: fitted radius changes by more than 5% on either neighbouring 3 mm frame, so the section is not "
             "equatorial; do not fit a centre z from it"],
            _PELVIC_RING + ["GRAS_2015"],
            "About 18-20 contiguous 3 mm frames per cup (about 53 mm), plus the lunate surface and the acetabular fossa."),
        _lm("ACETABULUM_R", "Right acetabulum (cup rim on its equatorial axial slice)", "acetabulum", "R",
            "As ACETABULUM_L on the opposite side",
            ["R9: circle-fit diameter outside 40-65 mm (review trigger)",
             "R10: fitted radius changes by more than 5% on a neighbouring 3 mm frame"],
            _PELVIC_RING + ["GRAS_2015"], "As ACETABULUM_L."),
        _lm("FEMORAL_HEAD_L", "Left femoral head (centre on an equatorial axial slice)", "femoral_head", "L",
            "Spherical articular head seated in the acetabulum; the in-plane circle centre on an equatorial slice",
            ["R11: circle-fit diameter outside 40-65 mm (review trigger)",
             "R12: the fitted centre lies outside the same side's acetabular cup outline",
             "R13: both heads claimed but their in-plane centre separation is outside 140-200 mm "
             "(Tannenbaum male interacetabular 169.3 +/- 7.8 mm, range 154-183; widened; escalate)",
             "R10: fitted radius changes by more than 5% on a neighbouring 3 mm frame (non-equatorial section)"],
            _PELVIC_RING + ["GRAS_2015"],
            "About 16-18 contiguous 3 mm frames per head to fit a sphere centre in z; one equatorial frame gives only an in-plane centre."),
        _lm("FEMORAL_HEAD_R", "Right femoral head (centre on an equatorial axial slice)", "femoral_head", "R",
            "As FEMORAL_HEAD_L on the opposite side",
            ["R11: circle-fit diameter outside 40-65 mm (review trigger)",
             "R12: the fitted centre lies outside the same side's acetabular cup outline",
             "R13: head separation outside 140-200 mm (review trigger)",
             "R10: fitted radius changes by more than 5% on a neighbouring 3 mm frame"],
            _PELVIC_RING + ["GRAS_2015"], "As FEMORAL_HEAD_L."),
        _lm("PUBIC_TUBERCLE_L", "Left pubic tubercle", "pubic_region", "L",
            "Small anterior bony prominence on the superior pubic ramus near the symphysis",
            ["R14: not mirrored on the contralateral side within 10 mm in scanner S (escalate)"],
            _PELVIC_RING, "A few frames at the tubercle level; the pubic rami and symphysis require their own contiguous run."),
        _lm("PUBIC_TUBERCLE_R", "Right pubic tubercle", "pubic_region", "R",
            "As PUBIC_TUBERCLE_L on the opposite side",
            ["R14: not mirrored on the contralateral side within 10 mm in scanner S (escalate)"],
            _PELVIC_RING, "As PUBIC_TUBERCLE_L."),
        _lm("PUBIC_SYMPHYSIS", "Pubic symphysis (midline cartilaginous joint)", "pubic_region", "midline",
            "Midline fibrocartilaginous joint between the pubic bodies; a contact, not a merged bone",
            ["R15: the two pubic bodies are fused or not separated by a joint space in a way that contradicts a "
             "symphysis (record the appearance; escalate)"],
            _PELVIC_RING + ["PELVIC_JOINTS_REVIEW_1991"],
            "Contiguous run through the symphysis (about 10-14 frames) bridging to the ischiopubic rami."),
    ]
    return {
        "schema_version": 1,
        "kind": "CT_LANDMARK_CANDIDATE_REGISTER",
        "created": created,
        "status_vocabulary": {
            "UNVERIFIED": "no image observation; observation null; confidence NONE",
            "CANDIDATE": "one reviewer, full provenance block, every rejection condition checked and none triggered",
            "VERIFIED": "CANDIDATE plus >= 2 contiguous supporting frames, independent second reviewer who agrees, confidence MODERATE or HIGH",
        },
        "review_state": "NO_IMAGE_REVIEW_PERFORMED: the original NLM files were unreachable from the cloud session (egress 403)",
        "image_review_performed": False,
        "pinned_manifest": {"path": manifest_path, "sha256": manifest_sha256,
                            "pins_reproduced_in_claude_session": False},
        "hard_constraints": [
            "Source skeleton governs geometry; this register never moves or reshapes it.",
            "No c005; c004 unchanged; canonical readiness unchanged.",
            "The donor is one cadaver, not a canonical 182 cm male.",
            "Scanner RAS is not the Home Gym PT world frame; no transform applied.",
            "Stored PNG values are not verified Hounsfield units; no density threshold is a bone definition.",
            "3 mm slices are not sub-millimetre surfaces; coordinates carry the conservative envelope.",
            "Image laterality must be established from an anatomical cue, never from the header or file order.",
        ],
        "canonical_promotion_allowed": False,
        "skeleton_change_recommended": False,
        "HomeGymPT_world_transform_applied": False,
        "scanner_to_skeleton_registration_verified": False,
        "citations": CITATIONS,
        "landmarks": lms,
    }


class RegisterError(ValueError):
    pass


def _need(cond, msg):
    if not cond:
        raise RegisterError(msg)


def _is_date(s):
    try:
        datetime.date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


def _check_observation(lm, obs, pins, geoms, status):
    lid = lm["id"]
    for k in OBS_REQUIRED:
        _need(k in obs and obs[k] not in (None, "", []), f"{lid}: observation missing {k}")
    sid = obs["source_id"]
    _need(sid in pins, f"{lid}: source_id is not one of the six pinned frames")
    pin = pins[sid]
    _need(obs["png_filename"] == geo.frame_name(sid, "png"), f"{lid}: png_filename does not match source_id")
    _need(obs["png_sha256"] == pin["png_sha256"], f"{lid}: png_sha256 differs from the pin")
    _need(obs["header_sha256"] == pin["scanner_header_sha256"], f"{lid}: header_sha256 differs from the pin")
    _need(type(obs["row"]) is int and type(obs["col"]) is int
          and 0 <= obs["row"] < geo.GRID and 0 <= obs["col"] < geo.GRID, f"{lid}: row/col must be integers 0..511")
    _need(obs["pixel_origin_convention"] in geo.CONVENTIONS, f"{lid}: unknown pixel-origin convention")
    ras = obs["scanner_RAS_candidate_mm"]
    _need(isinstance(ras, list) and len(ras) == 3 and all(type(v) in (int, float) for v in ras),
          f"{lid}: scanner_RAS_candidate_mm must be three numbers")
    _need(abs(ras[2] - pin["scanner_S_mm"]) < 1e-6, f"{lid}: candidate S differs from the pinned slice S")
    env = obs["uncertainty_envelope"]
    s = pin["scanner_S_mm"]
    _need(env.get("scanner_S_range_mm") == [s - 1.5, s + 1.5], f"{lid}: envelope must carry the 3 mm slab S range")
    _need(isinstance(env.get("in_plane_half_width_mm"), (int, float))
          and env["in_plane_half_width_mm"] >= geo.EXPECTED_PIXEL_SPACING_MM - 1e-9,
          f"{lid}: in-plane envelope narrower than convention+cell (one pixel)")
    _need(obs["slice_thickness_mm"] == geo.EXPECTED_THICKNESS_MM, f"{lid}: slice thickness must be 3 mm")
    _need(isinstance(obs["reviewer"], str) and obs["reviewer"].strip(), f"{lid}: reviewer required")
    _need(_is_date(obs["review_date"]), f"{lid}: review_date must be ISO yyyy-mm-dd")
    _need(isinstance(obs["laterality_cue"], str) and obs["laterality_cue"].strip(), f"{lid}: laterality_cue required")
    cross = obs["atlas_crosscheck"]
    _need(isinstance(cross, list) and all(isinstance(c, dict) and c.get("source") and c.get("figure") for c in cross),
          f"{lid}: atlas_crosscheck needs {{source, figure}} entries")
    ids = {c.split(":")[0] for c in lm["rejection_conditions"]}
    checked = obs["rejection_conditions_checked"]
    _need(isinstance(checked, dict) and set(checked) == ids, f"{lid}: every rejection condition must be checked")
    _need(all(v == "not_triggered" for v in checked.values()), f"{lid}: a triggered rejection condition forbids {status}")
    if geoms is not None:
        placed = geo.pixel_to_scanner_ras(geoms[sid], obs["row"], obs["col"], obs["pixel_origin_convention"],
                                          env.get("picking_allowance_px", 2.0))
        _need(all(abs(a - b) < 1e-6 for a, b in zip(placed["candidate_centre_RAS_mm"], ras)),
              f"{lid}: scanner RAS does not match the header-derived placement")
        _need(abs(placed["uncertainty_envelope"]["in_plane_half_width_mm"] - env["in_plane_half_width_mm"]) < 1e-6,
              f"{lid}: envelope does not match the header-derived envelope")


def validate_register(reg, manifest, geoms=None):
    """Raise RegisterError on any violation.  `manifest` is geo.load_pinned_manifest output."""
    pins = manifest["by_id"] if "by_id" in manifest else manifest
    _need(reg.get("schema_version") == 1 and reg.get("kind") == "CT_LANDMARK_CANDIDATE_REGISTER",
          "unexpected register schema/kind")
    for flag in FORBIDDEN_TRUE:
        _need(reg.get(flag) is False, f"register must keep {flag} false")
    cite_ids = set(reg.get("citations", {}))
    lms = reg.get("landmarks", [])
    _need(isinstance(lms, list) and lms, "no landmarks")
    seen = set()
    any_observed = False
    for lm in lms:
        for k in LANDMARK_REQUIRED:
            _need(k in lm, f"{lm.get('id', '?')}: missing field {k}")
        lid = lm["id"]
        _need(lid not in seen, f"duplicate landmark id {lid}")
        seen.add(lid)
        _need(lm["status"] in STATUSES, f"{lid}: status must be one of {STATUSES}")
        _need(lm["structure_class"] in CLASSES, f"{lid}: unknown structure_class")
        _need(lm["confidence"] in CONFIDENCE, f"{lid}: unknown confidence")
        _need(lm["anatomical_citations"] and set(lm["anatomical_citations"]) <= cite_ids,
              f"{lid}: anatomical_citations must be non-empty and defined in citations")
        _need(isinstance(lm["rejection_conditions"], list) and len(lm["rejection_conditions"]) >= 3
              and all(c[:1] == "R" and ":" in c for c in lm["rejection_conditions"]),
              f"{lid}: rejection conditions must be listed as 'R<n>: ...'")
        _need(len({c.split(":")[0] for c in lm["rejection_conditions"]}) == len(lm["rejection_conditions"]),
              f"{lid}: duplicate rejection condition ids")
        _need(lm["required_to_promote"], f"{lid}: required_to_promote must be stated")
        if lm["status"] == "UNVERIFIED":
            _need(lm["observation"] is None, f"{lid}: UNVERIFIED must have a null observation")
            _need(lm["confidence"] == "NONE", f"{lid}: UNVERIFIED must have confidence NONE")
            continue
        any_observed = True
        _need(isinstance(lm["observation"], dict), f"{lid}: {lm['status']} requires an observation block")
        _need(lm["confidence"] != "NONE", f"{lid}: {lm['status']} cannot have confidence NONE")
        _check_observation(lm, lm["observation"], pins, geoms, lm["status"])
        if lm["status"] == "VERIFIED":
            _need(lm["confidence"] in ("MODERATE", "HIGH"), f"{lid}: VERIFIED needs MODERATE or HIGH confidence")
            sup = lm.get("supporting_frames")
            _need(isinstance(sup, list) and len(sup) >= 2, f"{lid}: VERIFIED needs >= 2 supporting frames")
            window = next(t for t in geo.TRIPLETS if lm["observation"]["source_id"] in t)
            ids = [x.get("source_id") for x in sup]
            _need(len(set(ids)) == len(ids) and set(ids) <= set(window) and lm["observation"]["source_id"] in ids,
                  f"{lid}: supporting frames must be distinct frames of the observation's own window")
            _need(all(x.get("consistent") is True for x in sup), f"{lid}: every supporting frame must be consistent")
            second = lm.get("independent_second_review")
            _need(isinstance(second, dict) and second.get("agrees") is True
                  and isinstance(second.get("reviewer"), str) and second["reviewer"].strip()
                  and second["reviewer"] != lm["observation"]["reviewer"] and _is_date(second.get("review_date")),
                  f"{lid}: VERIFIED needs an agreeing, different second reviewer with a date")
    if reg.get("image_review_performed") is not True:
        _need(not any_observed, "observations exist but image_review_performed is not true")
    return True


def build_observation(geom, pin, row, col, convention, picking_px, reviewer, review_date,
                      laterality_cue, atlas_crosscheck, rejection_ids, window_low, window_high):
    """Complete observation block for a reviewed pixel; the reviewer pastes it into the register."""
    placed = geo.pixel_to_scanner_ras(geom, row, col, convention, picking_px)
    sid = pin["source_id"]
    env = placed["uncertainty_envelope"]
    return {
        "source_id": sid, "png_filename": geo.frame_name(sid, "png"),
        "png_sha256": pin["png_sha256"], "header_sha256": pin["scanner_header_sha256"],
        "row": row, "col": col, "pixel_origin_convention": convention,
        "scanner_RAS_candidate_mm": placed["candidate_centre_RAS_mm"],
        "uncertainty_envelope": {"in_plane_half_width_mm": env["in_plane_half_width_mm"],
                                 "picking_allowance_px": picking_px,
                                 "scanner_S_range_mm": env["scanner_S_range_mm"],
                                 "kind": env["kind"]},
        "slice_thickness_mm": geom["slice_thickness_mm"],
        "window_stored_low": window_low, "window_stored_high": window_high,
        "reviewer": reviewer, "review_date": review_date, "laterality_cue": laterality_cue,
        "atlas_crosscheck": atlas_crosscheck,
        "rejection_conditions_checked": {r: "not_triggered" for r in rejection_ids},
    }


def _cli(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("--manifest", type=Path, required=True)
    i.add_argument("--out", type=Path, required=True)
    i.add_argument("--created", default=datetime.date.today().isoformat())
    v = sub.add_parser("validate")
    v.add_argument("--register", type=Path, required=True)
    v.add_argument("--manifest", type=Path, required=True)
    v.add_argument("--ct-dir", type=Path, help="recompute geometry from private headers")
    o = sub.add_parser("observe")
    o.add_argument("--manifest", type=Path, required=True)
    o.add_argument("--ct-dir", type=Path, required=True)
    o.add_argument("--source-id", type=int, required=True, choices=geo.ALL_IDS)
    o.add_argument("--row", type=int, required=True)
    o.add_argument("--col", type=int, required=True)
    o.add_argument("--convention", choices=geo.CONVENTIONS, default="outer_edge")
    o.add_argument("--picking-px", type=float, default=2.0)
    o.add_argument("--reviewer", required=True)
    o.add_argument("--review-date", default=datetime.date.today().isoformat())
    o.add_argument("--laterality-cue", required=True)
    o.add_argument("--atlas-source", required=True)
    o.add_argument("--atlas-figure", required=True)
    o.add_argument("--rejection-ids", nargs="+", required=True)
    o.add_argument("--window-low", type=int, required=True)
    o.add_argument("--window-high", type=int, required=True)
    a = p.parse_args(argv)
    manifest = geo.load_pinned_manifest(a.manifest)
    if a.cmd == "init":
        text = json.dumps(build_blank_register(
            str(a.manifest), geo.sha256_regular_file(a.manifest, 1 << 20)[0], a.created),
            indent=2, sort_keys=False) + "\n"
        with open(a.out, "x", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {a.out}")
        return 0
    if a.cmd == "validate":
        reg = json.loads(a.register.read_text())
        geoms = None
        if a.ct_dir:
            geo.validate_private_inputs(a.ct_dir, manifest)
            geoms = {sid: geo.parse_scanner_header((Path(a.ct_dir) / geo.frame_name(sid, "txt")).read_bytes())
                     for sid in geo.ALL_IDS}
        validate_register(reg, manifest, geoms)
        counts = {s: sum(1 for x in reg["landmarks"] if x["status"] == s) for s in STATUSES}
        print(json.dumps({"register_valid": True, "status_counts": counts,
                          "geometry_recomputed_from_private_headers": geoms is not None}))
        return 0
    geo.validate_private_inputs(a.ct_dir, manifest)
    geom = geo.parse_scanner_header((Path(a.ct_dir) / geo.frame_name(a.source_id, "txt")).read_bytes())
    obs = build_observation(geom, {**manifest["by_id"][a.source_id], "source_id": a.source_id}, a.row, a.col,
                            a.convention, a.picking_px, a.reviewer, a.review_date, a.laterality_cue,
                            [{"source": a.atlas_source, "figure": a.atlas_figure}], a.rejection_ids,
                            a.window_low, a.window_high)
    print(json.dumps(obs, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
