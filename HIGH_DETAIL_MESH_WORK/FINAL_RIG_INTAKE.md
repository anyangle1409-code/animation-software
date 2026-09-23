# Final rig intake — superseded by canonical v3 freeze

The earlier 55-bone shoulder-girdle intake at `c2372c1` is retained as history only.

The current authoritative canonical structure is:

- commit: `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`
- skeleton ID: `hgpt_canonical_v3`
- canonical bones: 63
- hierarchy: structurally frozen
- metacarpals: four per hand added
- thumb base: `thumb_01` provides the CMC/opposition control; no extra thumb-base bone
- canonical twist bones: none
- scapular rhythm: off
- palm cupping/thumb twist: structurally available but not driven by exercises
- skin weights: unchanged
- tests: 418 passed / 1 skipped / 51 files
- typecheck/build: clean

Read `RIG_63_FREEZE.md` and `CURRENT_STATE.md` for the current source of truth.

The remaining issues do **not** reopen the skeleton:
1. mirrored-character hand-roll retargeting
2. correct production palm-bone export/binding if palm cupping is to deform the production mesh
3. mannequin hand-shape mismatch

Any final weighting/binding work should target `hgpt_canonical_v3` and preserve the frozen hierarchy.
