# Canonical skeleton freeze — hgpt_canonical_v3

The canonical hierarchy is structurally frozen at **63 bones**.

- Source commit: `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`
- Source branches: `chatgpt/absolute-retarget-imports` and `claude/home-gym-pt-animation-txux66`
- Skeleton ID: `hgpt_canonical_v3`
- Test state: 418 passed / 1 skipped / 51 files
- Typecheck: clean
- Build: clean
- Skin weights: unchanged
- Scapular rhythm: off
- Palm cupping: off
- Thumb opposition/twist: available structurally but not driven by exercises

## Structural additions after v2

Eight metacarpal bones were added:
- metacarpal_index_l/r
- metacarpal_middle_l/r
- metacarpal_ring_l/r
- metacarpal_pinky_l/r

Each finger root now hangs from its matching metacarpal. The thumb remains a three-bone chain; `thumb_01` is the thumb metacarpal/CMC control and now has a measured axial opposition axis, so no extra thumb-base bone was required.

There are no canonical twist bones. The production character's forearm twist helper remains character-specific and keeps the locked 50% share.

## Freeze guarantee

`src/rig/frozen.test.ts` locks:
- every canonical bone name
- every parent
- every rest head/tail position to micrometre tolerance

Joint limits are intentionally not structurally frozen.

## Equivalence against v2

Against `c2372c1`:
- all 7 exercises: worst difference 5.6e-16
- contacts and technique checks: identical
- production character bones/grips: worst 1.3e-15
- production character surface: worst 1.3e-15 m
- mannequin surface: worst 1.3e-15 m
- equipment/arm-to-trunk clearance: unchanged to 0.01 mm
- exported playback: all 63 bones within 0.01 mm of the studio pose

Only finger-root export tracks changed as expected from the inserted metacarpals.

## Palm geometry

The production character's exported Rigify palm bones are not usable as canonical placement references: they are displaced roughly 207–213 mm from their own knuckles and carry no weights.

The canonical metacarpals were therefore derived from the known knuckles and standard adult metacarpal proportions scaled to the 187 mm hand:
- index 66.9 mm
- middle 64.0 mm
- ring 56.1 mm
- little 52.2 mm

All derived metacarpals lie inside the production hand skin.

## Fixed since the freeze

The pre-existing mirrored-character hand-roll retarget error was fixed in `614033b256d869230ea273522620467401b0bc71` without changing the frozen hierarchy. The production character now matches same-side hand orientation; curls measure about 0.72° residual roll and press/squat 0.00°.

## Remaining non-structural items

These do not reopen the hierarchy:
1. the curl grip should be re-fit/reviewed in the corrected hand frame; its widest finger-wrap gap changed from 36° to 66°
2. production palm bones must be re-exported/rebound correctly if visible palm cupping is wanted on that asset
3. mannequin hand shape does not fully agree with the canonical knuckle geometry

Treat the hierarchy as frozen. Future issues should be solved in retargeting, weighting, deformation, solvers or asset binding, not by adding more canonical bones.
