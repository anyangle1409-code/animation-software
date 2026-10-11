# Actual laptop Blender checkpoint — 2026-10-10

## Scope and source pins

This is a fresh Blender execution and source-coordinate reproduction, NOT an
anatomically approved skeleton, contact audit, or new canonical candidate.
Blender 5.2.1 LTS (`9e2066aef7ef`) ran locally. No legacy V-series assets,
approved a003/c001–c004 records, production drivers or character geometry changed.
No c005 installation. No experiment was promoted.

Verified live refs before work and rechecked during execution:

| Source | Exact commit |
| --- | --- |
| Anatomical baseline, not main | `7761a12d684f576bf49a0bac7563d5b5ae9b8998` |
| PR #23 CT preparation | `ece4d136d05cf533bda9f319b38026cb9ecff75b` |
| PR #24 source inventory QA | `c46f477630e7f293e2722d12f943c780c462102e` |
| PR #25, this branch's parent | `6b8dda96a0bd70b3f54742147a03373ff836a3dc` |
| Claude r95 laptop branch | `540edd4ca97927e04c2966a27f70148678c29464` |
| Claude T001 coupled-trunk experiment | `de8d521bca94b826234a36a44fd3ea9243646d1f` |

Working branch: `codex/source-skeleton-blender-measurements-20261010`.
The Claude working checkout was clean and was not switched or edited.
T001 was read from its exact archived Git commit into private storage, not merged.

## Actual Blender files and measurements

Private artifact directory (outside Git):
`C:/Users/Mark/Documents/Codex/2026-10-09/referenced-chatgpt-conversation-this-is-an/work/private-source-skeleton-20261010/`.

1. Opened the real laptop
   `C:/Users/Mark/Documents/animation-software/repo/ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r95.blend`.
   It contains 67 active rig controls, a 53-control historical rig, body and shorts;
   it does **not** contain 206 anatomical bone meshes.
   Its SHA-256 stayed
   `8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd`.
2. Built/opened `c004-source-reconstruction.blend` from the approved c004 source
   record using the existing candidate builder, with r95 as the file container.
   No character fitting or skin-containment geometry adjustment was called.
   SHA-256 `2a9401e77c173280b0b6aa124330e3e48162d4cd1d1a1c77057feae7c874b7`.
3. Built/opened `t001-source-reconstruction.blend` directly from the existing
   T001 experiment record with the source-only CP3 builder; no character mesh.
   SHA-256 `d18c277892ae186441ac202f19fad5941f1a1ff3004dba96d2bf6b50a23297e8`.

Fresh captures: `c004-capture.json`, `t001-capture.json`.
Each contains 206 control heads/tails, parents and roll axes, plus 427 joint
marker centres and frames, measured from Blender. These are source-ID controls
and markers, **not 206 independently identified osseous surfaces or 427
validated articular contacts**. Neither skin nor rendered rods qualify as bone
surface evidence for PR #24. Surface/contact certification remains blocked.

Source-versus-Blender round trips (`*-roundtrip.json`) both passed storage
precision checks. Maximum bone-endpoint errors: c004 `5.87266e-8 m`, T001
`5.93415e-8 m`. Marker errors: c004 `1.99248e-7 m`, T001 `3.16156e-7 m`.
This checks faithful source reproduction, not anatomical correctness.

## Measured defect and existing experimental correction

Fresh CP2 reports are in `c004-cp2-measured/` and `t001-cp2-measured/`.

| Measured check | c004 | Existing T001 reproduced here |
| --- | --- | --- |
| Source control/marker identities and finite frames | PASS | PASS |
| Disc centre-line gaps | FAIL: 22 levels at 0 mm | PASS: all 23 positive |
| Minimum centre-line gap | 0 mm | 3.1897 mm, T4/T5 |
| T12/L1 centre-line gap | 0 mm | 5.5846 mm |
| L5/sacrum centre-line gap | 14.7328 mm | 10.2791 mm |
| Actual curved endplate clearance | UNVERIFIED | UNVERIFIED |
| Overall CP2 | FAIL, 8 PASS / 1 FAIL / 1 UNVERIFIED / 1 INFO | INCOMPLETE, 9 PASS / 0 FAIL / 1 UNVERIFIED / 1 INFO |

Exactly 46 controls have different endpoints between the captured scenes (92
endpoints: both head and tail of each changed control): 22 vertebrae
(C3–L5) and 24 ribs. The other 160 controls are unchanged. T001's experimental
spacing improvement was independently reproduced in actual Blender, not newly
invented or installed as canonical geometry. Unresolved C7 residual, sacral
frame, rib curvature/orientation, costal cartilage and anatomical endplate
surfaces remain blockers. The experiment's fixed pelvis/shoulder/head anchors
must not be changed to accommodate skin.

## Fresh visual review

`c004-rendered/` and `t001-rendered/` each contain 20 newly generated PNGs:
whole-body front/back/sides/obliques, shoulders, spine, pelvis, hands, foot and
head/neck. Source hashes remained unchanged after rendering. Body-front and
spine-side views were inspected, including the T001 spine-side comparison.
They show straight rib-control rods and point/line vertebral proxies, not
curved ribs or vertebral bodies. Other generated views are available for the
next region-specific visual review; generation alone is not anatomical review.

## Reversible technical correction

The movement-provenance gate used Windows backslash paths to look up immutable
Git-style slash-separated source evidence keys. Existing real-source tests
failed before correction; four lookups now use `Path.as_posix()` and all 10
focused movement-source tests pass. No hash pins, amplitudes, approval rules
or source geometry changed. CI adds an independent Windows run and disables
checkout newline conversion there so exact-byte provenance is preserved.

c004's source placement classes are 115 proportional, 45 surface-landmark,
38 surface-station, 4 shoulder-proposal and 4 regression controls. These are
placement provenance labels, not independently verified bone surface classes.

The source `isolated_tests.py` bytes in this private working checkout were
normalized back to the Git LF bytes for verification, without semantic edits.
This is not a relaxation of source hashing. Do not change pinned source hashes
to accept an arbitrary newline-converted local file.

## Evidence limits and next actual tasks

Regional readiness remains **0 READY / 9 PARTIAL / 3 BLOCKED**.
The 78 unsupported peaks across 49 source tests remain diagnostic-only.
No safe-ROM, loaded movement or natural compound-motion certification.

The private CT cache has 72 source frames and verified scanner/sample evidence,
but none of the seven required pelvic landmarks has independent anatomical
acceptance. Threshold bridges are not cartilage contact or bone identity;
patient/scanner-to-HGPT anatomical registration is still unverified. Do not
use this source-control reproduction as CT registration evidence.

Next laptop work can use these exact measured scenes without rebuilding them:

- Review fresh regional images and the CP2 reports; continue source-bound T001
  endplate/rib/cartilage work without replacing c004.
- Inspect neighbouring original CT slices and source-pinned annotations for
  the seven osseous landmarks; retain/reject hypotheses explicitly and acquire
  independent second-review evidence before accepting any landmark.
- Use actual closed bone surfaces, when independently justified, for PR #24
  mesh/contact intake. Never submit body skin or display rods as anatomical bone.
- Use PR #25's distinction between SC elevation and posterior axial rotation;
  no arbitrary clavicle curve or universal 10-degree cap.
- Continue carpal/tarsal/forearm/patellar/craniofacial blockers only as their
  independent source evidence allows; no canonical freeze or promotion.

## Completed actual diagnostic movement run

Blender saved and reopened `c004-diagnostic-motion.blend`, SHA-256
`db84bb2df3281d1a0f4d4642c806aaf642b5ae6552aa5c5d65013010bb69f363`.
The existing runner measured **9,575 evaluated frame samples across 135
isolated tests**. Its private report and samples are in
`c004-diagnostic-motion-run/`. The original c004 reconstruction and diagnostic
file hashes were unchanged by measurement; the frame was restored.

Results: 135/135 command/measurement implementation-integrity checks passed;
41/43 mirror pairs passed actual Blender measurements; two side-specific
amplitude pairs are recorded as solver-test-only, not Blender mirror passes.
Maximum joint-centre drift was `1.4283327219369698e-7 m`; maximum off-axis
residual `3.94644085838106e-5 degrees`. These are numerical implementation
observations, not physiological tolerances.

The runner's actual scope is isolated bone-control sweeps. Contact mechanics,
surface collision, real translations and physiological follower couplings are
not verified. The existing shoulder-complex diagnostic relation was exercised
as already authored, NOT installed as an independently justified clavicle curve.
No pressing/pulling/squat/hinge/lunge/grip/gait family is certified by these
isolated tests. All 78 unsupported source peaks remain quarantined.

The first invocation refused a nonempty output folder before authoring; the
successful retry used a new exclusive output folder. No output was overwritten.
`c004-motion-rendered/` contains 20 neutral views plus five actual peak-pose
screenshots: hip flexion (frame 21), knee flexion (381), subtalar inversion/
eversion (551), pronated elbow flexion (1176) and the existing diagnostic
shoulder complex (5716). They came from the measured saved scene, not synthetic
test fixture coordinates. The shoulder peak screenshot was inspected: controls
only, and the fixed shoulder camera crops the distal raised arm. It is not a
full-arm clearance view or anatomically validated overhead movement.

Blender resolved the relative render output path to a different private folder.
All 25 generated PNGs were moved into the intended private folder with each
SHA-256 checked before/after and no overwrites. The original render manifest's
`files_sha256` is empty because of that path mismatch; do not present it as a
complete PNG hash manifest. Use absolute CLI input/output paths on this laptop.

## Verification status

- Movement source provenance: **10 local tests passed**, independently rerun
  by the read-only reviewer.
- CP2 source-control geometry checks: **19 tests passed**.
- CP3 source/capture roundtrip checks: **8 tests passed**.
- Primary clavicle source compatibility: **6 tests passed**.
- PR #24 intake: **11 tests passed / one Windows symlink privilege error**
  (`test_private_qa_destination_never_inside_git_or_via_symlink`). This test
  was not weakened or bypassed; the local account cannot create its symlink.
- Git diff whitespace check passed; source byte hashes and scene hashes checked.
- Independent review found no substantive code/CI/evidence issue. Corrected
  its minor wording finding: 46 changed controls means 92 changed endpoints.
- GitHub Actions run `38061132864` at
  `d505cd54e00405008851b0c43dbb210a90df6112`: **both Windows source-motion
  provenance and Linux source-motion safety-gate jobs completed successfully**.
  This is focused CI, not the entire project's test suite or a remote Blender run.

The broad local Windows `unittest discover -s scripts -p test_*.py` run
finished: **1,097 tests, 20 failures, 71 errors, one skip**, 1,102.593 seconds.
Exact tracebacks are private in `full-suite-windows.log`. Several errors are
missing assets in this partial checkout, e.g. candidate r29/DEFORMATION_BASELINE
JSON, `coordination/MODEL_CANDIDATE_READY.template.json`, source exercise files
and a c003 Blender file. The symlink privilege error is also present. Other
reported failures need separate diagnosis; neither all causes nor absence of
unrelated regressions is claimed. No expectations were changed to make it green.

Failed test modules (the log preserves each precise test and traceback):
`test_ansur_endpoint_correspondence`, `test_arm_chain_ansur_audit`,
`test_canonical_lumbar_orientation_sensitivity`,
`test_canonical_lumbar_wedge_decomposition`, `test_complete_anatomical_atlas`,
`test_evidence_integrity_audit` (two), `test_original_v1_contact_source_bridge`
(two), `test_original_v1_execution_orchestration`,
`test_original_v1_whole_body_issues`, `test_review_pack_index` (two),
`test_rib_spiral_reconstruction`, `test_shoulder_proposal_c001` (two),
`test_shoulder_proposal_c002`, `test_skeleton_audit_and_p001`,
`test_spine_trunk_audits`, and `test_state_restoration_audit`.

Draft PR #26 publishes the technical fix and this checkpoint only, stacked on
PR #25. All generated Blender files, medical bytes, captures and images remain
outside Git; Claude/Work source branches are preserved.
