# Next action: visual review of V11

V8 remains the accepted body and knee geometry baseline. V9 was rejected and V10 was superseded; both are preserved. **V11 hand cleanup is built and passes every mechanical guard. It is not yet accepted visually.**

Read `REVIEW_V11_HAND_CLEANUP.md`, then look at the four boards in `renders_v11_hand_cleanup/`:

- `V11_V10_OPEN_HAND_COMPARISON.jpg`
- `V11_V10_CLOSED_FIST_COMPARISON.jpg`
- `V11_V10_EXERCISE_HAND_COMPARISON.jpg`
- `V11_V10_GLB_NORMALS_BIND_COMPARISON.jpg`, the same hands shaded as the app shades them

The questions from `V11_HAND_CLEANUP_PLAN.md`:

- Are the fingertip silhouettes smoother?
- Are the joint rings less artificial?
- Is the thumb web seam gone?
- Is the wrist transition continuous?
- Did any contact or grip silhouette get worse?

Two decisions go with it:

1. **Palm volume.** V11's palm is V8's, smoothed. V10's thenar and web volume caused the web wedge and was left out (`PALM_FIELDS=1` restores both).
2. **The finger-pad faceting left around the protected push-up contact vertices.** Changing it needs a replacement floor-contact proof.

## If V11 is accepted

Record it as the hand geometry baseline, then start Phase C: refit the curl grip first, then hammer, reverse and press, then pull-up.

## If it is not

Build V12 from V11, or change the V11 build and re-run `scripts/run_v11_pipeline.sh`. The build is deterministic.

- Do not go back to sculpt fields that push along vertex normals across unwelded seams: that is what opened V10's seams.
- Run `scripts/audit_hand_seams.py` on every candidate. The existing guards cannot see an open seam.

## Validation pin

Runtime `614033b` is the pinned validation source. The source branches have since moved to `87b881d`, which has 14 exercises and adds self-collision, feet and equipment-clearance gates. Measured on the current runtime (`REAL_CHARACTER_GLB` pointed at each candidate):

- **Upper arm against chest.** V10 and V11 fall below the production character's recorded baselines on 10 exercises. The closest distances are 0.5 to 4 mm, so they are not penetrations. This comes from the high-detail body's arm and chest shape, not from the hands, and V11 gives the same figures as V10.
- **Incline curl.** The dumbbell grazes the high-detail body's thigh by 0.76 mm (one vertex) at the end of the repetition. On the production character it clears.

Bring the pin forward to the current source before the body is bound for production. These are body-shape and exercise items to settle then; they do not block the hand review.

Do not change the frozen 63-bone `hgpt_canonical_v3` hierarchy, exercise mechanics, equipment, production references, palm motion or scapular rhythm.
