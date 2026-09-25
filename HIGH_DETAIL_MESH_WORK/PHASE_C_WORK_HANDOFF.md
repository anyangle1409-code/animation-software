# Phase C Work handoff — dormant until V15 visual acceptance

Do not execute this handoff unless V15 has passed the visual anatomy gate.

Read `PHASE_C_GRIP_REFIT_PLAN.md`.

When activated:

1. Fetch the newest `chatgpt/absolute-retarget-imports` and record its HEAD.
2. Work in an isolated source candidate/worktree. Do not merge it into the mesh branch.
3. Use the accepted V15 dressed GLB as the real character.
4. Preserve the existing `homeGymPTMale` solved grip as a baseline.
5. Create a temporary versioned solution such as `homeGymPTMaleV15Candidate`.
6. Re-solve the **dumbbell** family against the accepted V15 hand:
   - per-digit MCP/PIP/DIP;
   - thumb opposition;
   - bounded handle-centre correction.
7. Hold wrist pose, exercise motion, equipment transforms, sockets, retargeting
   and the frozen hierarchy fixed.
8. Reject any solve that introduces a new body/equipment/technique/contact gate
   regression anywhere in the current exercise library.
9. Generate matched high-zoom baseline/candidate grip boards.
10. Stop for acceptance. Do not overwrite the old solution or promote automatically.

The current source's historical `-9 mm` handle-centre correction is evidence,
not a target. Re-measure it against V15 and the current library.


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
