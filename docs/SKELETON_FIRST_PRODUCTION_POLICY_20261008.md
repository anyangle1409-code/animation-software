# Skeleton-first production policy — 2026-10-08

Owner decision: the anatomical skeleton is the source of truth for production proportions. The production mesh/skin must be refit around the validated skeletal target, not the other way round.

## Consequences

- The current a003 fit remains a diagnostic/audit baseline showing how the r95 body differs from the anatomical target.
- Do not preserve the r95 short forearm/hand or long-foot proportions merely because the current mesh has them.
- Do not move validated joint centres to accommodate the current mesh.
- Do not edit production geometry, weights, or runtime rig until the canonical target skeleton proportions are frozen and Gates 6–9 permit downstream work.
- Mesh reconstruction should proceed from: validated skeleton proportions -> joint centres/axes -> muscle/soft-tissue volumes -> skin/mesh -> runtime rig.
- Character styling may alter muscularity, breadth, fat/soft-tissue thickness and surface shape, but must not force implausible bone lengths or joint locations.

## Safe work before local production editing

1. Build a canonical proportion target table for the intended adult male using multiple independent anthropometric sources and open musculoskeletal models.
2. Define target long-bone, hand and foot segment ranges with source/context/confidence, avoiding a single-population mean as a hard target.
3. Compare the target skeleton to a003 and quantify required mesh changes separately from skeletal changes.
4. Continue Phase 8/9 follower and isolated-motion research/tests where defensible source magnitudes are available.
5. Prepare a production refit plan and acceptance tests, but do not alter the production mesh yet.

## Current known body-shape deviations from the audit

- Forearm/hand are short relative to stature-conditioned ANSUR comparison.
- Feet are long relative to the same comparison.
- Shoulders are broad.
- These are authored surface proportions, not evidence that the validated joint centres should be moved to match them.

The exact final target proportions must be selected from a plausible human range and verified across several sources rather than forced to the population mean.

## Owner decision, 8 October 2026: proportions

**The canonical skeleton uses normal anatomical proportions for a 1.82 m adult male, and the body mesh is refitted to it.** The authored r95 forearm-hand shortness, long feet and broad shoulders are not intended styling and must not constrain canonical bone lengths. Agreement with the r95 surface is therefore no longer sufficient corroboration for a canonical length: targets come from stature-conditioned anatomical evidence with matched endpoint definitions.

This answers the F-PROP-001 owner question. The decision is recorded as `owner_decisions` in `canonical_target_selection_v1.json` and `canonical_freeze_readiness_v1.json`, and is tested by `scripts/test_owner_proportion_policy_and_source_fixes.py`. No numeric target was selected and `freeze_ready` stays false.

**Restated by the owner, 8 October 2026:** the skeleton is to be accurate as a standard male, and the mesh is to work around it. **Once a skeleton element is confirmed correct, it is never changed to suit the mesh.** The mesh, weights and deformation adapt to the skeleton. A confirmed element may change only on new anatomical evidence, never because of mesh fit, skin clearance or deformation problems. This is recorded as `skeleton_precedence` in `owner_decisions`.
