# Historical 55-bone shoulder baseline

**Superseded by `RIG_63_FREEZE.md` / `hgpt_canonical_v3` at `19ca602`. Retained for provenance only.**


The canonical shoulder-girdle structure is now confirmed.

- Source branch: `chatgpt/absolute-retarget-imports`
- Mirror branch: `claude/home-gym-pt-animation-txux66`
- Exact commit: `c2372c16ad4b7a0763a4cfdf9a0da6a23c3524f2`
- Canonical bones: **55**
- New bones: `scapula_l`, `scapula_r`
- Hierarchy: clavicle -> scapula -> upper arm
- Scapula default: neutral/rest
- Scapular rhythm: **off**
- Scapula weights: **none yet**
- Upper-arm limits: unchanged
- Export skeleton ID: `hgpt_canonical_v2`

Both named branches were verified at this exact commit.

## Equivalence accepted

With the scapulae resting, the new canonical rig reproduces the old 53-bone result to numerical rounding across all seven current exercises.

Recorded evidence from the committed change:
- canonical frame comparison: 436,394 values, worst 2.7e-15
- production character bones/hand/grip frames: worst 5.4e-15
- production character posed vertices: worst 1.8e-15 m
- procedural mannequin posed vertices: worst 1.8e-15 m
- contacts and technique results: identical
- retarget flattened-hierarchy certification including clavicle: 0.0000 degrees / 0.0000 mm
- suite: 388 passed / 1 skipped, 48 files
- typecheck/build: clean

The 53-bone test rig reconstructed from the new definitions reproduces the old baseline bit-for-bit.

## Important mesh implication

The commit changes source/runtime rig logic and tests; it does **not** modify a production GLB/Blend asset and it does **not** paint scapula weights.

Therefore the current V6 high-detail character does not need to be thrown away or immediately rebound simply because the canonical runtime rig became 55 bones. The new retargeter intentionally walks through the unmapped scapulae and preserves the current production character motion.

For mesh work:
- knee retopology can continue
- skin/material work can continue
- shoulder/back/chest/armpit **topology and geometry planning can now use the confirmed scapula structure**
- final scapula deformation still needs a character-asset binding/weight pass that actually introduces/uses scapula deform influences
- hand geometry may continue, but final hand weights must wait for the palm-arch/thumb-twist decision

## Still not frozen by this commit

This commit settles the shoulder girdle only. It deliberately does not settle:
- palm-arch / hand-base bone decision
- thumb-twist decision
- scapulohumeral rhythm
- scapula skin weights
- reduced shoulder-joint-only upper-arm elevation limits

Forearm twist distribution/carrying-angle choices are not changed by this commit; do not infer that they were settled unless a later source commit explicitly records that decision.

## Validation rule from now on

New mesh candidates should be validated against this exact 55-bone source commit, not only against the older frozen validation snapshot. The laptop automation prepares an isolated `validation_55` source tree from this commit without merging it into the mesh-review branch.
