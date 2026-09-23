# Final rig intake checklist

Use this immediately when Claude finishes the canonical-rig work.

Do not begin rebinding the high-detail mesh until the items below are known.

## Record first

- exact `chatgpt/absolute-retarget-imports` commit SHA
- whether the canonical count is 55 bones
- whether `scapula_l/r` are neutral by default
- whether scapular rhythm is still disabled
- exact retargeter changes shipped
- whether the production-character GLB itself gained new deform bones or only the canonical/runtime rig changed
- whether forearm twist distribution changed
- whether carrying angle changed
- full test/build totals

## Compatibility check

If there is a new or changed GLB, run:

```text
python scripts/compare_rig_compatibility.py \
  HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb \
  PATH_TO_FINAL_RIG_GLb \
  --json reports/final_rig_compatibility.json
```

Interpretation:

- added/reparented named nodes: inspect before binding
- added/removed skin joints: weights/inverse binds need explicit handling
- duplicate node names: stop and resolve ambiguity
- no structural GLB change: the high-detail mesh can stay on its current source-character hierarchy and the new canonical mapping can be validated without rebinding first

## Before final weights

Must be settled or explicitly waived:
- scapula hierarchy and default neutral state
- forearm twist distribution
- carrying angle
- hand-base/palm-bone decision
- shoulder/chest/back/armpit topology adequacy

## First proof after any rebind

Before artistic weight tuning:
1. neutral pose equivalence
2. curl Bottom/Mid/Peak/Return
3. squat stand/deepest
4. shoulder press bottom/overhead
5. push-up top/bottom
6. pull-up bottom/top
7. hand/equipment lock
8. foot-floor lock
9. renderer/exporter agreement

Only once those are stable should scapula weights/rhythm and final corrective/deformation tuning start.
