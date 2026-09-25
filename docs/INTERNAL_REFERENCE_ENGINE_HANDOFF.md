# Internal Reference Engine — handoff

## Source snapshot

Planning branch created from:

- repository: `anyangle1409-code/animation-software`
- source branch: `chatgpt/absolute-retarget-imports`
- source HEAD at handoff: `8ec5247f9a5ef53dd023b3ebb7dd26339fac3060`
- planning branch: `work/internal-reference-engine-plan-20260925`

This branch is intentionally planning-only. It does not change rigging, exercise mechanics, family builders, generator behaviour, assets or production references.

## Current generator state at the snapshot

Prompt generation already has a vertical slice:

```
typed request
 -> ExerciseIntent
 -> certified family adapter
 -> family builder
 -> ExerciseDefinition
 -> clip
 -> 13-check validation
 -> bounded correction
 -> studio candidate
```

Prompt-certified families at this snapshot:

- curl
- overhead press
- squat
- lunge

Existing library:
- 28 exercise definitions
- suite reported by current source work: 868 passed / 1 skipped

The next generator family planned separately is hinge, followed by row.

## New strategic requirement

Make exercise verification stand-alone and independent of third-party services.

Do not solve this by making the generator compare against itself.

Add a separate Internal Reference Engine that owns versioned biomechanical reference envelopes and automatic review evidence.

Read:

1. `docs/INTERNAL_REFERENCE_ENGINE_PLAN.md`
2. `docs/reference/README.md`
3. `docs/reference/REFERENCE_SPEC_EXAMPLE.json`

## First implementation slice

Do not attempt the whole plan at once.

Recommended first code task:

**R0 + R1: reference contract and curl evaluator**

1. Add `src/reference/types.ts`.
2. Add a versioned local reference library.
3. Add the first independent curl reference.
4. Sample a candidate clip over normalized time.
5. Evaluate:
   - elbow ROM
   - upper-arm movement
   - forearm orientation by grip
   - wrist neutrality
   - torso movement
   - dumbbell path
   - symmetry
   - phase timing
6. Produce an explainable report with measured candidate value, allowed envelope and failure amount.
7. Prove accepted curl variants pass.
8. Add deliberately perturbed test candidates and prove the intended checks fail.
9. Do not connect corrections until the evaluator itself is trustworthy.

## Then

After R1 is proven:

- R2 automatic camera/render capture
- R3 deterministic visual/silhouette QA
- R4 connection to existing bounded correction
- expand references across prompt-certified families
- later add a locally rendered reference mannequin
- local vision is optional and comes last

## Protection rules

Do not:
- alter existing exercise definitions just to make reference checks pass;
- loosen validation limits;
- use family-builder outputs as reference truth;
- require network access;
- require YouTube or an external AI API;
- modify production character assets;
- change the frozen 63-bone hierarchy;
- couple reference-version changes to generator-version changes.

Any implementation should report whether all existing library clips remain unchanged.
