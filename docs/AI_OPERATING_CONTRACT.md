# AI operating contract

This contract applies equally to GPT, Claude, Codex, and any future AI agent working on Home Gym PT.

## Shared goal

Produce a high-quality, self-sufficient Home Gym PT exercise-animation system whose distributable runtime and production creative assets are first-party, while preserving biomechanical correctness and user-visible behaviour through the migration.

## Working method

Use the same sequence for every material change:

1. read the current authority and exact task;
2. establish the current executable baseline;
3. define or identify measurable acceptance criteria;
4. make the smallest reversible change;
5. run focused tests;
6. run typecheck/build where relevant;
7. run the required standalone/provenance gates;
8. preserve evidence;
9. commit one coherent checkpoint;
10. update `docs/CURRENT_HANDOFF.md` only with verified state.

Never substitute model confidence for evidence.

## Reference taxonomy

### Permitted production inputs

- project-authored source and numerical specifications;
- project-owned canonical hierarchy, semantics, algorithms, tests, and acceptance data;
- independently authored ORIGINAL v1 geometry/weights/materials;
- generic anatomical and biomechanical knowledge expressed independently;
- project-authored equipment primitives and exercise definitions after provenance gates.

### Reference-only

- V5-V15f and CORNER_FINAL lineage;
- old imported/high-detail characters;
- historical renders and rejected candidates;
- MakeHuman-derived body data;
- old handoff/review material.

Reference-only material may inform abstract failure examples or explicitly authorised measurements. It must not be copied into production.

### Prohibited production transfer

Do not copy or transfer from legacy/third-party-derived sources:

- vertices, faces, topology, UVs;
- skin weights, bind matrices, morph targets;
- textures/materials;
- source-rig numerical rest transforms derived from imported characters;
- nearest-surface/nearest-vertex projection;
- shrink-wrap reconstruction or retopology driven by the legacy surface.

## Quality stack

A change is not complete merely because it looks better. Evaluate, where applicable:

1. provenance;
2. structural correctness;
3. biomechanics/contact;
4. deformation;
5. visual anatomy;
6. motion continuity;
7. runtime/export parity;
8. standalone/release compliance.

## Behaviour preservation

Do not change exercise mechanics, joint limits, contacts, or generation semantics merely to make a replacement renderer or mesh pass. Fix the replacement.

Do not relax thresholds, remove tests, increase timeouts, or add allowlist exceptions merely to turn a failure green. Any legitimate gate change needs an explicit evidence-backed decision recorded in `docs/DECISION_LOG.md`.

## Handoff format

At the end of a work increment record:

- start state;
- end state/commit;
- task;
- authoritative inputs;
- files changed;
- files deliberately not changed;
- tests/gates run and exact results;
- renders/evidence produced;
- decisions made;
- open failures;
- next exact task;
- prohibited next actions.

The next agent should not need to re-audit project history.

## Stop conditions

Stop the affected task and record the conflict instead of guessing if:

- provenance is unclear;
- a step would copy prohibited legacy data;
- required parity cannot be demonstrated;
- a supposedly current instruction conflicts with a higher-authority file;
- a dependency can only be removed by breaking behaviour or weakening a gate.

## Model independence

Do not introduce GPT-specific or Claude-specific project rules. Both agents use the same repository authority, references, acceptance criteria, tests, and handoff format.
