# Model round 3 — pec shape and deltoid/clavicle transition

**Branch:** `chatgpt/absolute-retarget-imports`
**Executed from:** `f6ca1d6`
**One controlled candidate. Round-2 fixes retained. Upper body NOT frozen. Not merged.**

Two changes only: pec shape, and the side-view deltoid cap / clavicle transition. Abs and lower
torso, back and lat width, skin material, face, hair, rig, weights and curl mechanics are all
untouched. Skin tone and curvature shading were regenerated from the new geometry with identical
parameters, so the shading matches the new surface rather than the old one.

## What the measurements said to fix

- **Outer pec collapsed in depth**: 105 mm forward at y 1.43 falling to **61 mm at y 1.40** — a
  44 mm drop over 30 mm of height, so the chest fell away instead of rounding.
- **Upper/outer pec was dished, not domed**: relief ran from −4.5 mm concave to only +1.6 mm convex.
- **The clavicle junction stood +7.9 mm proud** at x 0.101, y 1.620, with a second +6.2 mm ridge on
  the rear deltoid — that pair is the shelf.
- **The cap apex sat 55 mm behind centre** (z −0.055).

## What changed

| Stage | Operation | Extent |
|---|---|---|
| 4 | Two low `cos²` domes of forward depth on the pec — upper/outer and lower/outer — then the boundary contour eased | 150 points domed, max **8.50 mm** forward; 148 eased |
| 5 | Cap tilted to walk the apex forward, **y only**; clavicle/deltoid junction relaxed | 203 points per side, max 11.95 mm; 560 points softened |

Largest single vertex move 11.56 mm over 898 points. The domes use a `cos²` profile, which is zero
in both value *and* slope at the rim, so no ring edge appears where they fade out. Depth (z) only
for the pec, so the ribcage half-width cannot move.

## Results

| Target | Before | After |
|---|---:|---:|
| Outer pec depth, y 1.40 | 61 mm | **67 mm** |
| Outer pec depth, y 1.46 | 104 mm | **107 mm** |
| Outer pec depth, y 1.49 | 93 mm | **101 mm** |
| Outer pec depth, y 1.52 | 91 mm | **95 mm** |
| Sharpest clavicle/deltoid ridge | **7.91 mm** | **4.38 mm** |
| Cap apex position | z −0.055 | **z −0.040** (15 mm more centred) |
| Cap silhouette radius, matched at z −0.055 | 128.4 mm | **205.4 mm** |

Inner and mid pec columns are unchanged (138 / 115 mm at y 1.40), so the sternum is untouched and
the new fullness is where it was missing.

### Guards — the things this round had to not break

| Guard | Before | After |
|---|---:|---:|
| Ribcage max half-width (y 1.34–1.52) | 218.7 mm | **218.7 mm** |
| Waist half-width (y 1.26–1.30) | 150.3 mm | **150.3 mm** |
| Half-width profile at y 1.28 / 1.32 / 1.48 | 150.3 / 167.8 / 218.7 | identical |
| Shoulder span (x bounds) | −0.8833..0.8833 | identical |
| Phase A seams | 7 groups / 14 / 71.0° | identical |

So the ribcage is not wider and the round-2 V-taper is intact to the tenth of a millimetre.

## A measurement artefact that sent me the wrong way twice

The cap radius appeared to collapse from 128.4 to 93.3 mm, and I retuned twice trying to recover
it — narrowing the ridge mask, then replacing an S-curve tilt with a linear one.

The radius was never lost. The fit window follows the apex, so when the apex moved forward the
metric measured a **different patch of shoulder** — one that is naturally sharper. Fitting both
bodies over the *same* patch settles it:

| Fit centre | Round-2 baseline | This candidate |
|---|---:|---:|
| z = −0.055 | 128.4 mm | **205.4 mm** |
| z = −0.040 | 95.0 mm | 93.3 mm |

At matched locations the cap is substantially rounder, and the front of the cap measures ~95 mm in
both. Isolating the stages confirmed it further: stage 4 is radius-neutral, and the whole apparent
change belonged to stage 5's apex move.

Worth keeping the linear tilt anyway — a parabola plus a linear term has the same second
derivative, so it walks the apex without touching curvature by construction, which the S-curve did
not. But the wider ridge mask I had narrowed is restored, because on matched metrics it is clearly
better: radius 205.4 against 147.4, and the ridge 4.38 mm against 5.99.

## Validation — nothing locked moved

| Check | Result |
|---|---|
| Bare ↔ dressed grip solution / offsets | `homeGymPTMale`, (0.0174, 0.0452, 0.0083) — both |
| Bare ↔ dressed posed hand / body | **0.0000 mm** / **0 of 10,839** |
| Grip contacts, curl t = 2 | −0.46 / −0.36 / −0.22 / −0.11 mm, 0 inside; thumb +1.18; palm −2.54; wrap 252° |
| Renderer vs exporter | 0.0000 mm, all six samples |
| Thigh clearance, body only | +4.68 / +4.79 mm, 0 inside |
| Clothing closest approach | 1.97 mm, non-interpenetrating |
| `clothing` / `waistband` / `clothdebug` | all pass |

## Candidate assets

| Role | File | SHA-256 |
|---|---|---|
| Bare | `scratchpad/reference-fit/HomeGymPT_Male_PEC_FINAL.glb` | `2bff95a36a2a87397b532e86cadb6c7c6f4922116f0cf64b74bc0579b2f27807` |
| Dressed | `scratchpad/reference-fit/HomeGymPT_Male_PEC_FINAL_SHORTS.glb` | `5a40efa0110ec822451e8c4132b5fa266f2f5fcafd05370947a24a0c2a0187e4` |

Rollback chain, all intact: round 2 `da5b3c5e…dc1e003` / `cf6c09a5…9f804bd7`; skin
`d71b70bc…c18f2be` / `8d07100f…f08f27ca`; Phase A `b3dc70e1…89fdf09` / `71c5bdef…9fe42da9`;
production v8 `951c2c39…963ee0` / `cc728366…5722e3`.

## A judgement call for you

At a 205 mm silhouette radius the shoulder no longer reads as a shelf or a point — but it is
trading some **deltoid definition** for that roundness, and in the side close-up the cap is
smoother than the reference board's, where the deltoid still reads as a distinct mass. Reducing the
junction relaxation from 3 iterations to 2 lands at 147 mm, which keeps more of the muscle read
while still clearing the shelf. One parameter, either way.

## What remains

- The outer pec still steps from 67 mm at y 1.40 to 107 mm at y 1.43. The dome eased that fall-off
  but did not remove it; closing it fully means adding more depth than I was willing to add
  unreviewed.
- Pec fullness overall is up but still short of the board's, and going further is additive volume
  rather than shape correction.
- Abs and lower torso untouched by instruction; still needs a map or real sculpting.

## Status

Pec shape and shoulder transition done and validated, upper body deliberately **not frozen**.
Stopped for review. **Nothing promoted, nothing merged.**
