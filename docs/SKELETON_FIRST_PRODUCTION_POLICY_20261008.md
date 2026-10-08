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
