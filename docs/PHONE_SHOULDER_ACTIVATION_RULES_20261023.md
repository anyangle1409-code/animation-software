# Home Gym PT — verified shoulder activation rules on preserved reconstructions

**23 October 2026. READ-ONLY rule introspection only — NOT anatomical/production approval, NOT a model repair.**

## Verified run and immutable artifacts

The [five-job cloud run 40023281618](https://github.com/anyangle1409-code/animation-software/actions/runs/40023281618) completed SUCCESS: W8/V14/R120 Blender 5.2 inspections, native failure localization, and cross-model comparison. Per-model JSON `shoulder_activation_rules.json` was retrieved from the source-hash-guarded model jobs. All three ZIP archives were independently downloaded, SHA256-verified against GitHub, and inspected.

| Model | Artifact | Verified ZIP SHA256 |
|---|---|---|
| W8 | [12530584836](https://github.com/anyangle1409-code/animation-software/actions/runs/40023281618/artifacts/12530584836) | `47ee3a5d142862b41467ddea761d1f3011583a830b7c3410ff52e6646a6e991d` |
| V14 | [12531403099](https://github.com/anyangle1409-code/animation-software/actions/runs/40023281618/artifacts/12531403099) | `580e880030147f5163238681f23d0419145845e73d4c1c050ad648529ecb68dd` |
| R120 | [12531547374](https://github.com/anyangle1409-code/animation-software/actions/runs/40023281618/artifacts/12531547374) | `a0482e3d2986d8482085e3f838d60e39d5a2c7cef65d137846065000916b5902` |

Each report has its correct preserved `.blend` source hash, `original_source_unchanged: true`, and status `READ_ONLY_ANGULAR_ACTIVATION_CONTRACT_NOT_APPLIED_TO_POSE`. No model opened for writing.

## Crucial S7 custom-property override

The pinned source `scripts/original_v1_review_candidate_drives.py` at `025d5f28fa7eba2064fba565b1c9b60119cdd2cb` assigns the `HGPT_S7_DELT_` family a *nominal* start of 130°, **overridable** by `hgpt_s7_angles_start` on the rig. **All three recovered models have the actual saved override `hgpt_s7_angles_start = 95.0°`.**

Each of W8, V14 and R120, on both suffix sides, has exactly the same S7 seven-angle list:
`[110, 120, 130, 136, 145, 156, 166]` degrees. There are seven matching shape keys per side, and the rule can be evaluated without missing angle properties or count mismatches.

The 95° start is **a documented authored setting**, not automatically a defect. Its influence must be tested against the full motion/corrective response, not silently restored to nominal 130°. Such a change could regress existing design and is not authorized.

## What the saved rule predicts at the authored press targets

The unchanged source benchmark uses nine smoothstep-sampled press targets: sample0 **90°**, sample6 (t=0.75) **149.0625°**, sample8 **160°** of intended humerothoracic elevation.

For S7 family on **both** sides, the exact pinned piecewise-linear rule gives approximately:

| S7 key | At start 90° | At 75% target 149.0625° | At top target 160° |
|---|---:|---:|---:|
| `HGPT_S7_DELT_*_145` | 0 | 0.630682 | 0 |
| `HGPT_S7_DELT_*_156` | 0 | 0.369318 | 0.6 |
| `HGPT_S7_DELT_*_166` | 0 | 0 | 0.4 |

These values are **mathematical predictions using intended targets**, not readings of actual applied shape-key values during the saved benchmark. The distinct shoulder helper-bone rotation, axilla contribution, and deformation behaviour remain unmeasured. The S7_156/166 source meshes have significant local stored Basis offsets (see [verified ROI report](PHONE_VERIFIED_SHOULDER_SHAPE_WEIGHT_20261023.md)), but direction, activation and combined evaluated geometry are not established by scalar magnitudes alone.

## Other relevant families and nominal rule matching

- S1 shoulder start 90° with actual side-specific angles approximately `105, 120, 145, 160`.
- S5 bake start 60° with angles approximately `85, 110, 130, 145, 160, 172`.
- C1 arm/trunk extension start 18° with angles approximately `25.1, 37.965`. **C1 is driven by shoulder extension, not humerothoracic elevation**; do not substitute press elevation into the C1 rule.
- Saved as-loaded shape-key values highlighted in shoulder ROIs were zero; that is not the posed state.
- The first audit compared nominal degrees *exactly* and warned about negligible float noise (`104.999985°` versus the `_105` key suffix). This is a **reporting false alarm**, not a discovered mismatch. A follow-up script amendment uses a 0.25° *metadata naming tolerance* (not an anatomy tolerance), records the exact maximum discrepancy, and adds helper property inspection and authored press targets. **The amended run has not been verified yet**; the raw source values above are directly verified in 40023281618.

## Next read-only investigation

1. Verify the follow-up native job after the naming-tolerance and helper snapshot changes.
2. Record actual saved `hgpt_cap_fraction`, optional `hgpt_cap_fraction_ramp`, `hgpt_axilla_fraction` and relevant helper bones; compare to pinned `original_v1_shoulder_cap_helper.py` before attributing any deformation.
3. Measure *actual* S1/S5/S7 key activations and helper angles in the same press sample0/6/8 test rig using a wholly isolated, no-save pose pass, explicitly differentiating target and measured humerothoracic angles.
4. Inspect signed local displacement vectors and the flagged triangle ROI after posing. No geometry/weight/driver correction without new candidate evidence and owner scope.

Immutable reconstructive source bytes, validated skeleton, `ORIGINAL_v1`, production bridge, `PT_MODEL_VERSION 1.0` and Claude branches remained unchanged. Model and anatomical acceptance stays FAILED / NOT_GRANTED.
