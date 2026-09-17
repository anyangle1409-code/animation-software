# Model phase A — forearm/wrist/hand surface repair

**Branch:** `chatgpt/absolute-retarget-imports`
**Executed from:** `589d5c7`
**Candidates only. Production v8 untouched. Not merged.**

Phase A of `docs/MODEL_APPEARANCE_PHASE.md`. The faceting is repaired on candidate assets with a
normals-only change; the accepted curl, the rig and the delivered production pair are unchanged.

## Diagnosis — what the faceting actually is

The diagnostic separates two questions that look alike and are not.

**1. Do co-located vertices disagree on their normal?** Yes, and this is the defect.

| Body | Seam groups | Vertices | Worst disagreement |
|---|---:|---:|---:|
| v8 (delivered) | 320 | 723 | 138.3° |
| v7 (previous) | 7 | 14 | 71.0° |

**2. Do the stored normals match the geometry?** In **both** bodies the stored normals match
per-vertex normals computed *without* welding co-located duplicates — mean deviation **0.00°**,
worst **0.0°**. That is the asset's own convention, not something v8 introduced.

So the mechanism is this. The mesh splits topology at UV seams, which duplicates vertices at the
same position. With unwelded normals, the two sides of a seam agree only while the surface is
locally smooth across it — which is how v7 reads. The Stage 1/2 arm work moved each side's
*neighbours* by different amounts, so in v8 the two sides now disagree by up to 138°, and the seam
shades as a hard blocky facet. The vertices themselves are still exactly co-located; it is the
surrounding surface that changed.

This is why the defect shows at Bottom on a straight arm as well as at Peak: it is in the asset,
not the pose.

## The repair

`scratchpad/repair/weldnormals.mjs`. For every co-located group whose stored normals disagree by
more than 5°, all members get the normalised mean of that group's stored normals. Nothing else is
written.

Groups that are **also** seams in the v7 reference body are matched by vertex index and left
alone, so intentional hard edges survive rather than being smoothed away by a blanket pass.

- **313 seam groups welded** (709 vertices)
- **7 reference hard edges preserved** (`spine.003` ×6, `spine.004` ×1)
- largest normal shift applied: 69.1°

### Result

| Measure | v8 delivered | v9 candidate | v7 reference |
|---|---:|---:|---:|
| Seam groups | 320 | **7** | 7 |
| Seam vertices | 723 | **14** | 14 |
| Worst seam disagreement | 138.3° | **71.0°** | 71.0° |
| Vertices >15° off the geometry's smooth normal | 418 | **219** | 283 |
| Vertices >45° off | 21 | **15** | 15 |
| Worst deviation | 73.6° | 73.6° | 73.6° |

The candidate lands exactly on v7's seam profile — the same 7 groups, the same 14 vertices, the
same 71.0° — and is *better* than v7 on smoothness (219 vertices over 15°, against 283). The
unchanged 73.6° worst deviation is a pre-existing scalp hard edge at `spine.006`, identical in all
three bodies and deliberately not touched.

### It is normals-only, verified attribute by attribute

Candidate against delivered v8, every buffer compared:

| POSITION | TEXCOORD_0/1 | COLOR_0 | JOINTS_0/1/2 | WEIGHTS_0/1/2 | indices | inverseBindMatrices | nodes | scene extras | skin joints |
|---|---|---|---|---|---|---|---|---|---|
| identical | identical | identical | identical | identical | identical | identical | identical | identical | identical |

**NORMAL**: 2,127 components differ — exactly the 709 welded vertices × 3.

## Candidate assets

| Role | File | SHA-256 |
|---|---|---|
| Bare candidate | `scratchpad/reference-fit/HomeGymPT_Male_BASELINE_v9_CANDIDATE.glb` | `b3dc70e19a539a4500c1b57804a59fd908d88e278819f6aed2ca2bfe289fdf09` |
| Dressed candidate | `scratchpad/reference-fit/HomeGymPT_Male_BASELINE_v9_CANDIDATE_SHORTS.glb` | `71c5bdef7164770528fcfb8c379957545d64f88a19fafb62f892fca89fe42da9` |

Production is the rollback reference and is byte-identical to before: v8 body
`951c2c39…963ee0`, dressed `cc728366…5722e3`.

The dressed candidate was built from the bare candidate through the repaired `dress.mjs`, so it
carries the rest pose (160 matrices, 50 changed), inverse binds (160, 50 changed), the full
`homeGymPT` extras, and its own correspondence file. Garment safety held: 9 garment joints, 50
re-bound, **0 overlap**.

## Validation

| Check | Result |
|---|---|
| Bare ↔ dressed grip solution | `homeGymPTMale` both, offsets (0.0174, 0.0452, 0.0083) both |
| Bare ↔ dressed posed hand | **0.0000 mm** |
| Bare ↔ dressed posed body | **0 of 10,839** vertices differ |
| Grip contacts, curl t = 2 | −0.46 / −0.36 / −0.22 / −0.11 mm, 0 inside; thumb +1.18; palm −2.54; wrap 252° |
| Renderer vs exporter | 0.0000 mm at t = 0, 2, 4, both sides |
| Thigh clearance, body only | +4.68 / +4.79 mm, 0 inside |
| Thigh clearance, with garment | +0.48 / +0.64 mm, 0 inside |
| Clothing closest approach | 1.97 mm, non-interpenetrating |
| `clothing` / `waistband` / `clothdebug` | all pass on the regenerated correspondence |
| Seams on the dressed candidate | 7 groups / 14 vertices / 71.0°, matching the bare candidate |

Every locked figure is identical to the accepted values. The full suite is not run here because
these are candidates, not a production proposal — that belongs with a promotion decision.

## Visual evidence

Rendered in the running app, not re-rendered offline. The bundled dressed v8 was proven loaded
first (`baseline-dressed`, `206 …v8_SHORTS.glb`, Character mode active), the before shots taken on
it, then the candidate imported through the app's own GLB import — reported by the app as
`HomeGymPT_Male_BASELINE_v9_CANDIDATE_SHORTS`, 12,249 vertices, 160 bones, 52 driven, "kept as
authored", matching the production dressed figures. Same camera, same bone focus, same frames.

`crop_before_v8_hands_peak.png` against `crop_after_v9_hands_peak.png`: the stair-stepped checker
patches on the forearm are gone, and nothing else in the frame changes.

## Two geometry findings the normals repair does not fix

Both were found during the diagnosis, both are pre-existing in the delivered v8, and neither is
touched here. Stating them rather than quietly masking them:

1. **The surface is genuinely creased at those seams.** The welded normal differs from what was
   stored by a mean of 12.5° and up to 69.1°, which is the size of the crease the Stage work left
   in the geometry. The repair shades across it — which is what normals are for, and it matches
   v7's convention — but the underlying surface is still slightly faceted there.
2. **22 vertex pairs that were welded in v7 are no longer exactly co-located in v8**, separated by
   up to **1.109 mm**. These are small cracks in the surface, not a shading issue, and a
   normals-only pass cannot close them.

Neither is visible in the review pack at these camera distances. Both would need a geometry
decision, which Phase A is explicitly not authorised to take.

## Appearance gaps against the reference board

From the candidate review pack, in the document's own refinement order. Nothing here is acted on
yet — this is the read for the user's review.

1. **Surface/normals** — repaired, item 1 done.
2. **Head/neck/shoulder line** — the shoulders already read relaxed and sloping rather than
   shrugged, which matches the board. The neck is thicker and shorter than the board's.
3. **Physique** — close in mass, but the board has a narrower waist with more V-taper, and more
   defined chest and abdominal separation. The candidate's midsection is fuller.
4. **Face** — the jaw is heavier and squarer and the cheekbones flatter than the board's leaner
   face. No stubble.
5. **Eyes** — the largest single gap. The candidate's lids read heavy and the eyes have no iris or
   sclera definition, so the expression reads sleepy rather than "relaxed, focused". The board
   wants open, natural light blue/grey eyes.
6. **Hair** — bald. The board wants short textured dark brown with tapered sides.
7. **Skin/material** — flat grey matte. The board's "realistic skin/material response" is the
   change that would move the look furthest, and it is a material question before a geometry one.
8. **Shorts** — the candidate's are shorter and tighter than the board's looser mid-thigh pair.
9. **Hands/forearms** — now smooth; shape reads well against the board's forearm panel.

Feet are left bare, per the reference limit on footwear.

Two capture notes for the next round: the side and back views are lit from the front by the
Studio backdrop so they read as near-silhouettes — the `light` or `study` backdrop would show the
silhouette better; and a bone stays selected for the focus-camera close-ups, so its rotation gizmo
is visible in some frames.

## Status

Phase A complete and validated on candidates. Production untouched, rollback intact. Stopped for
user review before any Phase B appearance change. **Not merged.**
