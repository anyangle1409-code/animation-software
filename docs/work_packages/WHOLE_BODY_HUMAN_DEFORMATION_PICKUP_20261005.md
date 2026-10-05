# Laptop pickup — whole-body human deformation recovery

**Date:** 2026-10-05  
**Purpose:** Resume Blender recovery without losing the new whole-body human movement and anatomical-coupling requirements.

## First rule

Do not start by editing the model.

1. Check the live remote HEAD of `codex/whole-body-deformation-recovery-20261004`.
2. If the laptop Work session has uncommitted/unpushed work, preserve it and push a
   clean checkpoint first.
3. Fetch `gpt/shoulder-layer-diagnostic-20261004`.
4. Compare the live Work branch against the GPT branch before integrating.
5. Preserve every newer Blender/model/evidence change from Work. Do not reset,
   rebase, force-push or replace a newer candidate.

The GPT branch is a documentation/evidence/diagnostic package built from Work's
last pushed recovery checkpoint. It is not permission to overwrite newer local
model work.

## New governing body authority

Read in this order:

1. `docs/ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.md`
2. `docs/ORIGINAL_V1_ANATOMICAL_COUPLING_CONTRACT.md`
3. `ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json`
4. `ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json`
5. `ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json`
6. `ORIGINAL_V1_HUMAN_BODY_COVERAGE_MATRIX.json`
7. `ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json`
8. `docs/ORIGINAL_V1_WHOLE_BODY_RECOVERY_20261004.md`

Historical Phase 4/r95 evidence remains immutable history. It is not current
anatomical acceptance.

## Non-negotiable deformation rule

When one body segment moves, every anatomically connected muscle/soft-tissue
system that should respond must respond coherently.

For multi-anchor tissue:

- do not assign the whole surface to one moving bone;
- preserve both/all attachment neighborhoods;
- prove weights-only deformation before fitting corrective keys;
- inspect intermediate and return motion;
- prove lengthening/compression, volume redistribution, folds/creases,
  bilateral consistency and load propagation;
- a corrective may refine a good foundation but may not conceal a bad one.

This applies to the entire body, not only the shoulder.

## Consolidated repo gate

After integrating the audit package:

```bat
RUN_ORIGINAL_V1_HUMAN_BODY_GATES.bat
```

It validates the human-evidence database, master plan, movement sweeps,
anatomical-coupling coverage and associated tests.

## Immediate shoulder/chest/axilla execution

r95 remains the immutable comparator.

### A. Run the read-only layer diagnostic

Use the exact r95 Blend:

```bat
RUN_ORIGINAL_V1_SHOULDER_LAYER_DIAGNOSTIC.bat <exact-r95.blend> r95_foundation_pickup press_top,pullup_hang 13
```

Do not save the r95 source.

The diagnostic separates:

- weights-only;
- abduction corrective;
- flexion corrective;
- scapular corrective;
- combined corrected surface;

and records per-zone movement in the shoulder, anterior axilla, posterior axilla
and lateral chest root.

### B. Assess the first four coupling systems

Before editing, create a fresh candidate-bound coupling evidence file from:

`ORIGINAL_V1_ANATOMICAL_COUPLING_EVIDENCE_TEMPLATE.json`

The first systems are:

- `CP-PEC-AX-002` — pectoralis/anterior axilla;
- `CP-POSTAX-003` — lat/teres/posterior axilla;
- `CP-DELTOID-004` — deltoid shoulder yoke;
- `CP-NECK-TRAP-001` — neck/trapezius/shoulder girdle.

Use the diagnostic plus real-human evidence to identify where weights-only
ownership first becomes implausible.

### C. Declare the repair scope before editing

The declaration must name:

- exact parent candidate SHA;
- left-owned vertex IDs and exact mirror rule;
- bones/weight groups allowed to change;
- whether topology is permitted to change;
- target coupling systems;
- expected human behaviour;
- protected neighboring regions;
- unchanged rig/pose/baseline/gate identities.

Do not declare a broad "shoulder fix". Use the smallest mechanically justified
support/ownership zone.

### D. Create a NEW candidate

Never overwrite r95.

Repair sequence:

1. weights/support first;
2. render/measure weights-only elevation arc;
3. verify anterior/posterior axillary folds, chest root and deltoid transition;
4. reject the candidate if weights-only still needs a corrective to hide a
   membrane/trench/wing;
5. only after foundation plausibility, fit/refit generic motion-driven
   correctives;
6. run full visual/numerical/symmetry/contact/whole-body regressions;
7. populate the coupling evidence file;
8. update the whole-body issue ledger.

## What counts as success for the shoulder recovery

Not "edge ratios pass."

Not "the top press image looks better."

The shoulder recovery is successful only when:

- pec remains chest-rooted while the humeral insertion follows the arm;
- anterior axillary fold changes naturally through elevation;
- posterior fold remains supported by lat/teres/trunk and humeral sides;
- deltoid remains connected to clavicle/acromion/scapular spine and humerus;
- trapezius/scapular surface changes coherently with girdle motion;
- weights-only deformation is already plausible;
- no membrane, trench, wing, spherical cap, detached flap or abrupt arm pinch;
- both sides behave equivalently under symmetric inputs;
- intermediate and return frames are clean;
- all existing contact and regression gates remain valid.

## Do not move to high-detail anatomy yet

Master Stage 5 / historical Phase 5 stays blocked until the whole-body foundation
and movement/evidence gates are explicitly cleared.

Do not use clothing, materials, lighting or sculpt detail to hide an unresolved
deformation problem.

## Broader continuation

After the shoulder foundation is repaired, continue Master Stage 1 system by
system using `ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json`.

The project must ultimately prove all fourteen coupling systems, all twelve body
regions and all twenty-seven movement families before the body can be treated as
generally human-like.

Production approval remains **NO**.
