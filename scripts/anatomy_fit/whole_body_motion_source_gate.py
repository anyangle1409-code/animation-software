#!/usr/bin/env python3
"""Whole-body pose amplitude provenance gate: source-traceability != human ROM.

Checks *all* 135 source isolated tests and their 278 amplitude peaks against
the original movement atlas + author-specified diagnostic basis. Exactly 78
peaks in 49 tests are explicit UNSOURCED TEST AMPLITUDE, and MUST NOT be
certified as safe/anatomical merely because Blender renders the motion.

Optional intake of a REAL bpy Blender report requires the existing strict
206-bone/427-joint measured-scene gate and the precise private .blend SHA.
This is read-only, emits NEW private JSON and changes no rig, mesh or limits.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from whole_body_blender_evidence_gate import (
    REPO, private_review_output, read_source_and_audit, verify_scene_bytes,
)

ANATOMY=REPO/"ORIGINAL_V1_WORK"/"anatomy"
RECORD=ANATOMY/"character_fit_r95_a003.json"
ATLAS=ANATOMY/"whole_body_movement_atlas.json"
SOURCE_QUEUE=ANATOMY/"audit/work_evidence_queue_20261009/unsupported_movement_peaks.json"
ARCHIVE=ANATOMY/"audit/amplitude_provenance/a003_isolated_014.json"
ISOLATED_SCRIPT=REPO/"scripts/anatomy_fit/isolated_tests.py"
AUDITED_KINDS={
    "EXACT_CONTEXT","STATED_IN_BASIS","HALF_OF_SOURCED_TOTAL",
    "CONDITION_IN_TEST_ID","TARGET_MINUS_FITTED_REST",
    "DRIVEN_TO_MEASURED_TARGET","LABELLED_TEST_AMPLITUDE",
}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evidence_context(record,atlas,original_queue,record_hash,atlas_hash,
                     archived_audit=None,script_hash=None):
    """Cross-verify original independent, SHA-anchored source audit ledgers.

    NumPy-dependent old pose-generator is NOT imported or executed here.
    Its separately committed amplitude-provenance evidence is SHA-pinned to
    the original generator, source character/atlas and original pose samples.
    This standard-library-only guard reconciles every audited peak with the
    independently authored unsupported-movement ledger, failing on drift.
    """
    if record!=json.loads(RECORD.read_text()) or atlas!=json.loads(ATLAS.read_text()):
        raise ValueError("live a003 record or atlas differs from source-pinned original")
    if record_hash!=digest(RECORD) or atlas_hash!=digest(ATLAS):
        raise ValueError("original record/atlas SHA no longer matches live audited source")
    if archived_audit is None:
        archived_audit=json.loads(ARCHIVE.read_text())
    if script_hash is None:
        script_hash=digest(ISOLATED_SCRIPT)
    previous=archived_audit.get("inputs_sha256",{})
    source_sample=REPO/"ORIGINAL_V1_WORK/anatomy/audit/runs/isolated_bone_only_014/isolated_samples.json"
    source_name=source_sample.relative_to(REPO).as_posix()
    if (archived_audit.get("label")!="a003_isolated_014" or
            archived_audit.get("kind")!="READ_ONLY_PROVENANCE_AUDIT" or
            archived_audit.get("status")!="TRACED" or
            archived_audit.get("tests")!=135 or
            archived_audit.get("peaks")!=278 or
            archived_audit.get("untraced")!=[] or
            previous.get(RECORD.relative_to(REPO).as_posix())!=record_hash or
            previous.get(ATLAS.relative_to(REPO).as_posix())!=atlas_hash or
            previous.get(ISOLATED_SCRIPT.relative_to(REPO).as_posix())!=script_hash or
            previous.get(source_name)!=digest(source_sample)):
        raise ValueError("original source movement provenance inputs changed")
    if (original_queue.get("schema_version")!=1 or
            original_queue.get("kind")!="READ_ONLY_MOVEMENT_EVIDENCE_QUEUE" or
            original_queue.get("anatomical_acceptance") is not False or
            original_queue.get("existing_limits_changed") is not False or
            original_queue.get("record_sha256")!=record_hash or
            original_queue.get("atlas_sha256")!=atlas_hash):
        raise ValueError("source movement queue SHA or nonacceptance invariant changed")
    details=archived_audit.get("detail")
    kinds=archived_audit.get("by_kind")
    if not isinstance(details,dict) or len(details)!=135 or not isinstance(kinds,dict):
        raise ValueError("original source provenance lacks all 135 movement tests")
    by_test={}
    for name,evidence in details.items():
        rows=evidence.get("peaks")
        if not isinstance(rows,list) or any(
                r.get("kind") not in AUDITED_KINDS for r in rows):
            raise ValueError("unknown or untraced original peak")
        by_test[name]=rows
    if sum(len(rows) for rows in by_test.values())!=278 or sum(kinds.values())!=278:
        raise ValueError("source provenance 278 peaks incorrectly classified")
    unsupported=[
        {"test":name,"channel":x["channel"],"peak":x["peak"]}
        for name,rows in by_test.items() for x in rows
        if x["kind"]=="LABELLED_TEST_AMPLITUDE"
    ]
    if len(unsupported)!=78 or kinds.get("LABELLED_TEST_AMPLITUDE")!=78:
        raise ValueError("original 78 unsourced pose peaks no longer recorded")
    raw_rows=original_queue.get("peaks")
    if (not isinstance(raw_rows,list) or original_queue.get("peak_count")!=78 or
            original_queue.get("test_count")!=49 or len(raw_rows)!=78 or
            not isinstance(original_queue.get("by_family"),dict) or
            len(original_queue["by_family"])!=12 or
            sum(original_queue["by_family"].values())!=78):
        raise ValueError("original unsupported-peak queue coverage changed")
    actual=[{"test":r.get("test"),"channel":r.get("channel"),"peak":r.get("peak")} for r in raw_rows]
    def peak_key(row):
        return (row["test"],row["channel"],row["peak"])
    if (len(set(map(peak_key,actual)))!=78 or
            sorted(actual,key=peak_key)!=sorted(unsupported,key=peak_key)):
        raise ValueError("one or more 78 unsourced peaks silently dropped/relabelled")
    family_counts=Counter()
    unsourced={}
    for r in raw_rows:
        if (r.get("status")!="UNSOURCED_TEST_AMPLITUDE" or
                r.get("replacement_authorized_by_this_report") is not False or
                r.get("role") not in ("diagnostic_excursion","conditioning_pose") or
                r.get("units") not in ("deg","m") or
                not isinstance(r.get("blocker"),str) or not r["blocker"] or
                not isinstance(r.get("family"),str) or not r["family"]):
            raise ValueError("unsupported source peak was wrongly approved or classified")
        if r["units"]=="m" and r.get("peak_mm")!=r["peak"]*1000:
            raise ValueError("TMJ source glide metres/millimetres changed")
        unsourced.setdefault(r["test"],[]).append(r)
        family_counts[r["family"]]+=1
    if len(unsourced)!=49 or dict(family_counts)!=original_queue["by_family"]:
        raise ValueError("49 unsourced test IDs or family counts changed")
    return {
        "test_ids":list(by_test),"by_test":by_test,"unsourced":unsourced,
        "by_family":dict(family_counts),
        "original_record_sha256":record_hash,
        "original_atlas_sha256":atlas_hash,
        "archived_generator_sha256":script_hash,
        "archived_pose_samples_sha256":digest(source_sample),
    }


def source_context_from_repo(root=ANATOMY):
    record_path=root/"character_fit_r95_a003.json"
    atlas_path=root/"whole_body_movement_atlas.json"
    queue_path=root/"audit/work_evidence_queue_20261009/unsupported_movement_peaks.json"
    return evidence_context(
        json.loads(record_path.read_text()),
        json.loads(atlas_path.read_text()),
        json.loads(queue_path.read_text()),
        digest(record_path),digest(atlas_path),
    )


def source_only_summary(context):
    rows=[]
    for source_id in context["test_ids"]:
        diagnostic=context["unsourced"].get(source_id,[])
        rows.append({
            "source_isolated_test_id":source_id,
            "source_test_peaks":len(context["by_test"][source_id]),
            "unsourced_peak_count":len(diagnostic),
            "unsourced_peaks":[{
                "channel":x["channel"],"peak":x["peak"],
                "units":x["units"],"family":x["family"],
                "role":x["role"],
            } for x in diagnostic],
            "amplitude_classification":(
                "DIAGNOSTIC_ONLY_UNSOURCED_AMPLITUDES" if diagnostic
                else "TRACEABLE_BASIS_ONLY_NOT_PHYSIOLOGICAL_CERTIFICATION"
            ),
            "actual_Blender_pose_executed":False,
            "human_anatomy_or_safe_ROM_verified":False,
        })
    return {
        "schema_version":1,
        "kind":"HGPT_SOURCE_135_TEST_MOVEMENT_EVIDENCE_GATE_NOT_ROM_APPROVAL",
        "original_source_record_sha256":context["original_record_sha256"],
        "original_movement_atlas_sha256":context["original_atlas_sha256"],
        "source_test_count":len(rows),
        "commanded_peak_count":sum(len(a) for a in context["by_test"].values()),
        "unsourced_test_count":sum(bool(row["unsourced_peak_count"]) for row in rows),
        "unsourced_peak_count":sum(row["unsourced_peak_count"] for row in rows),
        "unverified_peak_count_by_family":context["by_family"],
        "source_tests":rows,
        "real_pose_execution_verified":False,
        "active_passive_or_loaded_ROM_certified":False,
        "whole_body_motion_anatomically_verified":False,
        "canonical_promotion_allowed":False,
    }


def motion_report(raw,context,wholebody_qa):
    """Assess *claimed* source test associations; never certify the measured pose."""
    if not isinstance(raw,dict) or raw.get("kind")!="HGPT_BLENDER_206_BONE_QA_EXPORT":
        raise ValueError("input must be a measured original whole-body bpy QA packet")
    if (raw.get("canonical_promotion_allowed") is not False or
            raw.get("anatomical_identity_approved") is not False):
        raise ValueError("upstream Blender report attempted anatomical promotion")
    if (wholebody_qa.get("production_or_canonical_promotion_allowed") is not False or
            wholebody_qa.get("reported_scene_sha256")!=raw["provenance"]["blender_scene_sha256"]):
        raise ValueError("original whole-body source/scene audit prerequisite missing")
    seen=set()
    rows=[]
    for pose in raw["poses"]:
        key=pose["pose_id"]
        if key in seen:
            raise ValueError("duplicate measured pose association")
        seen.add(key)
        source_id=pose.get("source_isolated_test_id")
        if source_id is not None and (
                not isinstance(source_id,str) or source_id not in context["by_test"]):
            raise ValueError("unrecognized source isolated-test amplitude association")
        bad=context["unsourced"].get(source_id,[]) if source_id is not None else []
        if source_id is None:
            grade="NO_TEST_AMPLITUDE_PROVENANCE"
        elif bad:
            grade="DIAGNOSTIC_ONLY_UNSOURCED_AMPLITUDE"
        else:
            grade="TRACEABLE_BASIS_NOT_ANATOMICAL_ROM_CERTIFICATION"
        # An assertion of a source test identifier is not proof its exact
        # commanded motion was physically applied in this sampled bpy frame.
        if any(pose.get(flag) is True for flag in (
                "physiological_ROM_certified","exercise_anatomy_approved",
                "source_test_execution_independently_proven")):
            raise ValueError("Blender pose report tried to self-certify movement")
        rows.append({
            "pose_id":key,
            "movement_family":pose["movement_family"],
            "reported_source_isolated_test_id":source_id,
            "source_test_link_independently_verified":False,
            "motion_amplitude_grade":grade,
            "unsourced_test_peak_count":len(bad),
            "unsourced_source_peak_channels":sorted({v["channel"] for v in bad}),
            "actual_joint_angles_and_load_match_source_test_verified":False,
            "physiological_ROM_certified":False,
        })
    return {
        "schema_version":1,
        "kind":"HGPT_BLENDER_POSE_AMPLITUDE_G3_REJECTION_GATE",
        "source_test_count":len(context["test_ids"]),
        "source_peak_count":sum(len(v) for v in context["by_test"].values()),
        "all_unsourced_source_test_peaks":78,
        "unsourced_source_test_ids":49,
        "blender_scene_sha256":wholebody_qa["reported_scene_sha256"],
        "reported_git_commit":wholebody_qa["reported_git_commit"],
        "measured_pose_count":len(rows),
        "pose_amplitude_grades":rows,
        "grades":dict(Counter(row["motion_amplitude_grade"] for row in rows)),
        "source_test_ID_is_an_assertion_not_proof":True,
        "no_movement_certified_as_human_ROM":True,
        "skeleton_first_requires_independent_anatomical_sources":True,
        "canonical_promotion_allowed":False,
        "interpretation":"A labelled Blender exercise pose, a past test endpoint or a valid file hash is NOT evidence of physiological range, 3D articular contact or authentic full-body exercise mechanics.",
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-only",action="store_true",help="verify original 135 test evidence without a Blender scene")
    parser.add_argument("--input",help="real private bpy measured report, same as 206/427 gate")
    parser.add_argument("--scene-file",help="exact scene .blend for independent SHA verification")
    parser.add_argument("--out",required=True,help="new private output path outside Git worktrees")
    args=parser.parse_args()
    out=private_review_output(args.out)
    if out.exists() or out.suffix.lower()!=".json":
        raise ValueError("new private JSON output path required, cannot overwrite")
    context=source_context_from_repo()
    if args.source_only:
        if args.input or args.scene_file:
            raise ValueError("source-only mode does not accept unverified Blender claims")
        result=source_only_summary(context)
    else:
        if not args.input or not args.scene_file:
            raise ValueError("real bpy JSON and exact private .blend are required")
        report=json.loads(Path(args.input).read_text())
        verify_scene_bytes(args.scene_file,report)
        qa=read_source_and_audit(report)
        result=motion_report(report,context,qa)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as fp:
        json.dump(result,fp,indent=2,sort_keys=True)
        fp.write("\n")
    print(json.dumps({
        "kind":result["kind"],
        "source_test_count":result.get("source_test_count"),
        "unsourced_test_count":result.get("unsourced_test_count",49),
        "unsourced_peak_count":result.get("unsourced_peak_count",78),
        "canonical_promotion_allowed":False,
    },indent=2))


if __name__=="__main__":
    main()
