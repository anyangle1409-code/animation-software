# Phase C — final hand grip refit plan

## Gate

**Do not start this phase until the V15 hand geometry is visually accepted.**

Required before entry:
- `V15_POST_EDIT_REPORT.md` is technically clean;
- the matched V13e/V15 open-hand, fist, curl, push-up and pull-up boards have been reviewed;
- the V15 finger shaft/joint surface is accepted as the geometry source;
- no unresolved protected-contact or seam failure remains.

If V15 is rejected, this document stays dormant.

## Why a refit is required

The live source currently carries a character-scoped dumbbell solution in
`src/character/solvedGrip.ts`. At the source HEAD used to prepare this plan it
contains:
- a 15 mm dumbbell radius;
- per-digit solved MCP/PIP/DIP rows;
- positive thumb opposition;
- a handle-centre correction of **9 mm proximally**.

That solution was measured against an earlier hand/body state. It is a useful
baseline and regression reference, **not the final answer for an accepted V15
hand**.

Do not restore any historical target blindly, including either the old
`-9 mm` centre or a `0 mm` centre. Re-solve against the accepted geometry and
the current exercise library.

## Source isolation

Grip work belongs on a disposable/current-source worktree or a new source-side
candidate branch.

Do not merge `chatgpt/absolute-retarget-imports` into the mesh branch.

At execution time:
1. fetch the newest `chatgpt/absolute-retarget-imports`;
2. record the exact HEAD;
3. use the accepted V15 dressed GLB as the candidate character;
4. keep the existing source solution unchanged as the comparison baseline;
5. create a versioned candidate solution rather than overwriting the old row.

Suggested temporary solution ID:

`homeGymPTMaleV15Candidate`

No production reference should point at it until acceptance.

## What is fixed during the solve

Do not move these to make the grip look better:
- wrist pose;
- accepted exercise joint trajectories;
- equipment transforms;
- equipment socket definitions;
- frozen 63-bone hierarchy;
- retarget hand-frame correction;
- protected push-up floor contact;
- accepted V15 geometry.

The solve may vary only:
- per-digit MCP/PIP/DIP closure angles for the grip family;
- thumb opposition within the existing rig limits;
- the character-scoped handle-centre correction, within a bounded search that
  must pass full-body/equipment clearance.

## Solve dumbbell first

The current `GripKind` families are:
- dumbbell;
- bar;
- handle;
- rope;
- floor;
- none.

Start with **dumbbell** because it is the established solved family and is used
across multiple current exercises.

Do not assume the dumbbell result transfers to bar/handle/rope. Their geometry,
radius and contact pattern require separate certification.

The floor profile is not part of this solve.

## Objective order

Use a lexicographic objective, not a single aesthetic score.

A candidate is better only if it satisfies the higher-priority conditions
before optimising lower ones.

1. **No meaningful digit penetration**
   - each digit should reach/contact the finite cylinder without closing through it;
   - report nearest signed distance and inside-vertex count per digit.

2. **Palm remains naturally loaded**
   - do not move the handle away from the palm merely to clear the fingers;
   - report palm nearest distance/contact.

3. **All four fingers substantially wrap**
   - avoid fingertip-only hooks;
   - report each digit's MCP/PIP/DIP row and contact state.

4. **Thumb opposes and locks**
   - verify opposition sign and actual thumb surface clearance/contact.

5. **Wrap coverage improves**
   - use the existing `measureGripFit` / widest-gap / wrap-coverage diagnostics;
   - report both hands.

6. **Angles remain anatomically reachable**
   - every solved value must be inside the current joint limits without relying
     on a later clamp to make it legal.

7. **Left/right symmetry**
   - mirrored hands should produce equivalent contact behaviour.

8. **Pose invariance where appropriate**
   - a rigid handle held by the same hand/grip family should not need
     per-exercise finger numbers.

9. **No exercise/body/equipment regression**
   - the handle-centre search must be rejected if it improves the fist by
     spending thigh, torso, bench or other clearance beyond current gates.

10. **Visual fist quality**
    - matched high-zoom renders are still required after the numeric solve.

## Handle-centre search

Do not choose a centre by eye.

Search a bounded 3D correction around the character's embedded handle centre,
with the proximal/distal direction sampled most densely.

For each centre candidate:
- run the close-until-contact digit solve;
- measure finger and thumb penetration/contact;
- measure palm loading;
- compute wrap coverage;
- run current body/equipment clearance on every exercise using that grip family.

Reject a centre immediately if it creates a new source-gate regression.

The previous project history demonstrated why this is necessary: a centre that
improves wrap can consume thigh clearance. The final centre must be funded by
the actual accepted V15 geometry and current exercise envelope, not by an old
clearance estimate.

## Exercise validation

After solving the dumbbell family, test every current exercise that uses it,
not just bicep curl.

At minimum capture:
- each exercise/phase/frame with the worst digit reach;
- minimum equipment-to-body clearance;
- hand/equipment lock error;
- bone/equipment matrix comparison where applicable;
- technique-rule result;
- loop closure.

Use the source's current `scanGripWorstCases`,
`measureGripFit`, collision/clearance gates and production frame pipeline.

## Visual review

Generate matched baseline/candidate close-ups for:
- bicep curl Bottom / Mid / Peak;
- hammer/reverse curl where the grip family applies;
- standing and seated shoulder press;
- bench/fly/row/carry or any other current dumbbell exercise that shares the
  solved family;
- both hands where visible.

Show at least:
- palm side;
- back;
- handle-axis side view;
- one oblique view.

A numeric pass does not certify a convincing fist.

## Acceptance output

Record:
- current source HEAD;
- accepted hand GLB hash;
- grip family and handle radius;
- baseline solved row;
- candidate solved row;
- handle-centre correction;
- per-digit contact/penetration;
- palm contact;
- widest gap / wrap coverage;
- joint-limit proof;
- all-exercise clearance/gate result;
- matched visual boards.

## Promotion rule

Do not overwrite the existing `homeGymPTMale` solution while searching.

Only after explicit acceptance:
- either replace it in a dedicated reviewed source commit, or
- promote the versioned V15 solution ID and update the final character to use it.

Keep a revert point for the pre-refit source state.

## Stop conditions

Stop and report instead of compensating if:
- better wrap requires changing exercise mechanics;
- a wrist or equipment transform must move;
- a validation threshold must be loosened;
- the accepted V15 mesh would need reshaping solely to make the solver pass;
- a candidate centre creates a new body/equipment collision;
- bar/handle/rope requires per-exercise magic numbers rather than a family solve;
- the final binding later changes hand/handle geometry enough to invalidate this solve.

If final 63-bone binding materially changes the hand surface or embedded handle
offsets, re-run this Phase C certification before production.


## Prepared Phase C candidate evaluator

The numeric/regression evaluation path is already prepared.

Start from:

`PHASE_C_GRIP_CANDIDATE_TEMPLATE.json`

Copy it to a new candidate JSON and edit only:
- `thumbOppositionX`;
- `handleCentre`;
- per-digit MCP/PIP/DIP rows.

Then run:

`EVALUATE_PHASE_C_GRIP.bat accepted_hand.glb candidate.json <label>`

The runner:
- fetches the newest source branch into a disposable worktree;
- preserves the shipped `homeGymPTMale` row;
- injects the candidate under its own temporary solution ID;
- tags a **copy** of the accepted hand GLB to select that ID;
- proves the metadata selected the candidate row;
- checks the row against joint limits across every current dumbbell exercise closure;
- runs the existing shipped-path skinned-cylinder grip harness on both hands in curl/press;
- requires no digit/thumb penetration beyond the existing 0.5 mm contact tolerance;
- reports palm loading separately rather than treating intended palm contact as a failure;
- requires at least the existing 190° wrap diagnostic floor;
- compares mirrored-hand, equipment-clearance and self-collision tests baseline vs candidate;
- optionally requires the full normal source suite;
- writes `reports/phase_c_grip_<label>/phase_c_grip_evaluation.json`;
- removes the disposable worktree;
- never promotes or overwrites the production grip row.

A numeric PASS still requires the matched high-zoom visual grip boards described
above before acceptance.


## Prepared Phase C seed generation

Before hand-editing a candidate row, generate coarse solver-derived seeds from
the accepted hand:

`GENERATE_PHASE_C_GRIP_SEEDS.bat accepted_hand.glb <label>`

Default absolute handle-centre Y sweep (relative to the embedded centre):
- 0 mm
- -3 mm
- -6 mm
- -9 mm
- -12 mm

This range is grounded in the project's existing 0/-6/-9/-12 mm evidence. It is
a coarse search, not an acceptance preference.

For each centre the runner:
- fetches the latest source in a disposable worktree;
- reads the **current** shipped `homeGymPTMale` centre rather than assuming -9 mm;
- runs the existing close-until-contact skinned solver on the accepted hand;
- converts the solved curl-closure angles back to closure=1 `SolvedGrip` maxima;
- verifies the same row on the mirrored right hand;
- records per-digit/thumb/palm contact and wrap;
- writes a standalone candidate JSON.

Then run the stronger certification on shortlisted JSON files:

`EVALUATE_PHASE_C_GRIP.bat accepted_hand.glb candidate.json <label>`

Seed generation never promotes a row and does not replace visual review.
