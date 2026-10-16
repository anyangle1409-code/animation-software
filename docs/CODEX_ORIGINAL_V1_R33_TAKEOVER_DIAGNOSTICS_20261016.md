# ORIGINAL_v1 R33 takeover: bake-stage diagnosis, 16 October 2026

Review candidate only. R33 remains unaccepted. No new candidate or saved blend was created.

## Source and execution

Read the owner's handoff and R33 report from branch `claude/original-v1-consolidated-review-20261014`, verified at `08aaaf934e169f4afd73dc567cb585dd2a7488e4`.

The local environment has Python 3.12 but no working Blender; the cached Blender archive is truncated. Numerical measurements were therefore run in GitHub Actions using the existing pinned Blender 5.2.1 download and SHA256. This requires no Windows laptop.

- Baseline diagnostic run: https://github.com/anyangle1409-code/animation-software/actions/runs/38929208644
- Bake-stage trace: https://github.com/anyangle1409-code/animation-software/actions/runs/38929754451
- Trace script: `scripts/claude_review_tools/trace_r33_bake.py`.
- Machine-readable measured stage results: `docs/CODEX_ORIGINAL_V1_R33_BAKE_STAGE_TRACE_20261016.json`.
- Each completed diagnostic run passed R33's three unchanged native tests. The diagnostic steps also completed successfully.
- Full original candidate CI at diagnostic commit `8cf44082` passed. Test definitions and tolerances were not edited.

The trace opens the recorded B5 base and merged R33 targets, rebuilds S7 **in memory**, and measures target fit before and after the existing guards. It does not save a blend. Existing scratch tools run from temporary copies with their import paths adapted; repository measurement tools are unchanged.

## Confirmed front-armpit bake-error source

Error at vertex 18633 (millimetres):

| Arm elevation | Before path guards | After smooth guard | After final guard |
|---|---:|---:|---:|
| 120 degrees | 0.078 | 20.979 | 20.979 |
| 145 degrees | 0.091 | 23.443 | 23.443 |
| 156 degrees | 0.097 | 4.878 | 4.878 |
| 166 degrees | 0.106 | 0.106 | 0.106 |

The smooth guard causes the large loss of target fit at this vertex; the initial inverse bake and final stepwise guard do not cause that loss. This narrows the handoff's guard hypothesis to `smooth_guard` in `build_original_bake_corrective_blender.py`.

The existing build log shows this guard reacting to both collapsed faces and intersecting pairs on the full press and benchmark paths. It reduces active S7 offsets around affected vertices with a diffused local mask. The stage trace does not yet identify which individual path/time/face first forces the worst vertex back. Removing or weakening the guard is **not** a validated fix.

Fresh measurements on the saved R33 reproduce:
- 120 degrees: maximum error 21.0 mm, p99 2.7 mm, 136 vertices over 5 mm.
- 145 degrees: maximum error 23.4 mm, p99 3.0 mm, 146 vertices over 5 mm.
- 156 degrees: maximum error 11.8 mm, p99 1.0 mm.
- 166 degrees: maximum error 8.8 mm, p99 0.1 mm; seven vertices over 5 mm. The small p99 must not be reported as the maximum.

## Fold measurements: improvements and regressions

Same existing fold tool and full-press poses, counting edges within 18 cm of the right arm root with dihedral above 30 degrees and increase above rest greater than 15 degrees:

| Elevation | R31 fold edges | R33 fold edges | R31 maximum local dihedral | R33 maximum local dihedral |
|---|---:|---:|---:|---:|
| 120 | 32 | 22 | 87 | 70 |
| 125 | 42 | 31 | 70 | 63 |
| 130 | 52 | 47 | 104 | 132 |
| 132 | 50 | 44 | 96 | 115 |
| 139 | 56 | 27 | 84 | 65 |
| 145 | 80 | 34 | 86 | 83 |
| 151 | 43 | 17 | 73 | 64 |
| 156 | 54 | 45 | 75 | 83 |
| 166 | 55 | 67 | 94 | 79 |

Dihedrals are rounded degrees and are maxima over the local region, not only the counted new folds. At 130 degrees R33's sharpest edge lies approximately 2.3 cm outward, 2.2 cm forward and 3.6 cm below the right shoulder joint. R33 has fewer fold edges overall there, but its worst front edge is sharper. Lockout also has more counted fold edges, despite a lower maximum. These regressions remain recorded.

## Benchmark sampling gap (static finding, not yet a proven cause)

The guard samples `t=i/20`. The nine-frame benchmark samples `t=i/8`. Benchmark times 0.125, 0.375, 0.625 and 0.875 are absent from the guard's sample set. Thus a guard pass cannot prove those benchmark poses are clean. This is a plausible explanation for the recorded two crushed triangles, **not yet a reproduced causal diagnosis**.

R33's native test explicitly permits the known +2 shoulder-press collapse regression and reads recorded metrics for those assertions. Passing that test does not mean the deformation is visually accepted or that every intermediate pose is clean.

## Next candidate boundary

No R34 exists from this work. Priority remains:
1. Identify the specific guard triggers at the front patch and produce a localized correction that retains collision/collapse protection.
2. Reduce stretch without undoing the rear-armpit, upper-arm and elbow improvements.
3. Reproduce and remove the two benchmark crushed triangles, including exact benchmark sample times.

Before any broader change to the guard algorithm or deformation design, ask the owner. R33 still awaits the owner's visual review. Any new candidate must use a new R34-or-later folder, its own test, measured documentation, same-angle before/after images and a press video.

All owner restrictions remain: frozen canonical skeleton and production V-series untouched; `HGPT_SHOULDER_*` untouched; no existing test weakening; no merges or force-pushes; no reference photos, secrets or third-party assets added.

## Existing R33 visual review material

These were produced by the previous assistant; this takeover did not create new renders or video:

- [R31/R33 back and three-quarter comparison](https://github.com/anyangle1409-code/animation-software/blob/08aaaf934e169f4afd73dc567cb585dd2a7488e4/ORIGINAL_V1_WORK/anatomy/candidates/claude_review_r33_20261016/renders/press_r31_r33.jpg)
- [R33 press video](https://github.com/anyangle1409-code/animation-software/blob/08aaaf934e169f4afd73dc567cb585dd2a7488e4/ORIGINAL_V1_WORK/anatomy/candidates/claude_review_r33_20261016/press/shoulder_press_r33_views.mp4)
