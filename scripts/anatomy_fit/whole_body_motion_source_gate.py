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

import isolated_tests as isolated
import movement_evidence_queue as queue
from whole_body_blender_evidence_gate import (
    REPO, private_review_output, read_source_and_audit, verify_scene_bytes,
)

ANATOMY=REPO/"ORIGINAL_V1_WORK"/"anatomy"
RECORD=ANATOMY/"character_fit_r95_a003.json"
ATLAS=ANATOMY/"whole_body_movement_atlas.json"
SOURCE_QUEUE=ANATOMY/"audit/work_evidence_queue_20261009/unsupported_movement_peaks.json"
AUDITED_KINDS={
    "EXACT_CONTEXT","STATED_IN_BASIS","HALF_OF_SOURCED_TOTAL",
    "CONDITION_IN_TEST_ID","TARGET_MINUS_FITTED_REST",
    "DRIVEN_TO_MEASURED_TARGET","LABELLED_TEST_AMPLITUDE",
}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evidence_context(record,atlas,original_queue,record_hash,atlas_hash):
    """Independent recalculation; no false upgrade if old evidence changed."""
    if (original_queue.get("schema_version")!=1 or
            original_queue.get("kind")!="READ_ONLY_MOVEMENT_EVIDENCE_QUEUE" or
            original_queue.get("anatomical_acceptance") is not False or
            original_queue.get("existing_limits_changed") is not False or
            original_queue.get("record_sha256")!=record_hash or
            original_queue.get("atlas_sha256")!=atlas_hash):
        raise ValueError("source movement queue SHA or nonacceptance invariant changed")
    tests=isolated.specs(record,atlas)
    ids=[t["id"] for t in tests]
    if len(ids)!=135 or len(set(ids))!=135:
        raise ValueError("expected 135 independent isolated movement tests")
    generated=queue.build(tests)
    if (generated["peak_count"]!=78 or generated["test_count"]!=49 or
            len(generated["by_family"])!=12 or
            sum(generated["by_family"].values())!=78 or
            generated!={
                k:v for k,v in original_queue.items()
                if k not in ("record_sha256","atlas_sha256")
            }):
        raise ValueError("original 78-source movement-peak queue no longer matches executable source tests")
    by_test={}
    classified_peaks=0
    for test in tests:
        kinds=queue.provenance.classify(test)
        if any(k["kind"] not in AUDITED_KINDS for k in kinds):
            raise ValueError("new unknown/untraced pose amplitude must be investigated")
        classified_peaks+=len(kinds)
        by_test[test["id"]]=kinds
    if classified_peaks!=278:
        raise ValueError("original 278 commanded test peaks changed")
    unsourced={}
    for row in generated["peaks"]:
        unsourced.setdefault(row["test"],[]).append(row)
    if len(unsourced)!=49:
        raise ValueError("all 49 diagnostic-only movement tests must be retained")
    for test_id,peaks in by_test.items():
        unsupported=[x for x in peaks if x["kind"]=="LABELLED_TEST_AMPLITUDE"]
        observed=unsourced.get(test_id,[])
        if len(unsupported)!=len(observed):
            raise ValueError("one or more unsupported peaks silently dropped")
        for x in unsupported:
            if not any(x["channel"]==q["channel"] and x["peak"]==q["peak"] for q in observed):
                raise ValueError("source peak/channel mismatch")
    return {
        "test_ids":ids,"by_test":by_test,"unsourced":unsourced,
        "by_family":generated["by_family"],
        "original_record_sha256":record_hash,"original_atlas_sha256":atlas_hash,
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
