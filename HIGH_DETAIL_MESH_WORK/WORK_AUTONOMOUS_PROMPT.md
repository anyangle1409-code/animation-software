# Work autonomous continuation prompt

Use this text when handing the mesh candidate back to Work on the Blender laptop.

> Open the latest `codex-high-detail-candidate-v6-knee-review-20260922` branch and work only there or on a new candidate-only branch derived from it. Read `HIGH_DETAIL_MESH_WORK/WORK_START_HERE.md`, `LAPTOP_CONTINUATION_HANDOFF.md`, `FINAL_RIG_INTAKE.md`, `REVIEW_V6_KNEE_SEAM.md`, `REVIEW_V5_HANDS.md` and `REVIEW_V4B.md` first. Run `python HIGH_DETAIL_MESH_WORK/scripts/preflight_resume.py` before editing.
>
> Reproduce/verify the V6 baseline before modelling. If useful, create the review-only tagged Blender copy with `scripts/tag_v6_review_regions.py`; its `AUDIT_*` groups are selection helpers only and must never become deform weights.
>
> Continue autonomously in this order while the final canonical rig is being completed separately:
> 1. true medial-knee retopology into connected anatomical joint loops, including patella/tendon/medial-knee shape;
> 2. realistic finger/thumb/palm/wrist anatomy while preserving the push-up floor-contact guard;
> 3. skin/material refinement.
>
> Do not finalise shoulder/chest/back/armpit weights or scapular deformation against the old hierarchy. Do not change the frozen rig, exercises, IK, grips, contacts, equipment transforms, production assets or `bundled.ts`.
>
> After each exported candidate, run `scripts/candidate_quick_check.py` first. Reject failed candidates immediately before spending time on the slower tests. Then run the relevant existing focused guards and five-exercise visual/motion review. Preserve every prior candidate and create a new review checkpoint rather than overwriting V6.
>
> Keep working without asking me for routine implementation decisions. Stop and report only if a genuine structural decision is required, a validation guard cannot be satisfied without changing accepted mechanics, or the final canonical rig arrives and the task moves into rebinding/final weighting.
>
> For each accepted checkpoint, update the review note with exact geometry changes, validation totals, hashes and remaining limitations.

## Optional Blender navigation helper

The following creates a separate V6 working copy with named selection groups for:
- left/right knee seam
- a two-edge-ring knee work region
- the protected push-up floor-contact vertices

```text
blender --background --factory-startup --python scripts/tag_v6_review_regions.py -- HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.blend HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_WORK_READY.blend
```

The helper intentionally does not move vertices or change topology/skin weights.
