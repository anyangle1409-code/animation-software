# First-party model, pass IND2 (3 Nov 2026)

**What:** our own Body v2 mesh (W12c, our own topology, on the canonical skeleton), reshaped towards the owner-approved MPFB M13/M14 **proportions target**. Script: `scripts/body_v2/section_fit_blender.py`.

- **Method:** cross-section statistics only. Skin radius is measured from the trunk and each limb axis at 16 stations × 24 directions. Our mesh is scaled by the ratio, smoothed and clamped to 0.8–1.3, and faded at the region ends.
- **What was not copied:** no MPFB vertex or topology. The chest band is smoothed, because the pecs are to be sculpted.
- **Stand pose (W12c → IND2):**

| Measure | W12c | IND2 |
|---|---|---|
| Folds over 90° | 7 | 9 |
| Edges over 35° | 363 | 414 |
| Self-intersections | 2 | **164** |

  The jump in self-intersections is still to be located.
- **Status:** a first pass, **not approved**. The change is modest. The high, square shoulder top and the mannequin head remain, because the neck and upper trapezius are faded out on purpose (IND1 grew a collar there). The pecs and definition are still to be sculpted.
