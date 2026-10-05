# r96 weights-only screening: local topology still required

This is pre-candidate evidence from exact r95 SHA `8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd`. Every run disabled the six r95 shoulder/flexion/scapular corrective keys in memory and did not save the opened Blend.

## Declared probe

- Zone: 440 existing vertices / 220 exact mirror pairs from `r96_weight_subzone_declared_before_edit.json`.
- Permitted solver columns: clavicle, scapula and upper arm per side plus `spine_02` and `spine_03`.
- Selected probe: 2 inverse-edge-length diffusion iterations at lambda 0.25.
- Selected probe invariants: maximum weight change `0.17790737795178824`; mean row L1 change `0.020953916444724996`; zero out-of-zone change; zero non-permitted-column change; zero mirror error; four influences maximum; normalization error `2.220446049250313e-16`.

## Numeric screening

The selected temporary probe candidate SHA was `c68fa4dbd2f239525a647e0231f3b651b039fea025f23d28a9d9c8f003db5334`.

- Full 15-pose comparison against the same corrective-disabled r95 control: `IMPROVED`, 2 failed checks in both, 0 regressions, 16 material severity improvements.
- Improvements include press-bottom shoulder minimum `0.39 -> 0.41`, pull-up-top shoulder minimum `0.31 -> 0.35`, press-bottom shoulder maximum `2.62 -> 2.37`, pull-up-top shoulder maximum `2.48 -> 2.25`, and several torso maxima.
- Self-intersection counts did not change in the shoulder-owning screen.
- Stronger probes (2 iterations at lambda 0.5 and 4 iterations at lambda 0.25) are rejected: each materially worsened press-top shoulder minimum ratio (`0.123 -> 0.100` and `0.123 -> 0.102`).

## Visual anatomical review

The six paired close-ups under `candidates/review/r96_weights_only_screening/` were inspected at original resolution. The selected mild probe is visually near-identical to its r95 control. It retains:

- a deep, pointed anterior axillary notch in press-top and press-top-rhythm;
- a flat membrane-like plane from upper arm into chest instead of readable anterior/posterior folds;
- a sharp posterior/side fold and tented lobe in overhead pull-up;
- abrupt clavicle/pectoral and deltoid/torso transitions.

These are still High-severity anatomical defects under the recovery design. Therefore the probe is not promoted as r96, no corrective fitting is authorized, and the Task 6 stop rule directs work to the already-declared local support topology. The numeric probe remains useful as a bounded weight starting point after topology is added.

Production approval remains false.
