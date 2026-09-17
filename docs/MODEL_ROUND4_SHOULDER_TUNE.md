# Model round 4 — shoulder junction tuned to 147 mm

**Branch:** `chatgpt/absolute-retarget-imports`
**Executed from:** `905dbfb`
**Candidate only. Pec and torso improvements retained. Not merged.**

One change retained: the shoulder junction relaxation is dialled back so the cap silhouette
measures **147.4 mm** instead of 205.4 mm — rounded, with the deltoid still reading as a mass.
The second half of the request turned out not to be a defect; that is explained below with the
measurement.

Untouched: armpit, abs and lower torso, back and lat width, skin material, rig, weights, curl
mechanics. Skin tone and curvature shading regenerated from the new geometry with identical
parameters.

## Correction to what I told you last round

I said "reducing the junction relaxation from 3 iterations to 2 lands at 147 mm". **That was
wrong.** 147 mm was the *narrow* ridge mask (reach x 0.19) at 2 iterations. With the wide mask I
had retained, dropping to 2 iterations goes the other way:

| Ridge mask reach | Iterations | Cap radius (fitted at z −0.055) | Sharpest ridge |
|---|---:|---:|---:|
| x 0.19 | 2 | **147.4 mm** | 5.99 mm |
| x 0.19 | 3 | 148.6 mm | 5.99 mm |
| x 0.24 | 2 | 304.0 mm | 5.79 mm |
| x 0.30 | 2 | 283.6 mm | — |
| x 0.30 | 3 | 205.4 mm | 4.38 mm |

Two things to take from that table. The **mask reach**, not the iteration count, is what drives the
radius — at x 0.19 the iteration count barely moves it (147.4 against 148.6). And the knob is not
monotonic: at the wide reach, *fewer* iterations gave a smoother cap, not a sharper one. So this
parameter cannot be reasoned about, only measured.

You asked for ~147 mm and for the deltoid to keep its definition, so the retained configuration is
the one that actually measures 147.4 mm: **reach x 0.19, 2 iterations.**

## Retained result

| Measure | Round 3 (205 mm) | **This candidate** | Round 2 baseline |
|---|---:|---:|---:|
| Cap silhouette radius, fitted at z −0.055 | 205.4 mm | **147.4 mm** | 128.4 mm |
| Sharpest clavicle/deltoid ridge | 4.38 mm | **5.99 mm** | 7.91 mm |
| Cap apex | z −0.055, y 1.5980 | z −0.055, y 1.6009 | z −0.055, y 1.6003 |

So the cap is still meaningfully rounder than the round-2 baseline and the shelf is still
substantially softer than the 7.91 mm it started at, but the deltoid reads as its own mass again
rather than blending into the trapezius.

### Guards

| Guard | Value | Status |
|---|---:|---|
| Ribcage max half-width (y 1.34–1.52) | 218.7 mm | unchanged |
| Waist half-width (y 1.26–1.30) | 150.3 mm | unchanged |
| Sternum columns, y 1.40 (x .03–.09 / .09–.15) | 138 / 115 mm | unchanged |
| Shoulder span (x bounds) | −0.8833..0.8833 | unchanged |
| Deepest pec/armpit crease | −2.58 mm at x 0.036 y 1.361 | identical to round 3 — armpit untouched |
| Phase A seams | 7 groups / 14 / 71.0° | unchanged |

## The outer-pec depth step is not a surface defect

I tried to smooth it — a z-only Laplacian across the y 1.37–1.43 outer band — and it did nothing
useful: the depth at y 1.40 went 67 → 65 mm and the step stayed ~42 mm. So I measured what is
actually there.

| Band, x 0.15–0.21, front surface | Vertices | Forward-facing | Side-facing | Max z |
|---|---:|---:|---:|---:|
| y 1.38–1.42 ("the flat area") | **3** | **0** | 3 | 67 mm |
| y 1.42–1.46 ("the fuller area") | 11 | 1 | 10 | 107 mm |

There is no forward-facing surface in the lower band at all. The 40 mm "step" in my depth table is
the **pec's outline**, not a crease: below y ≈ 1.42 the pec's lower-outer corner does not extend
into that band, so the probe was reading the laterally-facing flank of the ribcage and returning a
much smaller number. My own measurement box invented the step.

Closing it for real means building that lower-outer corner out — adding pec volume where there is
currently none, which is the broad chest mass this round excluded, and it sits directly against the
armpit, which was also off-limits. So I did not do it, and I dropped the ineffective stage rather
than ship a change that only cost 2 mm of depth.

If the lower-outer chest bothers you in the renders, the real fix is a small local volume addition
there — narrow, not broad — and I would want you to authorise it as an additive change.

## Validation

| Check | Result |
|---|---|
| Bare ↔ dressed grip solution | `homeGymPTMale`, both |
| Bare ↔ dressed posed hand | **0.0000 mm** |
| Grip contacts / wrap | −0.46 mm index, 252° — identical |
| Renderer vs exporter | 0.0000 mm, all six samples |
| Thigh clearance | +4.68 / +4.79 mm, 0 inside |
| Clothing closest approach | 1.97 mm, non-interpenetrating |
| `clothing` / `waistband` / `clothdebug` | all pass |

## Candidate assets

| Role | File | SHA-256 |
|---|---|---|
| Bare | `scratchpad/reference-fit/HomeGymPT_Male_PEC2_FINAL.glb` | `4918165cc31a69ed2e561ada1f059fc246c97418ab01964722b5416b1c0339f1` |
| Dressed | `scratchpad/reference-fit/HomeGymPT_Male_PEC2_FINAL_SHORTS.glb` | `990bc0b20b81026a61f8d24d369a3d11b3049b9ba920d994310c9b05483b972c` |

Rollback chain intact: round 3 `2bff95a3…b2f27807` / `5a40efa0…2a0187e4`; round 2
`da5b3c5e…dc1e003` / `cf6c09a5…9f804bd7`; skin `d71b70bc…c18f2be` / `8d07100f…f08f27ca`;
Phase A `b3dc70e1…89fdf09` / `71c5bdef…9fe42da9`; production v8 `951c2c39…963ee0` /
`cc728366…5722e3`.

## Status

Shoulder tuned as asked. The outer-pec step is reported as a measurement artefact rather than
silently left. Stopped for review. **Nothing promoted, nothing merged.**
