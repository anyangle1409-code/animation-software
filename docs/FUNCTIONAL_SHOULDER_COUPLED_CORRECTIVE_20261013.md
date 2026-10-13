# W2: pose-space shoulder correctives solved against the coupled motion — provisional

- **Branch:** `claude/functional-shoulder-coupled-corrective-20261013`.
- **Base:** stacked on draft PR #111 `13cea5a5`, whose exact-head CI is green on all three checks. PR #111 is itself on the reviewed PR110 head `26bf25f0`.
- **This step** is the exact next action recorded in PR #111: correctives against the coupled 0–160 motion.
- **Untouched:**
  - PR110's motion, PR111's guides and axial channel, F-SIDE-001, and the 206-bone source, which stays at rest;
  - the source blend (`670a37bf…cbbe56`) and its weights, legacy keys and rigs;
  - Lane G code and GLBs, PR68's views, control map, samples and limits, and Claude's unaccepted C3 foot candidate.

**Scope:** an engineering diagnostic candidate only. It is not muscle or tissue simulation. There is **no anatomy, deformation, GLB, clinical or production approval**.

## Method

All code is in `scripts/build_functional_shoulder_corrective_blender.py` (Blender) and `scripts/anatomy_fit/functional_coupled_corrective.py` (pure contract).

**Exact inverse.**
- The body uses plain linear-blend skinning: normalized weights, at most 4 influences, shape keys applied before skinning.
- A posed-space target therefore maps exactly to a rest-space shape-key delta through each vertex's inverse blended matrix.
- The inverse is checked against Blender's own evaluation at every key (max error 8.4e-7 m).

**Keys.**
- 7 keys at 100, 110, …, 160° humerothoracic elevation, each warm-started from the previous solved shape.
- Activation is a piecewise-linear hat per key. Every key is 0 at and below 90°, where the coupled pose has no collapse or self-intersection. Each key is exact at its own pose.
- In-between poses are blends, measured every 5° rather than assumed correct.

**Posed-space relaxation** acts only in the failing zones: faces with area ratio < 0.5 or > 2.5, plus intersecting faces, dilated by 6 rings with a smooth falloff. Each iteration:
1. Edge-length springs pull compressed or stretched edges towards their rest lengths, and a volume-pressure term restores the rest body volume.
2. Light fairing keeps the surface smooth.
3. Averaged face separation is applied to self-intersecting pairs.
4. Torso-dominant skin that has sunk inside the static rib guides is pushed out to 3 mm, through a smoothed displacement field.

The solve stops only when pairs, rib push and collapse are all zero, or after 300 iterations.

**Symmetry.** Deltas are mirrored, with a mirror-map error of 3.7e-7 m.

## Rejected variants (measured, recorded so they are not repeated)

| Variant | Outcome at 160° unless stated |
|---|---|
| Taubin smoothing + summed face pushes | Unstable: 444 pairs grew to 668 |
| Plain Laplacian | Unfolds buckles (444 → 134 pairs) but volume falls to −11% and 420 faces collapse |
| Independent 120/160 keys with a linear blend | 480–990 pairs between the keys |
| Per-vertex rib push without field smoothing | Saw-tooth chest profile along the ribs (visible in the 140° side view) |
| Stop criterion without collapse | 120° key stopped with 18 collapsed faces |
| Skin-weight diffusion in the fold zone, uncorrected motion (`scripts/diagnose_shoulder_weight_diffusion_blender.py`) | 140° pairs fall 132 → 54–70, but 160° is unchanged (418–456) and collapse and volume get worse |

## Result (original 17,946-vertex male, 7,406-face shoulder region)

Each cell gives the value without → with the correctives.

| Elevation | Faces < 0.1 | Self-intersecting pairs | Body volume Δ % | Stretched > 2 | Torso skin to rib guides (min, mm) |
|---|---|---|---|---|---|
| 0 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | 7.2 → 7.2 |
| 90 | 0 → 0 | 0 → 0 | 1.82 → 1.82 | 310 → 310 | −45.4 → −45.4 (keys inactive) |
| 100 | 0 → 0 | 0 → 0 | 0.84 → −0.08 | 366 → 268 | −45.8 → **7.3** |
| 110 | 2 → 0 | 0 → 0 | −0.27 → −0.15 | 408 → 282 | −46.2 → **5.5** |
| 120 | 2 → 0 | 0 → 0 | −1.43 → −0.12 | 424 → 212 | −46.5 → **7.3** |
| 130 | 16 → 0 | 2 → **82** | −2.55 → −0.10 | 444 → 196 | −46.8 → **5.8** |
| 140 | 40 → 0 | 132 → **182** | −3.56 → −0.10 | 432 → 186 | −46.9 → **5.3** |
| 145 | 48 → 0 | 176 → **604** | −4.00 → 0.17 | 428 → 296 | −47.0 → **4.7** |
| 150 | 38 → 2 | 432 → 224 | −4.39 → −0.12 | 420 → 182 | −47.0 → **4.3** |
| 160 | 42 → 6 | 444 → **236** | −5.01 → −0.13 | 400 → 196 | −47.1 → **4.0** |

The full 5° table (0–160) is in the manifest.

**Met everywhere from 100° up:**
- body volume within ±0.17% (target ±2%);
- torso skin outside the ribs by at least 4 mm (target 3 mm);
- collapse no worse than without correctives, and ≤ 6 faces;
- stretch roughly halved.

**Not met — self-intersection.**
- It is 0 up to 120° and better than without correctives at 150–160°.
- It is **worse at 125–145°** (82–604 pairs, against 2–176), in the blend between keys.
- The diagnosis (`w_pairs` analysis): these are **local buckles of the shoulder-top skin** (rest z 1.41–1.55 m, |x| 0.15–0.28 m; faces 1–12 edges apart in the upper-arm/clavicle/scapula zones), not axilla contact. Linear-blend skinning compresses that skin during a 160° swing about the glenohumeral centre.

**Visible:**
- the chest and flank no longer sink or saw-tooth;
- shoulder-top folds persist at 140–160° (front and rear);
- a small dorsal notch remains on the 140° side profile;
- the sternal "V" crease is inherited from the base mesh.

## Blocker and exact next action

Removing the shoulder-top buckle needs either:
- a **shoulder-top helper deformer** (for example a deltoid/acromion bone driven at a fraction of humeral elevation, with fold-zone weights transferred to it); or
- a different skinning scheme.

Both change the **67-joint runtime contract** consumed by Lane G (GPU palette, GLB) and by PR68's six-control map. That contract change needs owner and Lane G agreement. It is not done here.

Until then, the safe W action is:
1. denser keys between 120° and 160° (5° spacing);
2. a monotone-blend check that rejects any key whose blended neighbours add pairs.

## Evidence and tests

- **Tests:** 7 pure (contract) tests and 6 native Blender 5.2.1 tests pass. The native tests cover:
  - exact inverse and mirror;
  - no effect at 0/90°;
  - volume, collapse and rib improvement at every key;
  - self-intersection recorded, not gated;
  - source at rest, single driver, legacy keys at 0;
  - fail-before-mutation.

  PR111's 9 and PR110's 6 native tests still pass, and the pure plus inherited suite passes.
- **Private evidence:** nine 900 px shoulder views (front/side/rear at 120, 140 and 160°; 0/90° are unchanged and not rerendered) plus a manifest, SHA-256 `78a5cf14cbb0bc1bc5707ea9028fe408fb438b0c228b691e3725ec945e3077a1`.
- **CI:** produces the same as an artifact. The correctives are in-memory shape keys rebuilt deterministically on each run; nothing binary is committed.
