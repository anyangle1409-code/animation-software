# Next action: rebuild finger shaft and joint surface locally

V8 remains the accepted body/knee geometry baseline. V13e is the last hand review candidate. **V14e is an unaccepted experimental checkpoint**: adding 2,737 finger-body vertices and up to 1.086 mm of constrained smoothing passes all guards but does not sufficiently change the broad, segmented silhouette. See `REVIEW_V14E_FINGER_BODY_TRIAL.md` and its three V13e/V14e comparison boards.

Work from V13e in a separate candidate. Replace or redirect actual finger shaft, knuckle and joint surface topology on both hands, including the unwelded patches that create the angular silhouette. Keep all 682 protected original push-up contacts and their skin rows exact; keep non-hand body, frozen rig, runtime `614033b`, exercise/equipment behavior and production references unchanged. Audit bind and posed seams after the rebuild. Validate the five focused guards, seven exercises, bare/dressed equivalence, and matched open/fist/curl/push-up/pull-up renders. Only a visibly improved, technically passing hand candidate may become the geometry source for grip fitting.

## Validation pin

Runtime `614033b` is the pinned validation source. The source branches have since moved to `87b881d`, which has 14 exercises and adds self-collision, feet and equipment-clearance gates. Measured on the current runtime (`REAL_CHARACTER_GLB` pointed at each candidate):

- **Upper arm against chest.** V10 and V11 fall below the production character's recorded baselines on 10 exercises. The closest distances are 0.5 to 4 mm, so they are not penetrations. This comes from the high-detail body's arm and chest shape, not from the hands, and V11 gives the same figures as V10.
- **Incline curl.** The dumbbell grazes the high-detail body's thigh by 0.76 mm (one vertex) at the end of the repetition. On the production character it clears.

Bring the pin forward to the current source before the body is bound for production. These are body-shape and exercise items to settle then; they do not block the hand review.

Do not change the frozen 63-bone `hgpt_canonical_v3` hierarchy, exercise mechanics, equipment, production references, palm motion or scapular rhythm.
