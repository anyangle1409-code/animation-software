# Home Gym PT — master roadmap to self-sufficient exercise generation

This is the high-level execution order. Detailed plans and tools live beside it
in `HIGH_DETAIL_MESH_WORK`.

## Non-negotiable architecture

- Canonical driver: `hgpt_canonical_v3`, 63 bones, structurally frozen.
- Final character keeps its reviewed source rig/bind/helper structure; the
  canonical rig drives it through retargeting.
- Existing family builders remain the source of exercise motion.
- Prompt generation translates intent into typed family variants; it does not
  author arbitrary joint angles.
- Validation limits are never exposed to the correction loop.
- Unsupported prompts are refused/questioned rather than approximated.
- Candidates never auto-promote.

## Phase map

| Phase | State | Main remaining work | Needs Blender/Work? |
|---|---|---|---|
| A — knee/body geometry | DONE for current geometry checkpoint | V8 remains accepted body/knee baseline | No |
| B — hand geometry | ACTIVE / prepared | V15 deep shaft/joint surface rebuild + visual acceptance | **Yes — actual modelling** |
| C — final grip refit | PREPARED / gated | Re-solve final hand grip family geometry after B | Mostly source/analysis; visual review |
| D — skin/material | PREPARED / gated | Run bounded verified material sweep, choose result | No Blender required for prepared GLB sweep; visual review |
| E — shoulder/back/chest/armpit topology | PLANNED / gated | Final deformation-ready shoulder/axilla mesh topology | **Yes — actual modelling** |
| F — source-rig deform structure/weights | PLANNED + audits prepared | Plausible source palm/metacarpal + scapula controls/weights; preserve source rig | **Yes — rig/weight work** |
| G — palm/thumb/scapula movement | PLANNED / gated | Activate existing canonical capabilities through final retargeted character | Source code + validation |
| H — prompt-generation expansion | PLANNED + tooling prepared | Certify remaining 12 family builders | Source code + validation |
| Final acceptance | RUNNER PREPARED | One isolated release proof | No Blender if previous phases complete |

## Phase B — current immediate job

Source:
- body/knee: V8
- hand source: V13e
- V14e: rejected visual calibration only

Preparation branch:
`work/v15-deep-hand-rebuild-prep-20260925`

### Work flow

From `HIGH_DETAIL_MESH_WORK`:

1. `START_V15_HAND.bat`
2. Perform the actual finger shaft/joint modelling in Blender.
3. Save the prepared candidate.
4. `RUN_V15_POST_EDIT_ALL.bat`
5. `OPEN_V15_REVIEW.bat`

If the candidate is fundamentally weak:
- preserve it;
- run `START_NEXT_V15.bat`;
- never overwrite an earlier attempt.

See:
- `V15_DEEP_HAND_REBUILD_PLAN.md`
- `V15_WORK_HANDOFF.md`
- `V15_FAILURE_RECOVERY.md`

## What Phase B automation already handles

Work does not need to rediscover:
- baseline/version history;
- protected push-up vertices;
- problem finger regions;
- bone/joint guides;
- V13e visible surface ends;
- UV/weight export repair for new vertices;
- export triangulation;
- stable-ID GLB packing;
- frozen/runtime validation;
- direct V13e matched renders;
- rejected-V14e image calibration;
- per-digit faceting comparison versus V13e/V14e;
- latest-source integration;
- iteration naming/preservation;
- result summary/dashboard.

The irreducible task is the actual mesh shape.

## Phase C — grip

Entry:
- final hand geometry visually accepted.

Use:
- `PHASE_C_GRIP_REFIT_PLAN.md`
- `PHASE_C_WORK_HANDOFF.md`

Important:
- the historical -9 mm character handle-centre correction is evidence only;
- re-solve against the accepted hand and current full exercise library;
- keep wrist, exercise motion, equipment transforms and canonical hierarchy fixed;
- no automatic promotion.

## Phase D — appearance

Entry:
- accepted geometry source named/hashed.

Use:
- `PHASE_D_SKIN_MATERIAL_PLAN.md`
- `MAKE_PHASE_D_SKIN_SWEEP.bat <candidate_version>`

Prepared sweep:
- roughness 0.50 / 0.58 / 0.64;
- metallic 0;
- warm tone in `COLOR_0`;
- proven curvature modulation;
- binary/JSON invariant checking;
- paired bare/dressed output.

Choose appearance visually; do not make material compensate for geometry.

## Phase E — shoulder/axilla topology

Entry:
- accepted hand and body source.

Use:
- `PHASE_E_SHOULDER_TOPOLOGY_PLAN.md`

Blender work:
- connected deformation-ready deltoid/pec/lat/axilla/scapular topology;
- no joint changes;
- no scapular rhythm yet;
- full current exercise close-up review.

## Phase F — final source-rig deform setup

Entry:
- all geometry accepted.

Use:
- `PHASE_F_FINAL_BINDING_PLAN.md`
- `AUDIT_PHASE_F_SOURCE_RIG.bat reference.glb candidate.glb`
- `VALIDATE_PHASE_F_RUNTIME.bat reference.glb candidate.glb label`

Correct model:
- source rig remains the skin skeleton;
- canonical 63-bone rig remains the driver;
- preserve source helpers/twist structure;
- repair/add source-side palm/metacarpal and scapula deform controls only where
  needed for plausible canonical mapping;
- prove zero-state/rest equivalence.

## Phase G — activate dormant movement capability

Entry:
- Phase F mapping/weights accepted.

Use:
- `PHASE_G_MOVEMENT_ACTIVATION_PLAN.md`

Order:
1. palm cupping;
2. thumb opposition/twist;
3. scapular rhythm.

Rules:
- feature-by-feature revert points;
- family/biomechanics-driven, not exercise-ID hacks;
- zero-feature state reproduces Phase F baseline;
- full library validation after each slice.

## Phase H — prompt generation

Entry:
- final character and motion system stable.

Use:
- `PHASE_H_SELF_SUFFICIENT_GENERATION_PLAN.md`
- `PROMPT_FAMILY_CERTIFICATION_MANIFEST.json`
- `PROMPT_FAMILY_CERTIFICATION_MATRIX.md`
- `PROMPT_FAMILY_CERTIFICATION_TEMPLATE.md`
- `AUDIT_PROMPT_GENERATION_COVERAGE.bat`
- `START_PROMPT_FAMILY_CERTIFICATION.bat <family>`

Current source state when prepared:
- 16 movement families;
- 28 exercises;
- 4 certified prompt families: curl, overhead press, squat, lunge;
- 12 remaining.

Planned remaining order:
1. hinge
2. row
3. raise
4. calf
5. horizontal press
6. supine
7. trunk flexion
8. extension
9. vertical pull
10. carry
11. anti-rotation
12. rotation

Every family must:
- reproduce its existing library proving set;
- expose only real typed variant fields;
- derive correction levers from measured failures;
- include negative/refusal tests;
- render automatic review views;
- pass final-character validation;
- keep previous certified prompts deterministic.

## Final release proof

Use:
`RUN_FINAL_SYSTEM_ACCEPTANCE.bat final_character.glb`

See:
`FINAL_SYSTEM_ACCEPTANCE_PLAN.md`

For a full release it requires:
- all 16 current families certified;
- source suite clean;
- final-character source suite clean;
- typecheck clean;
- build clean;
- prompt parse/generate tests clean;
- character collision/contact/retarget gates clean;
- certification manifest/source registry consistent.

The output records the exact source HEAD and final character SHA-256.

## What remains genuinely manual/judgement-based

Even with all prepared automation, these should not be silently guessed:
- whether a rebuilt hand actually looks anatomically convincing;
- whether final skin/material appearance is acceptable;
- whether shoulder/axilla deformation looks natural in difficult poses;
- whether final palm/scapula weights deform plausibly;
- whether a newly certified generated family looks like the intended exercise.

The software can narrow these decisions with metrics, comparisons and automatic
review packs, but green tests alone should not promote visual anatomy.


## Prepared-tooling self-check

At any phase, before spending substantial Work/Blender usage, run:

`CHECK_PREPARED_TOOLING.bat`

It statically compiles every Python helper and verifies the authoritative roadmap/phase/launcher files plus the 16-family / 28-exercise certification manifest. It does not require Blender, Node modules or network access and does not modify candidates.


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
