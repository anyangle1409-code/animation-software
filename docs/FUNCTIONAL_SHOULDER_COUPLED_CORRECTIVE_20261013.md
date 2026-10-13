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

**Forward check.**
- The body uses plain linear-blend skinning: normalized weights, at most 4 influences, shape keys applied before skinning.
- The per-vertex blended matrix reproduces Blender's own evaluation at every key (maximum error 9.7e-7 m).

**Keys.**
- 7 keys at 100, 110, …, 160° humerothoracic elevation, each warm-started from the previous solved shape.
- Activation is a piecewise-linear hat per key; every key is 0 at and below 90°.
- In-between poses are blends, measured every 5°.

**Posed-space relaxation** acts only in the failing zones (area ratio < 0.5 or > 2.5, plus intersecting faces, dilated by 6 rings):
1. Edge-length springs pull edges towards their rest lengths, and volume pressure restores the rest body volume.
2. Light fairing keeps the surface smooth.
3. Averaged face separation is applied to self-intersecting pairs.
4. Torso skin is pushed out to 3 mm outside a **closed convex thorax hull built from the rib guides**, through a smoothed displacement field. "Torso skin" means trunk- or girdle-dominant skin within the rib span; neck skin is excluded.

**Back to rest space** by **damped least squares**, `d = (AᵀA + 0.01 I)⁻¹ Aᵀ r`, with a hard **30 mm cap** on every rest delta.
- Near 160° some blended skin matrices are nearly singular: the smallest singular value is 0.43 at 100°, 0.024 at 140° and 0.0024 at 150°.
- An undamped inverse (the first local version, commit `69a2f344`, never pushed) stored rest deltas up to 4.1 m. Those exploded to 322–374 mm posed corrections between keys.

**Symmetry.** Deltas are mirrored (3.7e-7 m).

## Independent review (of local `69a2f344`) and what changed

| Finding | Severity | Status |
|---|---|---|
| Undamped inverse: metre-scale deltas, regression between keys | HIGH | Fixed: damped solve plus cap. Tests bound every stored delta and the posed correction at all 16 angles (≤ 30 mm). |
| Rib clearance used a horizontal sign heuristic: neck skin above rib 1 read as "inside the ribs", inflating −47 mm and +7 mm | HIGH | Fixed: signed distance to a closed hull, neck excluded, rib span only. **Real** uncorrected torso sinking is 8–17 mm. |
| Vacuous or weak native tests | MEDIUM | Replaced with bounds: deltas, posed correction, volume, hull clearance, neck exclusion, unmet-target consistency. |
| Doc inaccuracies (LBS error, "at least 4 mm", "stretch halved", stale docstring, no render at the worst pose) | MEDIUM | Fixed; 145° is now rendered. |
| Redundant world matrix in `add_keys`; legacy keys could leak | LOW | Fixed: transforms asserted identity; legacy keys forced to 0 in every corrective pose. |

## Rejected variants (measured, recorded so they are not repeated)

| Variant | Outcome |
|---|---|
| Taubin smoothing + summed face pushes | Unstable: 444 pairs grew to 668 |
| Plain Laplacian | Volume −11%; 420 faces collapsed |
| Independent 120/160 keys with a linear blend | 480–990 pairs between the keys |
| Per-vertex rib push without field smoothing | Saw-tooth chest profile |
| Stop criterion without collapse | 120° key stopped with collapse |
| Undamped inverse | Rest deltas up to 4.1 m |
| Weight diffusion in the fold zone (`scripts/diagnose_shoulder_weight_diffusion_blender.py`) | 160° pairs unchanged (418–456); collapse and volume worse |

## Result (original 17,946-vertex male, 7,406-face shoulder region, bounded correctives)

Each cell gives the value without → with the correctives.

| Elevation | Faces < 0.1 | Self-intersecting pairs | Body volume Δ % | Stretched > 2 | Torso skin to thorax hull (min, mm) |
|---|---|---|---|---|---|
| 0 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | 3.0 → 3.0 |
| 90 | 0 → 0 | 0 → 0 | 1.82 → 1.82 | 310 → 310 | −8.1 → −8.1 (keys inactive) |
| 100 | 0 → **4** | 0 → 0 | 0.84 → 0.54 | 366 → 272 | −10.0 → 2.9 |
| 120 | 2 → 2 | 0 → 2 | −1.43 → −0.61 | 424 → 346 | −13.3 → 2.8 |
| 130 | 16 → 12 | 2 → **70** | −2.55 → −1.03 | 444 → 364 | −14.7 → 2.8 |
| 145 | 48 → 28 | 176 → **226** | −4.00 → −1.45 | 428 → 358 | −16.1 → 2.8 |
| 150 | 38 → 30 | 432 → 438 | −4.39 → −1.49 | 420 → 352 | −16.4 → 2.8 |
| 160 | 42 → 30 | 444 → **512** | −5.01 → −1.46 | 400 → 348 | −16.6 → 2.8 |

The full 5° table is in the manifest.

**What the bounded correctives achieve:**
- body volume within ±1.5% from 100° up (target ±2%);
- torso skin about 2.8 mm outside the thorax hull instead of 8–17 mm inside (target 3 mm, nearly met);
- fewer collapsed faces from 130° up (e.g. 42 → 30 at 160°);
- moderately less stretch.

**What they do not achieve:**
- **Self-intersection is not reduced**: worse at 120–145° and at 160°.
- Collapse rises slightly at 100–115°.
- The relaxation asks for more than 30 mm at 788–1,127 vertices per key, so the cap clips it. The posed residual (requested minus achieved) reaches 66–84 mm.
- **Visible:**
  - dark crease wedges on the anterior and posterior chest wall beside ribs 3–5 at 120°, 145° and 160°;
  - shoulder-top folds persist.

**Conclusion: this is a diagnostic result, not a usable corrective.** Pose-space relaxation on the existing weights cannot remove the shoulder-top buckle. Near 145–160° the skinning matrices of that skin are nearly singular: LBS collapses it, so no rest-space delta of bounded size can restore it.

## Blocker and exact next action

**Blocker:** the shoulder-top and axilla skin needs **different skinning, not more correctives**. Either option below changes the **67-joint runtime contract** consumed by Lane G (GPU palette, GLB) and by PR68's six-control map, and needs owner and Lane G agreement:
- a helper deformer, e.g. a deltoid/acromion bone driven at a fraction of humeral elevation, with fold-zone weights moved onto it; or
- a skinning change.

**Safe W actions meanwhile:**
1. a weights-only refit of the shoulder-top and axilla skin onto the existing clavicle and scapula controls, so the blended matrices stay well-conditioned; measure the minimum singular value per vertex at 160° as the acceptance metric;
2. then re-run this corrective solve on the refitted weights.

## Evidence and tests

- **Tests:** 7 pure (contract) tests and 8 native Blender 5.2.1 tests pass. PR111's 9 and PR110's 6 native tests still pass.
- **Private evidence:** nine 900 px shoulder views (front/side/rear at 120°, 145° (the worst blend) and 160°) plus a manifest, SHA-256 `3ac71cbc8b16d67bc2115bdca9ef190ebed0e478208a4bf23f31fffb9b95b44d`.
- **CI:** produces the same as an artifact. The keys are in-memory and deterministic.
