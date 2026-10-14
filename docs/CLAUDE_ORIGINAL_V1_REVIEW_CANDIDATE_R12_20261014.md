# ORIGINAL_v1 review candidate R12: baked delta-mush shoulder shapes (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

**Owner:** "Continue to fix the issue. We can't progress until it's fixed."

**Starting point:** R11's re-meshed shoulder was smooth but kept R10's shapes: a flat deltoid, a shallow armpit, and crease lines at lockout.

## What R12 is

R12 is R11 plus 12 shape keys, `HGPT_S5_BAKE_<s>_{85,110,130,145,160,172}`. They are driven on elevation from 60° by
`drives.drive_s1` (family `HGPT_S5_BAKE_`). Weights, bones, basis mesh, modifiers and every R11 key are unchanged, and
there is **no new runtime deformer**.

**How the keys are made** (`scripts/build_original_review_candidate_r12_blender.py`, three processes):

1. **Target.** R11 with its S4 keys re-solved on the re-meshed body at 5× (trapezius at 0.3 of that), plus a **delta-mush
   deformer**: Blender Corrective Smooth, 60 iterations, factor 1.0, length-weighted, applied over the shoulder region (full to 16 cm from the
   pivot, fading out by 24 cm).
   - **Why only a target:** this is the best-looking press of everything tried (closeups: `press/bake_variants_closeups.jpg`, top row).
   - **What stops it shipping:** live, it pushes armpit skin through itself (50 / ~150 / ~190 self-intersecting pairs at
     start / near top / lockout, against 0 / 0 / 1 for R11). The weaker settings that stay collision-free lose most of the look.
2. **Dump.** The target's posed surfaces are saved at the six key poses of the full-range press.
3. **Bake** (`scripts/build_original_bake_corrective_blender.py`):
   - each vertex's posed offset from R11 is mapped to rest through R11's blended LBS matrices (damped, capped at 50 mm);
   - a **smooth collision guard** runs along the press path. Wherever the keys add self-intersecting pairs or collapsed faces,
     their deltas are scaled by 0.5 + 0.5·m, where m is a diffused mask (0 on the offending vertices, 1 five rings away). The
     guard is mirror-symmetric and repeats until no pose adds any.

## Variants measured and rejected

| Variant | Result |
|---|---|
| Delta mush live (60 it, factor 1.0) | best look; 36–193 self-intersecting pairs |
| Delta mush live, weaker or armpit-damped | 0–14 pairs only at settings with little visual effect |
| Bake with the S4-style step guard | jagged seams where whole rings were halved |
| Bake + fade of the target's own overlaps | seams remain |
| Bake + Laplacian smoothing of the keys | shapes weaken, and the lockout crease lines return |
| Static collision repair of the target | did not converge (more pairs) |
| Target with trapezius at 5× | jagged top-of-shoulder edge in the target itself |
| **Trapezius 0.3, no fade, smooth guard** | **selected** |

## Results

**Full press, R11 → R12** (`r12_build.json`):
- self-intersecting pairs are never above R11 (0 to 160°, 1 at lockout);
- collapsed faces 24 → 14 at lockout;
- faces stretched beyond 2× fall to about half from 120° up (lockout 570 → 286).

**Recorded costs:**
- body volume +1.07 % at the start pose (the rounder, contracted deltoid);
- −2.06 % at lockout, against −1.73 %.

**Benchmarks** (`r12_validation.json`):
- **Shoulder press (160° path):** 0 / 310 / 0 → 4 / 160 / 0 (collapse / stretch / pairs).
- **The other 12:** identical to R11.

## Against the owner's reference photos

The comparison sheet is kept outside the repo because it contains the owner's photo. Animation: `press/shoulder_press_r11_vs_r12.gif`.

| Stage | R12 |
|---|---|
| Start, mid | deltoid visibly rounder (closer to the photo's full cap) |
| Near top | a defined pectoral fold running into the arm, with a hollow beneath it (as in the photo); a faint line remains at the top of the armpit |
| Lockout | cleaner armpit with one fold line; the hollow is still shallower than the photo |
| Overall | the model's build is slimmer than the reference (body shape, not deformation) |

## Tests

`scripts/blender_tests/test_original_review_candidate_r12.py`, 6 native tests (CI):
- **Identity.**
- **No deformer added:** R12 = R11 + the 12 baked keys.
- **Deltas:** bounded and mirror-symmetric (within 1 mm).
- **Press path:** no new overlap or collapse at any frame; at least 30 % less stretch from 120° up; the volume costs are asserted.
- **Live drive:** the lockout row reproduces exactly.
- **Benchmarks vs R11.**

R1–R11 and the press-extension tests pass.

## Phone review set and the next deformation issue (hip fold)

**Phone review set:** `sequences/` holds every one of the 13 benchmarks as a filmstrip (three-quarter and side view, t = 0 to 1) plus a GIF, each with a peak frame of a003 next to R12.

**Hip fold, measured after R12.** The worst remaining benchmarks are the squat and the deadlift. At their peaks there are 227 and 313
self-intersecting pairs (28 and 38 collapsed faces).
- **Where:** every pair is in the groin crease at the front of the hip (rest z 0.83–1.06 m, about 8 cm anterior). In the
  squat the classes are thigh/thigh and pelvis/thigh; in the deadlift, spine_01/thigh and thigh/thigh.
- **What it is:** a natural anatomical fold whose two layers pass through each other in a thin sliver. In the renders it
  reads as a hip crease.

**Attempted and rejected:** a K1-style hip contact corrective (hinge pelvis → thigh, keys 90/115/135, contact plane bisecting
the trunk and thigh directions), tried two ways:
- sides chosen by bone weight;
- sides chosen by rest position across the joint plane, because the crease skin is thigh-weighted on both of its layers.

Either way, in isolated hip-flexion poses the contact push creates new folds. The guard therefore backs the keys almost to zero on the crease vertices (at most 0.1–1 mm), and the squat and deadlift counts do not change (227 → 227, 313 → 313). The code was reverted.

**What would work:** the shoulder approach (crease re-weighting or a hip-crease helper joint, with a delta-mush bake). The fold is barely visible, so this is queued below the owner's open decisions.
