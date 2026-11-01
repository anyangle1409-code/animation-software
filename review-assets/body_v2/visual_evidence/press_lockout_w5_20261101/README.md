# Press lockout chest ripples: C1 vs W5 (1 Nov 2026)

- **C1:** the current candidate.
- **W5:** C1 with one change. The lockout key `R121_ARM_<s>_153` is patched with a guarded delta-mush pass.
- **Clip:** the shoulder press, 49 rendered frames. The cameras are close-ups of the shoulders (front, side, back),
  identical for both models.

**What W5 fixes.** At lockout, C1's skinning leaves fine wood-grain ripples across both pectorals and the side of the
chest. They are the same with every shape key off. W5 smooths the posed skin and puts back the rest pose's own fine
relief:

- only the height above the smoothed surface changes, along its normal;
- skin within two rings of a crease is left alone, tapered over six rings;
- the arm skin is left alone.

| | C1 | W5 |
|---|---|---|
| Lockout roughness, upper body, p95 / p99 (rest: 0.066 / 0.131 mm) | 0.076 / 0.125 mm | **0.059 / 0.104 mm** |
| Peak self-intersections (49 frames) | 7 | 7 |
| Peak folds over 90° | 8 | 8 |
| Peak edges over 35° | 361 | 361 |
| Edges stretched over 2× (peak) | 9011 | 8995 |
| Edges collapsed under 0.5× (peak) | 5635 | 5686 |
| Return to neutral | 0.0 mm | 0.0 mm |

**Other movements (17-frame harness).**

- **Pulldown:** the same as the press.
- **Overhead extension:**
  - peak self-intersections 383 → 381;
  - folds unchanged at 67 (one frame 61 → 62);
  - edges over 35° 768 → 766.
- **Lateral raise, curl and squat:** identical. The key is off there.

**Still visible in both.** The V-lines from the sternum to the armpits are pose creases, which the guard leaves alone
on purpose. Ripples on the upper arms remain because arm skin is excluded; including it raised overhead-extension
folds.

**How it was found.** Nine variants were measured before this one. Each was rejected for a measured regression. They
are listed in `docs/R121_MOVEMENT_TRAJECTORIES_20261024.md`, section W5.

**Status:** candidate. C1 (W3) is unchanged and remains available.

**Files:** `press_lockout_c1_vs_w5.mp4`, `STILLS_press_<view>.jpg` (neutral, rack, lockout, return),
`press_lockout_metrics.json`.
