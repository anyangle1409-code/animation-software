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

Validation results and actual diagnostic-motion run will be appended once
the currently running local checks finish. Full-suite success is not claimed.
