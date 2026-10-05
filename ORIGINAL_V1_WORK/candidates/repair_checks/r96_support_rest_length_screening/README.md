# r96 support-row rest-length screening: family rejected

This pre-candidate family starts from the exact declared topology intermediate SHA `6934594dde9140193882c0e293f8b404fb24bed8b1b1b2722267ff97d13844dd`, whose immutable lineage parent is r95 SHA `8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd`. The edit family was committed before authoring in `r96_support_rest_length_declared_before_edit.json`.

## Authored probes

The authoring script moved only 32 of the 38 declared new support vertices. The remaining six were at or inside the declaration's zero-taper boundaries. Every retained shape key received the same per-point delta, so its delta relative to Basis stayed fixed. All original vertices, weights, topology and the 67-bone rig were preserved.

| Declared strength | Actual maximum displacement | Geometry-only candidate SHA | Candidate after the already-declared i1/lambda0.25 weights |
|---|---:|---|---|
| 0.004 m | 0.00333905 m | `db08787d86b136f08292370ed4483a57a4d415ea6afc0230d38abc433c6165e1` | `bd0ecc732af2dc8aaca7afe413c6fca135fb26b725ccc6d42581eb3e572ff7c6` |
| 0.008 m | 0.00667810 m | `91510adc8a19ea7ce42eaf3775e2c977f27ac64a5bae2e057a29f6de4559d0ed` | `415c85c19846422041c81c97f9d5b2d674ebc5486b6df36cc8c35ba042724e0c` |
| 0.012 m | 0.01001715 m | `9e6004aeb7a869d1c8d06b5e17a0f3d2dcc48a0ef90a80c7f848993c3a1dd256` | `f6dcd93af3aa915b0d5dc975c9090195c1b39cd9d029a34efddf6d9ab6a4391e` |

All candidates were evaluated through the exact production pose path with every non-Basis corrective disabled in memory.

## Numerical gate

- 0.004 m: `UNCHANGED` versus the topology+i1/lambda0.25 control; two failed checks on each side, zero regressions and zero material improvements.
- 0.008 m: `REGRESSION`; squat-bottom self-intersections increased `82 -> 96` (tolerance 5).
- 0.012 m: `REGRESSION`; squat-bottom self-intersections increased `82 -> 94` (tolerance 5).

The machine-readable comparisons are committed beside this report. The 8 mm and 12 mm probes are rejected before visual selection because they violate the material-regression stop condition.

## Visual anatomical gate

The 4 mm probe is the only numerically eligible member and its committed close-ups were inspected at original resolution. It produces a small silhouette shift but does not remove the High-severity defects:

- the anterior axillary opening still terminates in a pointed notch;
- the upper-arm-to-chest transition still reads as a flat membrane rather than continuous anterior and posterior folds;
- the posterior/side view still contains the tented lobe and abrupt shoulder-to-torso transition.

Representative image SHA-256 values are:

- press-top close shoulder A: `8d4f6691e29cc3ca5d5474277cee5ba6429dbc487d1172313545b111ad4ce74d`;
- press-top close shoulder B: `b265de8bbf5bb074ef615fa93043c318d259a9496e3a3329dba63b49a63550b9`;
- pull-up-top close shoulder B: `14c8ad47dad6b2c27e0638aca72d2e8f5cca254368323af9b8bc091e3469cae3`.

The family therefore fails the Task 6 weights-only visual gate and is not promoted. It also demonstrates that bowing the single horizontal support row cannot supply the missing anatomical fold structure; the next foundation attempt must change the local topology layout rather than increase this displacement or enable correctives.

Production approval remains false.
