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

## IND3 to F5: Option 5 male target (3 Nov, owner chose "1: start the independent model")

**Pipeline** (all first-party scripts, on our own W12c mesh; the basis and all 149 movement keys are edited together):

1. `rest_taubin_smooth_blender.py`: Taubin smoothing of the rest surface, with the head, hands and feet masked out.
2. `section_fit_blender.py`: fit to the Option 5 male (MPFB v8) section statistics, scaled to 1856 mm.
3. `anatomy_relief_blender.py`: a port of the procedural definition pass. It is written, but not yet judged on this mesh.

**Results (stand pose):**

| Run | Change | Self-intersections | Edges > 35° | Verdict |
|---|---|---|---|---|
| W12c | none | 2 | 363 | Lumpy surface (upper back, upper arms, thighs) |
| IND3 | fit only, clamp 0.8–1.3 | 960 | 402 | Rejected: amplified the lumps and caused shoulder/hip collisions |
| T4 | Taubin 40 | 2 | 103 | Fine crinkles gone |
| T5 | Taubin 300 | 2 | 100 | Cleaner; banding on the arms and thighs remains |
| T6 | Taubin 1500 | 295 | 1293 | Rejected: the smoothing went unstable on the stitched mesh |
| F5 | T5 + fit, clamp 0.85–1.2 | 159 (shoulder) | 108 | Best so far, but still a boxy shoulder top, back lumps and arm banding |

**Voxel remesh into one clean surface** (`remesh_review_blender.py`): failed. The stitched mesh overlaps itself internally, so the remesh made a lace-like double shell.

**Finding:** the W12c base, a patchwork of many patch passes, limits what procedural passes can do. See `IND_F5_progress.jpg`. **Not approved.**
