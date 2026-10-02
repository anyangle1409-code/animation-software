# Phase 3 pre-freeze owner corrections — 2026-10-02

Status: OWNER-DIRECTED PRE-FREEZE CORRECTION PACKAGE  
Branch: `claude/original-v1-blender-o2-20260929`  
Starting live HEAD when this package was authored: `f3936a69fedc69a38565a57b65f23e8b402e48e2`  
Starting verified candidate: `r38`  
Starting candidate SHA-256: `7369b2d886ddffe6d8f80911a14f0efc69d8b5daf741ba92014434433323819b`

This package records explicit owner visual review of the real r38 Blender renders. It does not
approve r38 for production and does not weaken any gate. Current repository evidence still
supersedes this starting snapshot if the branch advances.

## Owner decision already given

The owner authorises the five inherited R2 shoulder/torso minima regressions to be retained as a
documented DEVELOPMENT trade-off for continuation. R2 itself remains untouched. Acceptance
thresholds and comparison tolerances remain unchanged.

The next numbered development baseline must be created only from the latest genuinely verified
continuation after the corrections below, not blindly from the r38 starting snapshot if a newer
candidate is required.

The five authorised inherited regressions are:

1. `press_bottom / shoulder / region_min_ratio`: R2 0.577 -> 0.548
2. `press_bottom / torso / region_min_ratio`: R2 0.943 -> 0.889
3. `press_top / torso / region_min_ratio`: R2 0.886 -> 0.823
4. `pullup_top / shoulder / region_min_ratio`: R2 0.694 -> 0.670
5. `pullup_top / torso / region_min_ratio`: R2 0.883 -> 0.861

These values are a development floor, not a quality target. Later work should improve them when
safe without erasing their historical record.

## New pre-freeze correctness findings from owner review

The following findings are not routine Phase 5 cosmetic polish. They must be resolved or explicitly
classified with evidence before Phase 4 development deformation freeze proceeds.

### A. Distal finger bending direction — MUST FIX NOW

Real r38 review images include:
- `hand__pose_curl_peak_close_hand_a.png`
- `hand__pose_curl_handle_close_hand_a.png`
- `shoulder__pose_pullup_top_close_hand_a.png`

Observed problem:
- distal finger segments visibly reverse-bend / hyperextend in flexed grip poses;
- fingertip direction does not read as anatomically consistent human flexion.

Required correction:
- inspect the generic finger joint rotations, limits, pose construction and skin deformation;
- correct the underlying generic hand/finger behaviour, not the camera;
- do not introduce an exercise-name-specific hack;
- no visible reverse DIP/PIP bending in a flexed grip unless a deliberately validated anatomical
  posture genuinely requires it;
- preserve the solved grip/contact behaviour and re-run grip evidence after any change.

High-detail knuckle, nail, crease and general hand sculpt polish remains Phase 5D.

### B. Push-up palm and hand support — MUST FIX NOW

Real r38 review images include:
- `pushup__pose_pushup_bottom_three_quarter.png`
- `pushup__pose_pushup_bottom_close_hand_a.png`

Observed problem:
- the hand reads as loading on its side/edge rather than through a planted palm;
- the support posture is not a convincing human push-up hand contact.

Required correction:
- palm/metacarpal support plane must read planted to the floor;
- fingers should project/splay naturally for loaded support;
- left/right support must be coherent;
- preserve floor-contact semantics and verify contact residuals after correction;
- do not hide the failure with crop, camera, clothing or a cosmetic sculpt.

### C. Push-up wrist orientation / extension — MUST FIX NOW

The wrist is part of the same functional support chain and must not be deferred as surface polish.

Required correction:
- inspect hand-to-forearm orientation under the push-up load;
- establish believable loaded wrist extension and forearm/hand alignment;
- eliminate obvious twist, edge-loading or discontinuity caused by pose, weights or deformation;
- keep the solution generic and reusable for human movement rather than keyed to one exercise name.

Surface creases/tendon detail remain later anatomy work; support mechanics do not.

### D. Push-up toe / forefoot support — MUST FIX NOW

Observed problem:
- the push-up rear-foot/toe presentation is not a convincing loaded forefoot/toe support posture.

Required correction:
- support should read through a plausible forefoot/toe-pad region;
- toe/forefoot dorsiflexion and ankle-foot alignment must be anatomically believable;
- do not use a shoe to conceal incorrect barefoot support;
- preserve the floor/contact system and re-run relevant contact evidence.

Final foot proportions and toe sculpt quality remain Phase 5F.

### E. Shoulder / axilla overhead deformation — CLASSIFY NOW; FIX NOW IF DEFORMATION-BASED

Real r38 review image:
- `shoulder__pose_press_top_close_shoulder_a.png`

Observed problem:
- sharp webbed/pinched axillary transition and poor shoulder-to-upper-arm continuity in overhead
  elevation.

Before Phase 4, classify the cause using existing stress poses:
- `press_bottom`
- `press_top`
- `press_top_rhythm`
- `pullup_hang`
- `pullup_hang_rhythm`
- `pullup_top`

Decision rule:
- if caused by weighting, pose support, deformation topology or other movement mechanics, repair it
  now before freeze;
- if deformation is mechanically sound and the defect is only coarse surface anatomy, document the
  evidence and defer the surface-form refinement to Phase 5B.

Do not reopen canonical-v4 rest/hierarchy or weaken gates merely to improve appearance.

## Shoes — approved later, not as a masking workaround

The owner wants a pair of athletic/training shoes added to the final character if practical.

Rules:
- barefoot push-up forefoot/toe contact must first be correct;
- shoes are a later first-party clothing/garment task, expected under Phase 7 unless the authoritative
  plan is deliberately updated;
- shoes must be independently authored and zero-third-party;
- their sole/contact geometry must respect the verified underlying support mechanics;
- shoes may visually cover toes in the final dressed character, but must never be used as evidence
  that an unresolved barefoot contact problem is fixed.

## Protected structures

Do not silently alter:
- R2 historical baseline or its evidence;
- development/production thresholds;
- comparison tolerances;
- frozen 15 stress-pose definitions;
- canonical-v4 63-bone hierarchy/rest structure;
- provenance controls;
- solved equipment handle frames merely to manufacture a pass.

No V8-V15f geometry, topology, coordinates, weights, bind data, materials, textures or garment
content may be copied or transferred.


## External human-reference validation — REQUIRED for this pre-freeze package

Read and follow `docs/EXTERNAL_HUMAN_MOVEMENT_REFERENCE_POLICY.md`.

Before accepting the corrections for finger flexion, push-up palm/wrist support,
push-up forefoot/toe support, or shoulder/axilla classification, use suitable external
human exercise imagery/video as **reference-only development evidence**.

Required use:
- compare the project-owned candidate at defined movement checkpoints with multiple
  competent human examples where practical;
- record source metadata plus relevant timecode/frame location;
- write generic anatomical/biomechanical observations rather than copying a person's
  exact form;
- use the reference to identify whether the model problem is pose/constraint,
  contact/support, joint direction, weighting/deformation, topology/support, or
  surface anatomy;
- then implement the smallest general first-party correction and re-run all project
  evidence.

External media is NOT production content. Do not transfer or copy geometry, topology,
coordinates, weights, bind data, textures, motion data, authored animation curves,
or person-specific body proportions. Prefer committing links/timecodes and
project-authored observations rather than third-party media.

This reference layer supplements — never replaces — the unchanged numerical gates,
contact diagnostics, provenance rules and real Blender review renders.

## Execution method

1. Fetch/re-read live remote HEAD before touching Blender.
2. Run the existing session preflight/start wrapper and reconcile any newer evidence.
3. Preserve r38 and all historical candidates.
4. Diagnose A-E independently before broad edits.
5. Use the smallest general first-party correction that resolves the underlying cause.
6. Declare local edit masks/intents before geometry/weight edits under the existing evidence policy.
7. Use new numbered candidate revisions; never overwrite r38.
8. Re-run affected focused evidence first, then the full 15-pose evidence/comparators before
   accepting a continuation.
9. Reject a local fix if it creates a new material regression or breaks established contact/grip
   behaviour.
10. Generate and commit real Blender review PNGs. Routine owner viewing is non-blocking once the
    technical correctness evidence is genuinely green.

## Minimum real review evidence after correction

Commit matched current-candidate views sufficient to inspect:
- curl/grip hand close-up with distal finger flexion visible;
- pull-up hand close-up;
- push-up full three-quarter;
- push-up palm/wrist close-up;
- push-up forefoot/toe close-up;
- press-top shoulder/axilla close-up;
- any extra side/rear view needed to classify shoulder cause.

Use the existing controlled capture protocol and candidate/source hashes.

## Phase transition order after these corrections

Only after the corrections above are technically reconciled:

1. record the owner's authorised five-minima DEVELOPMENT trade-off;
2. create the next unused numbered development baseline from the verified continuation;
3. run the genuine Phase 3 exit verifier;
4. if it genuinely passes, run Phase 4 development deformation freeze;
5. if Phase 4 genuinely passes, continue automatically to Phase 5:
   - 5A torso
   - 5B shoulders
   - 5C arms
   - 5D hands
   - 5E pelvis/legs
   - 5F feet
   - 5G head/neck

Phase 5 should improve safely where possible; the authorised R2 minima are not quality targets.

## End-of-session handoff required

Record and push:
- live HEAD and new candidate revision/hash;
- correction/classification outcome for A-E;
- development blocker/failure count;
- comparisons versus R2, direct parent and relevant hand/contact candidates;
- exact Phase 4 eligibility state;
- real review-image paths/manifests;
- current next action;
- whether an actual owner-only decision remains.

Do not claim production approval.
