# V11 Hand Cleanup Plan

Purpose: make the next Work session as direct as possible. V10 is the mechanically safe topology checkpoint; V11 should be a focused visual/anatomical cleanup, not another rig or solver change.

## Source state

- Accepted body/knee geometry baseline: V8
- Rejected hand experiment: V9
- Current hand-topology checkpoint: V10
- V10 branch: `codex-high-detail-candidate-v10-hand-anatomy-review-20260923`
- V10 commit: `e1b77e4b5c8705f358a0f843aa3e39f8a7c864d3`
- Frozen skeleton: `hgpt_canonical_v3`, 63 bones, frozen at `19ca602`
- Current runtime/retarget source: `614033b`
- Do not change the rig, exercise mechanics, equipment, palm motion, scapular rhythm or production asset references.

## Start point

Use V10 as the modelling source unless a V10-local defect proves easier to correct from V8. Preserve V8, V9 and V10 unchanged.

Primary editable source:
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v10_hand_retopology.blend`

## V11 objective

Keep V10's useful added topology, but remove the remaining obvious artificial features:

1. Fingertips
   - round the distal caps
   - remove faceted/polygonal end silhouettes
   - keep fingertip pad volume
   - do not shorten digits unless measured evidence requires it

2. Finger joints
   - reduce visible banding/ridging at DIP/PIP/MCP transitions
   - preserve readable joint structure without ring-like segmentation
   - keep natural taper from proximal to distal phalanx

3. Thumb-index web
   - remove the dark seam/crease visible in some V10 angles
   - preserve a believable web thickness and thumb base
   - do not collapse the thenar mass

4. Palm
   - keep V10 palm volume
   - refine thenar/hypothenar transitions only where needed
   - avoid flattening the palm

5. Wrist transition
   - remove the visible stepped/banded transition
   - blend forearm into wrist/hand smoothly
   - preserve wrist dimensions and bone alignment

6. Symmetry
   - mirror the anatomical cleanup left/right unless a measured asymmetry is intentional

## Hard preservation requirements

- all 682 protected push-up contact vertices remain unchanged unless a replacement floor-contact proof is produced
- no non-hand original V8/V10 body vertex may move
- canonical hierarchy remains exactly frozen
- no grip refit yet
- no equipment movement
- no exercise-definition changes
- no validation-threshold relaxation
- no production promotion
- no scapular rhythm or palm-cupping activation

## Validation required before review

Run the same V10 guard set against runtime `614033b` / frozen `hgpt_canonical_v3`:

- structural quick check
- zero degenerate triangles
- zero >2-face non-manifold edges
- bare/dressed equivalence
- push-up floor-contact guard
- all seven exercises, 26 frames each
- bone matrices unchanged
- equipment matrices unchanged
- loop closure
- technique/reachability checks

## Visual review set

Generate matched V10 vs V11 closeups with identical cameras and lighting:

1. open palm
2. back of open hand
3. thumb-index web
4. equipment-free closed fist — palm
5. equipment-free closed fist — back
6. equipment-free closed fist — side
7. curl grip
8. push-up hand contact
9. pull-up grip

The review should make it easy to answer:
- Are fingertip silhouettes smoother?
- Are joint rings less artificial?
- Is the thumb web seam gone?
- Is the wrist transition continuous?
- Did any contact or grip silhouette become worse?

## Acceptance rule

V11 is acceptable as the hand-geometry baseline only if:
- the four visible V10 defects above are materially improved,
- no new seams/ridges are introduced,
- all mechanical guards pass,
- push-up floor contact is preserved,
- and no unrelated body geometry changes.

If V11 still has obvious faceting/seams, preserve it and stop for another local cleanup candidate. Do not start grip refitting until hand anatomy is visually accepted.

## After hand acceptance

Only then move to Phase C:
- refit curl grip first
- then hammer/reverse/press
- then pull-up
- judge actual contact, penetration, wrap and fist quality
