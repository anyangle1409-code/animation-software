# Model appearance phase — preserve the accepted bicep curl

**Branch:** `chatgpt/absolute-retarget-imports`  
**Starting branch checkpoint:** `e882fa1e8422fd31c85baa424987b4a3be71fcde`  
**Do not merge. Do not start another exercise.**

## Product state entering this phase

The real bundled dressed v8 bicep curl has now been visually reviewed in the app and is accepted mechanically.

Treat the following as **locked unless a model change proves a genuine regression that must be corrected**:

- bicep-curl Bottom → Mid → Peak → Return mechanics;
- grip solution and dumbbell contact;
- wrist orientation;
- elbow path and shoulder behaviour;
- curl timing/easing and loop continuity;
- thigh/shorts clearance;
- solved-grip metadata delivery;
- Stage 1 forearm/hand proportions already retained;
- Stage 2 shoulder/body proportions already retained;
- forearm twist-helper behaviour;
- retargeting machinery and exercise definitions.

The purpose of the next work is **model appearance only**. Existing non-curl exercises may be used only as regression checks if a shared character change requires it. Do not improve, tune or redesign them.

## Important asset/workspace caveat

The production GLBs and correspondence files are intentionally gitignored. Work from the same environment that contains the delivered v8 assets and prove the correct dressed v8 is loaded before judging visuals. A fresh checkout without the binaries may fall back to the procedural character and must not be used for appearance decisions.

Do not overwrite the accepted production assets at the start of this phase. Create candidate outputs first and retain the accepted delivered v8 as the rollback reference until the user approves the model appearance.

## Phase A — fix the objective surface defect first

The accepted curl preview exposed a real model-surface defect: hard/blocky faceting on the forearms, wrists and hands.

Measured evidence from the delivered v8 review:

- v8 body: about **320 split-normal seam groups / 723 affected vertices / worst split angle 138.3°**;
- v7 body reference: about **7 groups / 14 vertices / worst split angle 71.0°**;
- concentration is bilateral in the hands, forearms, thumbs and nearby upper-arm regions.

This defect is visible at both Bottom and Peak, so it is not a curl-pose problem.

### Required approach

1. Diagnose the normal/smoothing discontinuities on the actual delivered v8 body rather than changing pose, rig or exercise data.
2. Repair normals/smoothing as narrowly as possible.
3. **Prefer a normals-only / shading-only repair.** Do not alter vertex positions, topology, skin weights, joint matrices, inverse binds, solved-grip metadata, garment geometry or exercise motion merely to hide the faceting.
4. Produce candidate bare and dressed outputs rather than overwriting the accepted production pair immediately.
5. Preserve the dressed/default body-to-bare equivalence established by the delivery fix.
6. If the normal repair unexpectedly requires topology, geometry, weights, skeleton or rest-pose changes, stop and report before continuing.

### Validation after the surface repair

Prove at minimum:

- affected split-normal/seam counts and worst angles materially improve;
- no new visible seams are introduced elsewhere;
- bind/body vertex positions are unchanged if this is truly a normals-only repair;
- skeleton, weights, joint matrices, inverse binds and `scene.extras.homeGymPT` remain unchanged;
- bare vs dressed posed-body equivalence remains 0.0000 mm / zero differing posed body vertices;
- clothing remains non-interpenetrating and correspondence remains valid;
- the accepted curl still has the same grip/contact, wrist, elbow, shoulder, thigh/shorts clearance and loop behaviour;
- renderer/exporter agreement remains intact.

Use focused checks first. Run the expensive full suite only on a retained candidate that is being proposed for production.

## Phase B — visual model refinement, one decision at a time

After Phase A is visually clean, prepare a neutral model-review pack from the **actual dressed candidate**:

- full-body front;
- full-body 3/4;
- full-body side;
- upper-body/front close-up;
- face/head close-up;
- hands/forearms close-up;
- accepted curl at Bottom and Peak so model edits can be checked against the locked movement.

Then stop for user review before making broad subjective changes.

Previously requested appearance direction to keep in mind and visually reconfirm with the user:

- improve the head/shoulder silhouette first;
- add suitable hair;
- make the face more relaxed/natural;
- improve the eyes;
- preserve legs/feet unless the user now asks for changes.

Do **not** assume exact hair style, face shape, eye colour, skin/material look, body size or other subjective details without user direction. Work one visual area at a time so accepted parts are not repeatedly disturbed.

## Model-edit guardrails

For every retained appearance change:

- preserve the accepted bicep curl;
- preserve solved grip and dumbbell contact;
- preserve rig compatibility and retarget behaviour;
- keep body/dressed assets equivalent where they are supposed to be equivalent;
- keep clothing fit valid;
- take before/after screenshots from the same camera and pose;
- record any new asset hashes and what changed;
- keep the previous accepted asset available as rollback.

If an appearance edit changes deformation or motion, treat that as a regression to investigate, not as permission to retune the accepted curl around the model.

## Exit condition for this phase

The model phase is complete only when the user explicitly approves:

1. the repaired surface quality;
2. the final character appearance; and
3. the accepted bicep curl still running correctly on that final character.

Only then may the final model + curl be frozen together and another exercise become eligible for work.

**Do not merge during this phase unless the user separately authorises it.**
