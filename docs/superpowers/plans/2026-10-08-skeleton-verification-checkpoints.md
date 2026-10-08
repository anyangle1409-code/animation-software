# Complete anatomical skeleton checkpoint plan

> For agentic workers: use superpowers:executing-plans to implement one verifiable checkpoint at a time. The owner's existing autonomous execution instruction remains in force. Claude independent inspection is planned separately; no routine approval pause is introduced by this document.

**Goal:** Build and independently verify the anatomical skeleton before rebuilding the production body around it.

**Architecture:** Source-defined regional targets become common-frame joint/contact coordinates, then a new immutable Blender anatomical revision. Geometry and movement must be verified separately before muscle volumes, skin, deformation, the smaller runtime rig and the app are updated.

**Tech stack:** Python/unit tests, JSON evidence/targets, NumPy and Blender 5.2.1 LTS through bpy; existing animation software for later functional checks.

**Spec:** `docs/SKELETON_FIRST_PRODUCTION_POLICY_20261008.md`, `docs/COMPLETE_HUMAN_SKELETON_LIVE_TRACKER_20261007.md`, and `ORIGINAL_V1_WORK/anatomy/canonical_skeleton_rebuild_spec_v1.json`.

Baseline for this plan: live branch HEAD `137f71058b2c9f142478a4261af2db352cb1bf27`, checked 2026-10-08. The plan's own publication commit will follow this baseline. Repository: `anyangle1409-code/animation-software`; branch: `codex/whole-body-biomechanics-audit-20261007`.

## Current position

**We are at CP1, canonical regional target closure (Gate 6), with provisional data and essential open dependencies.** A new corrected whole-body canonical skeleton does not yet exist. Blender is available and has run source-data fixtures and a003 movement rechecks. Those fixtures are not a replacement skeleton.

| Existing evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| 206 bones, 427 articulation/contact complexes, 30 semantic frames | Complete conventional inventory and reference structure | Correct final geometry or natural motion |
| a003: 135/135 implemented integrity tests; 41 mirror pairs and two solver-test exceptions | Reproducible diagnostic baseline and implemented test coverage | Gate 9 acceptance or complete contact/follower coverage |
| Measured scapular envelope/glenoid rim frames; lumbar orientation families; distal rib segments; carpal axes; corrected hyoid dimensions | Regional provisional source geometry and checked conversions | Absolute shoulder/spine/contact placement or a complete new skeleton |
| Latest 26 CP2/CP3 affected tests passing; earlier 21 shoulder-source checks retained | Finite capture rejection, frame metadata and limited evidence checks | Full-project green or anatomical acceptance |
| Full suite: 805 tests; five failures/four errors | Same nine named legacy production/recovery failures as the earlier checkpoint, documented | Permission to conceal the failures or modify production controls |

Current machine-readable authorities: `canonical_target_selection_v1.json` (`freeze_ready=false`) and `canonical_freeze_readiness_v1.json` under `ORIGINAL_V1_WORK/anatomy/`. Gates 6, 8 and 9 remain open. Phase 10 is blocked by those gates.

## Constraints and review focus

- Fetch/check live HEAD before each mutation batch; read and preserve concurrent work. Never reset, revert or force-push. Work only on the branch above.
- Keep a003/r95 immutable as comparison baselines. Production geometry, weights and runtime drivers remain unchanged until anatomical gates explicitly allow downstream work.
- Source endpoints, plane/projection, units, sex/stature, posture, evidence grade and independent-publication/cohort identity accompany each numerical target. Do not average incompatible definitions or infer a target by reversing a stature-prediction equation.
- Retain failed runs that expose a validator weakness. Successful commands alone do not justify anatomical acceptance.
- Review five recurring false-pass risks: endpoint/axis swaps; duplicated or incompatible sources; bilateral sign/chirality errors; positive centre gap hiding surface intersection; tests commanding a movement without measuring follower/contact behavior. Regional tests must exercise these where relevant.
- No calendar or percentage estimate is assigned until essential numerical evidence is available. Progress is measured by accepted deliverables.

## Checkpoint ladder

| ID | Deliverable | Current status | Evidence required to close it |
| --- | --- | --- | --- |
| CP0 | Protected baseline and verified tools | CONFIRMED, limited scope | Branch/head and clean state; inventory; source hashes; usable bpy; retained diagnostic movement report |
| CP1 | All regional canonical targets and measurement mappings | PROVISIONAL; specific evidence BLOCKED | Close CP1a–g below, with compatible independent evidence and source-defined geometry; no essential unset coordinate/contact targets |
| CP2 | Complete machine-readable coordinate/contact preflight | BLOCKED by CP1 | Common world/local frames; coherent 206-bone identities and 427-complex accounting; all hard invariants and adversarial checks; justified exclusions; explicit evidence review permits candidate creation |
| CP3 | New immutable canonical Blender skeleton | BLOCKED by CP2 | Next unused revision, full provenance and SHA256; independent capture/reload matches accepted target data; no a003 overwrite |
| CP4 | Owner-visible anatomical review pack | BLOCKED by CP3 | Six views, skeleton-only and transparent old-mesh overlays, old/new comparison, shoulder/spine-rib/hand/foot/pelvis close-ups; every render identifies the actual new revision |
| CP5 | Coherent joint/contact/follower mechanics (Gate 8) | PROVISIONAL core; gate open | Correct centres/axes/contact paths on the new geometry; missing mechanics implemented or independently justified; no unsupported coupling magnitudes |
| CP6 | Complete isolated movement acceptance (Gate 9) | PROVISIONAL a003 coverage; new-skeleton acceptance blocked | Independent measured sweeps on the new revision, both sides, reversals and coupled cases; explicit coverage/exclusion ledger; no unresolved movement-critical defects |
| CP7 | Whole-body exercise acceptance (Phase 10) | BLOCKED by Gates 6/8/9 | Authored exercise inputs on anatomical skeleton; simultaneous joint/contact measurements; all exercise cases below; failures retained and repaired |
| CP8 | Muscle/soft-tissue volumes, skin and deformation | BLOCKED by anatomical acceptance | Production refit follows accepted skeleton/contacts; verify silhouettes, contacts and deformation without moving anatomy to fit old skin |
| CP9 | Smaller runtime rig and app acceptance | BLOCKED by CP8 | Master/runtime trajectory comparison, export/performance checks and exercise behavior in the animation software on target devices |

CP5 research and validator work may continue independently while CP1 is open; acceptance still requires the corrected geometry. A source-data fixture never closes CP3 or CP4.

## CP1 regional checkpoints, in priority order

| ID / region | Already available | Remaining deliverable / closure check |
| --- | --- | --- |
| CP1a Shoulder | Confirmed clavicle/breadth defects; endpoint cross-check; measured relative scapula and rim frame | Evidence-backed clavicle chord/curve and SC anchor; neutral thorax pose; AC and GH/contact geometry derived from the scapula. Preserve distinct SC/AC/GH and nondegenerate AA/TS/AI. Independent dimensions use matched endpoints. |
| CP1b Spine/discs | Body/disc evidence stack, P1 S1 frame, superior/inferior lumbar orientations, independent wedge sensitivity, continuous planar clearance checker | Resolve posture/middle/edge/normal-height semantics; body/endplate envelopes and centres; cervical/thoracic curvature and head balance. Explicit nonzero C2/3–L5/S1 gaps across actual overlapping surfaces; no discs at C0/C1 or C1/C2. |
| CP1c Ribs/sternum | All 24 identities, demographic model, verified distal spiral segments | Unambiguous full proximal curves, thoracic orientation, head/tubercle/anterior contact layout, compatible sternum targets. Rib 11/12 have no costotransverse articulation. Unselected age/weight remain explicit, not invented. |
| CP1d Forearm/wrist/hand | Direct ANSUR radius context, separate ulna policy, seven carpal axes/eight envelopes, metacarpal evidence | Matched radius/ulna endpoints separately; PRUJ/DRUJ/wrist layout; all eight carpal centroids/contacts including pisiform; CMC and digit geometry. Rebuild M2–4 selectively, no uniform hand scaling. |
| CP1e Foot | Surface-length defect, source conflict records, tarsal size context | Calcaneus/talus through TMT contact chain; matched metatarsal/toe definitions and stature context; complete internal length plus separate heel/toe soft tissue. No blanket metatarsal shortening. |
| CP1f Pelvis/lower limb | Provisional HJC/sacral/femur/tibia/patella anchors, P1 S1 frame | Landmark-rich os coxae and acetabulum, SI/pubis ring closure, fibula endpoints/contacts, patellar trochlear translation. Retain corroborated anchors unless rebuilt contacts disprove them. |
| CP1g Head/mandible/hyoid | Conventional topology, plausible TMJ breadth, source-defined hyoid dimensions with corrected axes | Craniofacial envelopes, complete mandible landmarks/TMJ contact geometry, hyoid body/cornu landmarks/tilt/cervical placement. One suspended hyoid, no direct osseous articulation. Source dimensions alone do not determine the full shape. |

For each row, execute and record this cycle:

- [ ] Resolve source endpoints and independent evidence; record conflicts and essential blockers beside the values.
- [ ] Store accepted coordinates/corridors, frame definitions and contact constraints in the relevant `ORIGINAL_V1_WORK/anatomy/canonical_*_v1.json` files.
- [ ] Add a failing regression/mutation for any discovered defect; implement the smallest correction; retain revealing failures.
- [ ] Run affected numerical and bilateral/sign/contact tests; use a fresh bpy fixture when geometry or Blender conversion changes.
- [ ] Update selection, readiness, both primary tracking documents and Claude handoff; commit/push coherent verified progress with evidence links.

No regional row is checked off merely because a population mean was found or a Blender helper was drawn. Independent blocked rows may be worked while another row awaits essential evidence.

## CP2–CP7 verification tasks

- [ ] CP2: compare target selection, convergence, measurement definitions and readiness; reject NaN, collapsed centres, reflected frames, incompatible dimensions, unknown grades and missing coverage. Verify geometry continuously where centre-only checks can falsely pass. Record the independent numerical review before promoting `freeze_ready`.
- [ ] CP3: adapt `scripts/anatomy_fit/build_anatomical_master_blender.py` only after CP2 permits construction. Independently capture the fresh file and compare coordinates, identities, parent/contact relationships and hashes with accepted JSON. Reopen discrepancies.
- [ ] CP4: use/adapt `scripts/anatomy_fit/render_master_review.py` and `render_review_pack.py` for the actual new revision. Views: front, back, left, right, 3/4 front, 3/4 back. Retain a003 overlays/comparison and named close-ups; no old render labelled corrected.
- [ ] CP5: close movement-critical spine/rib, shoulder, carpal/thumb, pelvic-ring, patella/fibula and foot follower/contact findings from the live tracker. Explicitly separate sourced amplitude, test amplitude and unknown amplitude. Do not fabricate missing couplings.
- [ ] CP6: run/adapt `scripts/anatomy_fit/run_isolated_tests_blender.py` against the new immutable revision. Independently measure world directions, frame signs, joint paths, contact/clearance, followers, reversals and near-limits. Map every relevant articulation to measured coverage or a justified exclusion. Independent Claude inspection may reopen any gate.
- [ ] CP7: after Gates 6/8/9 permit it, run squat, lunge, hinge, calf/forefoot loading, shoulder press, pull-up/hang, row, curl, push-up/plank, loaded grip/pinch, wrist-supported loading, overhead and multiplanar reaching. Use project-authored exercise definitions and sourced expectations; record simultaneous joint behavior rather than invented target ranges. App diagnostic previews do not equal exercise acceptance.

## Routine verification and reporting

Run from repository root, adjusting the focused test set to the actual changes:

```bash
python -m unittest discover -s scripts -p 'test_canonical*.py'
python scripts/validate_canonical_target_selection.py
python scripts/validate_complete_anatomical_atlas.py
python scripts/validate_canonical_carpal_axes.py
git diff --check
```

A valid preflight with `freeze_ready=false` proves that the block is preserved, not that the skeleton is accepted. Broader checks are run when a change warrants them, with all known failures reported by name. Latest full-suite evidence and per-name baseline comparison are in `ORIGINAL_V1_WORK/anatomy/audit/runs/work_cp3_rejection_repair_20261008_001/`; older traces remain historical.

At every coherent push, update this plan's checkpoint position and the primary tracker. Report: **checkpoint ID; concrete change; evidence/run/revision; checks and exceptions; remaining blocker and needed input; next independent action; pushed commit.** Keep previous failed runs and immutable revisions.

**Next action:** CP1a SC/manubrial articular-centre evidence and clavicle curve/pose mapping remain first. Li2012's linked full text returned HTTP402 and its abstract omits the required value/endpoints. Recover an accessible primary table/figure or independently matched landmarks; do not substitute outer manubrial width. Continue independent CP1b–g evidence/contact work while that evidence is unavailable. No routine owner decision is currently required.

Self-review: all seven regional groups, pre-Blender gate, new revision, visual review, Gates 8/9, Phase 10, skeleton-first production hierarchy and app verification are mapped above. Dates/counts identify checkpoints rather than acceptance claims.

## 2026-10-08 laptop-session preparation checkpoint

CP1 numerical closure remains PROVISIONAL/BLOCKED. Independent CP3 review repaired finite-input/identity rejection and source-frame vs attachment metadata without changing a003 geometry. Fresh Blender 5.2.1 LTS rehearsals/captures verify 206 bones/427 markers and unchanged attachments/marker centres. The old capture mislabeled 202 source frame IDs; failed reports remain retained. CP2 actual anatomy still fails, and CP3/CP4 canonical acceptance stays blocked. 26 affected tests pass; full discovery 805 with the same nine named baseline failures/errors. Planned 20:30 BST laptop/Claude inspection instructions: `docs/LAPTOP_SKELETON_HANDOFF_20261008_2030.md`. This records readiness for an independent review, not a timed promise of skeleton completion.
