# Realism layer, Stage 1 — pose-dependent biceps / brachialis / forearm deformation

**Branch:** `chatgpt/absolute-retarget-imports`
**Executed from:** `63d7c1c`
**Candidate for review. Nothing promoted, nothing merged.**

Stage 1 of `docs/BICEP_CURL_REALISM_LAYER.md`. The arm now changes shape with flexion instead of
reading as a tube following bones. The static body, rig, weights, grip, wrist alignment and curl
path are untouched.

## No reference video was attached

The doc asks for the movement reference video to be supplied when this phase runs. It was not
attached on this turn, so the amplitudes below are anatomical judgement, not a match to the
reference. That is the one part of Stage 1 that cannot be signed off without it.

## What was built

`src/character/muscleDeformation.ts`, following the idiom already established by
`importedDeformation.ts`: corrective **morph targets**, authored once at build time as bind-space
deltas, driven per frame by the elbow's own flexion.

Three targets per side, six in total:

| Target | Region | Peak amplitude |
|---|---|---:|
| `homeGymPT_biceps_{l,r}` | anterior upper-arm belly — swells *and* draws axially toward its own middle | 7.0 mm swell, 4.0 mm axial |
| `homeGymPT_brachialis_{l,r}` | distal humerus into the proximal forearm, front and outer | 4.5 mm |
| `homeGymPT_forearm_{l,r}` | proximal/mid forearm flexor mass | 3.0 mm |

Each is gated by the vertex's own skin-weight share of the bone it belongs to, profiled `cos²`
along the bone axis so it reaches zero value *and* zero slope at its edges, and gated anteriorly by
the radial direction's dot with the model's front axis.

The driver is `elbowFlexion` (`src/body/elbow.ts:311`) — a smoothstep of the angle between the
upper-arm and forearm bone axes, already used by the elbow correctives. It is **exactly 0 in the
rest pose**, which is what makes the doc's "Bottom returns exactly to the accepted baseline shape"
a property of the construction rather than a tuning result.

Three points of care worth recording:

- **Morph normals as well as positions.** A silhouette that swells while the shading stays flat
  barely reads as fuller. three.js indexes `morphAttributes.normal` by the same slot as
  `morphAttributes.position`, so the layer is built *after* the elbow correctives and pads their
  four slots with no-change normals — leaving their behaviour exactly as it was.
- **`importedDeformation.ts` was not re-authored.** It only gained an `export` on
  `correctiveSampler` and a name for its target type, so both layers bake identically and the
  viewport and exporter cannot drift apart.
- **`CharacterBuild` carries one stack**, so `retargetSource.ts` gained a small
  `composeDeformation` that runs the layers in order and concatenates their controls and samplers.

The layer is code-side, so the accepted gitignored GLBs need no re-authoring. It is exposed in the
editor's Correctives panel as **Arm muscle contraction** (0% = the accepted static arm at every
pose, 100% = the authored contraction), which is also how the before/after below was captured, and
it can be disabled per-asset with `scene.extras.homeGymPT.muscleDeformation.enabled = false`.

## Measured behaviour

`scratchpad/repair/muscle.test.mts`, on the accepted `CORNER_FINAL_SHORTS`, layer off vs layer on
at the same pose.

### Bottom and Return are the accepted body, exactly

| Frame | Vertices moved | Worst displacement |
|---|---:|---:|
| Bottom | **0** of 12,249 | **0.000 mm** |
| Mid lift | 636 | 2.739 mm |
| Peak | 636 | 5.425 mm |
| Mid lower | 636 | 2.739 mm |
| Return | **0** of 12,249 | **0.000 mm** |

Corroborated independently in the renderer: of the 16 before/after capture pairs, **every `bottom`
and `return` pair is byte-identical** and every `mid`/`peak` pair differs.

### The fill is localised, not a fatter arm

Mean anterior radius from the humerus axis, three rings along the bone:

| Frame | proximal (0.16–0.26) | **belly (0.40–0.56)** | distal (0.70–0.80) |
|---|---:|---:|---:|
| Bottom | 0.0% | **0.0%** | 0.0% |
| Mid lift | +0.8% | **+5.1%** | +1.2% |
| Peak | +1.3% | **+7.7%** (+3.31 mm) | +1.6% |
| Mid lower | +0.7% | **+4.5%** | +1.0% |
| Return | 0.0% | **0.0%** | 0.0% |

A five- to six-fold contrast between the belly and the ends: the mass appears where a biceps is,
not along the whole arm. Left and right agree to 0.01 mm.

### The belly shortens as well as fills

Axial gap between two fixed bands near the belly's ends — no threshold, so a taller bump cannot be
mistaken for a longer one:

| Frame | off | on | Δ |
|---|---:|---:|---:|
| Bottom | 109.95 mm | 109.95 mm | 0.00 |
| Mid lift | 111.18 mm | 110.10 mm | −1.08 mm |
| Peak | 113.64 mm | 111.50 mm | **−2.14 mm (−1.9%)** |
| Return | 109.95 mm | 109.95 mm | 0.00 |

### It stays inside the arm

Worst displacement at Peak by dominant bone:

```
upper_armR 5.425  upper_armL 5.415  upper_armR001 5.107  upper_armL001 5.096
forearmR001 2.602  forearmL001 2.602  forearmL 2.559  forearmR 2.559
handL 0.080  handR 0.080  breastL 0.020  breastR 0.020
```

The hand and chest figures are the smooth blend the doc asks for ("blends smoothly into elbow,
deltoid and armpit regions") rather than a bulge; a hard zero at a skin-weight boundary is how a
crease gets made. No finger, thumb or palm vertex moves at all, which is why the grip contacts
cannot have shifted.

## Guardrails — every locked figure unchanged

| Check | Result |
|---|---|
| Technique rules (22 authored) | **no violations**, none unreachable, loop closed |
| Renderer vs exporter grip frame | **0.0000 mm** at t = 0, 2, 4, both sides |
| Dumbbell / thigh clearance at Bottom | +0.48 / +0.64 mm, 0 inside — identical to accepted |
| Grip contact, palm | −2.54 mm — identical to the Phase A record |
| Finger wrap | 343° shipped profile — unchanged |
| Bare ↔ dressed posed equivalence | **0.0000 mm** over 10,839 vertices |
| Project suite | **38 files, 298 passed**, 1 skipped, no threshold loosened |
| Typecheck | clean |

`src/body/neck.test.ts` timed out once at vitest's 5 s default while a Playwright capture was
running on the same container; it passes 12/12 in isolation and passed in the uncontended suite
run. CPU contention, not a regression.

## One regression found and fixed during the round

The first capture pass came back with **crumpled faceting across the face, neck and chest** — areas
the layer must not touch. The cause was mine: the normal morph differenced against the normals
*stored in the asset*, but this asset's convention is unwelded per-vertex normals with deliberate
hard edges at the scalp and neck (the Phase A finding). That produced a non-zero normal delta over
the whole body, so at full influence the muscle fill rewrote the entire surface to welded smooth
normals and undid the Phase A repair.

The reference is now the smooth field recomputed from the *undisplaced* positions. Differencing two
fields computed the same way cancels the asset's convention out and leaves a delta that is exactly
zero wherever the surface does not move. Per-slot reach after the fix:

```
homeGymPT_elbow_l        (none)     homeGymPT_elbow_outer_l  (none)
homeGymPT_elbow_r        (none)     homeGymPT_elbow_outer_r  (none)
homeGymPT_biceps_l       upper_armL:109 upper_armL001:104 breastL:16 forearmL:5
homeGymPT_brachialis_l   upper_armL001:65 forearmL:44 forearmL001:2
homeGymPT_forearm_l      forearmL:69 forearmL001:58 upper_armL001:19 handL:8
```

No spine, jaw, scalp, foot or face vertex is reshaded, and the elbow correctives read `(none)` —
their behaviour is preserved exactly. `muscle.test.mts` now guards this per slot, by region.

## Visual evidence

Rendered in the running app on the accepted candidate, proven loaded before anything was captured:
active source `import`, the character panel naming `CORNER_FINAL`, the `Character` toolbar button
`is-active`, and the Correctives panel reporting **Arm muscle contraction · 100%**. `light`
backdrop, no selection gizmos, canvas-only frames. 32 captures in `scratchpad/musclepack/`,
composites in `scratchpad/musclereview/`.

- `close_upperarm_l_peak_ab.png` — the headline pair. The ON side has a fuller, rounder belly crown
  while the deltoid and elbow read the same.
- `close_clavicle_l_peak_ab.png` — shoulder, armpit, neck, chest and grip visually identical; no
  crease, the accepted armpit repair undisturbed.
- `front_peak_ab.png`, `front_mid_ab.png`, `three_quarter_peak_ab.png`, `left_peak_ab.png`.
- `loop_front.png`, `loop_three_quarter.png` — Bottom → Mid → Peak → Return with the layer on.

### Honest limits of this pack

1. **At full-body distance the effect is subtle.** It is clear in the close-ups and visible but
   understated in `front_peak_ab.png`. The amplitudes are deliberately conservative; the control is
   already wired, so raising them is a one-line change if the review wants more.
2. **The focus camera framed the character's left arm off the right edge**, so the arm close-ups
   show the *right* arm. The measurements confirm the two sides agree to 0.01 mm, so nothing is
   hidden, but the framing is not what was intended.
3. **`close_forearm_l_peak_ab.png` is a weak panel** — the crop landed on the rim-lit back of the
   arm and the shorts. The forearm change is better judged from the numbers and the 3/4 pair.
4. **No recording.** The doc asks for a short clip at normal playback speed; this pack is stills
   only.

## Stage 1 against the doc's targets

| Target | State |
|---|---|
| Biceps visibly fuller/shorter toward Peak, lengthening toward Bottom | **done** — +7.7% belly radius, −1.9% working length |
| Brachialis / upper-forearm mass participates | **done** — 4.5 mm at the junction, 2.6 mm on the forearm |
| Forearm silhouette changes through flexion | **partly** — flexion yes; supination is Stage 2 |
| Blends smoothly into elbow, deltoid and armpit | **done** — sub-0.1 mm feather, no crease in the captures |
| Bottom returns exactly to the accepted baseline | **done** — 0.000 mm, byte-identical renders |
| Non-destructive, pose-driven, static body not remodelled | **done** — morph targets only, no GLB re-authored |

## Status

Stage 1 built, measured and validated on the accepted candidate. Every locked curl figure is
unchanged. Stopped for visual review before Stage 2 (progressive forearm supination).

**Not promoted. Not merged.** The accepted curl and `CORNER_FINAL` remain the rollback, and the
layer can be taken to 0% in the editor without touching an asset.
