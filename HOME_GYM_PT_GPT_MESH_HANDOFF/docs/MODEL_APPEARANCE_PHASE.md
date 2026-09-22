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

## Approved visual reference direction

The user has supplied an **AI-generated Home Gym PT character reference board** in the conversation immediately before this phase. When this phase is executed, the same reference-board image should be attached/provided alongside the prompt so it can be judged visually rather than from prose alone.

Use that board as the main **appearance-direction reference**, not as an identity match and not as a new rig/pose authority.

The intended appearance shown by the board is:

- realistic, contemporary athletic male rather than a mannequin/cartoon look;
- muscular and lean but still natural and believable for a fitness/PT character;
- broad, naturally sloping/relaxed shoulders — **not elevated or shrugged**;
- defined chest, arms and forearms with a narrow athletic waist and balanced legs;
- clean human proportions rather than exaggerated bodybuilding mass;
- realistic hands and forearms with smooth surface shading;
- short, textured dark-brown hair with tidy/tapered sides;
- relaxed, focused neutral expression rather than a strained or blank face;
- natural-looking eyes, approximately light blue/grey in the board;
- subtle facial stubble rather than a heavy beard;
- realistic skin/material response rather than the current flat grey mannequin presentation;
- simple dark athletic shorts.

The board contains front, 3/4, side and back body views plus dedicated head/face, chest/shoulder, arm, forearm/hand, hair and eye references. Use each panel for the feature it depicts rather than forcing one camera view to define everything.

### Reference limits

- Do **not** treat the generated person as a real individual to reproduce exactly; it is a design target.
- Do **not** use the reference to change the accepted bicep-curl pose or movement.
- Do **not** infer exact height or absolute body dimensions from the board.
- Do **not** add trainers/footwear merely because they appear in the reference board; preserve the current feet unless the user separately requests footwear.
- Do **not** substantially bulk up or shrink the character without visual review; aim for the reference silhouette while protecting the accepted rig/deformation work.
- If matching a visual feature would require changing rig proportions, weights, topology, bind/rest pose or accepted curl mechanics, stop and show the trade-off before doing it.

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
- full-body back;
- upper-body/front close-up;
- face/head front and 3/4 close-ups;
- hands/forearms close-up;
- accepted curl at Bottom and Peak so model edits can be checked against the locked movement.

Compare the candidate directly with the supplied reference board using the same or as-close-as-practical camera angles. Then stop for user review before making broad subjective changes.

### Visual refinement order

Unless the user changes the priority after seeing the review pack, work in this order:

1. surface/normal quality, especially forearms, wrists and hands;
2. head/neck/shoulder silhouette and relaxed shoulder line;
3. overall physique/silhouette against the front/3/4/side/back reference views;
4. face shape and relaxed expression;
5. eyes;
6. hair;
7. skin/material presentation;
8. shorts/material finishing;
9. final hands/forearms visual pass.

Do not change everything at once. Present a candidate after meaningful visual stages so the user can steer the look without repeatedly disturbing accepted work.

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
2. the final character appearance against the supplied visual reference direction; and
3. the accepted bicep curl still running correctly on that final character.

Only then may the final model + curl be frozen together and another exercise become eligible for work.

**Do not merge during this phase unless the user separately authorises it.**

---

# Review round 2 — upper-body appearance (user review, 2026-09-17)

Added by Claude from the user's review of the Phase A + skin/material captures, before any
further change, so this file stays the joint source of truth for the phase.

## Accepted so far

- **Phase A normals repair — accepted.** The Phase A candidates are the working baseline.
- **Skin and material — delivered for review** (`MODEL_PHASE_B_SKIN_MATERIAL.md`), candidates
  `d71b70bc…c18f2be` / `8d07100f…f08f27ca`. Not yet explicitly approved; carried forward as the
  base for this round.

## This round's scope, in the user's priority order

This **supersedes** the generic "visual refinement order" above for the next round of work. Items
1–4 only; nothing else.

1. **Rear rib / armpit protrusion.** An odd protrusion on the back/side torso near the rear rib
   and armpit area.
2. **Armpit placement and transition**, so it reads naturally from the front and 3/4 views.
3. **Pointed shoulder silhouette in side view** — the shoulders should read rounder and more
   natural.
4. **Overall torso shape against the reference board**: cleaner pec shape, more natural
   chest-to-shoulder and chest-to-armpit flow, clearer V-taper, tighter waist and obliques, and
   more refined abs and lower torso.

## Constraints restated for this round

Unchanged and not to be touched:

- locked bicep-curl mechanics and loop;
- grip solution and dumbbell contact;
- the Stage 2 shoulder-width work;
- every already-approved validation result.

What this round *may* change: body vertex positions on the torso and shoulder/armpit region.
What it may **not** change: topology, skin weights, the skeleton, joint matrices, inverse binds,
bind/rest pose, `scene.extras.homeGymPT`, the garment, or any exercise definition. Shoulder span
must measure the same before and after.

Deliverable: review-ready matched comparison captures (front, 3/4, side, and close-ups where
needed) plus a short written summary of what changed, what remains, and any blocker. Then stop.
No merge, no promotion.
