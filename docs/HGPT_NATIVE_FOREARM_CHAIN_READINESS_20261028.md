# Native forearm skeletal-chain readiness — 2026-10-28

## Purpose

Before any elbow-flexion or pronation/supination pose trial, establish what the existing pinned skeletal inventory can actually support. This is a read-only hierarchy audit. It does not bind bones to radius/ulna anatomy, identify anatomical left/right, calibrate ISB axes, or move a model.

## Independently checked evidence

Historical run `40029398965` is still **FAILED overall** because its read-only source test falsely matched `bpy.ops` text in a docstring. That does not turn the run green. Its three successful model-inspection artifacts were independently downloaded again and passed ZIP CRC and GitHub SHA256 checks:

| Model | Artifact | ZIP SHA256 | Rig-member SHA256 |
|---|---:|---|---|
| W8 | `12534047239` | `adaba1780dcde12b589f590bc6de7ae2227485471f9ff0817a56dff888188267` | `01ef8a7cf4eab8ea8eb29d2fcb2f5cd310ce8a936062624b06868a2e38b7b677` |
| V14 | `12534147742` | `098c34ab14d8e14dbf21735b11808067df4296247dcc7efb7e9420b7b43545a9` | `4f4927fd0e31c6418cd78b5763f4450de574689247379bcd628361b5a1781998` |
| R120 | `12534222622` | `17266fbc256cc775ce21c16b556d6a0fbff36499a1f2f78d05a6c058d6e56018` | `7a77b55f51f592eef42a293583b4974212e7594834644962b496c6b877acc13f` |

Each artifact reports the exact pinned model source SHA, original source unchanged, 77 bones, and no anatomical/ISB/side/ROM approval.

## Result

For both authored suffixes in all three models, the recorded chain is:

`upperarm_{suffix} -> forearm_{suffix} -> hand_{suffix}`

Two deforming helpers, `forearm_tw0_{suffix}` and `forearm_tw1_{suffix}`, are both parented to the one `forearm_{suffix}` control. The hand is also directly parented to `forearm_{suffix}` rather than through either helper. No radius- or ulna-named skeletal control is present. The selected hierarchy/coordinate/rotation-mode subset is identical across W8/V14/R120, fingerprint `3f623b6bb994ede5cbdc875cb40ef645072ae49a3c073bb0872f54119dc0ac52`.

Status: `BLOCKED_NO_INDEPENDENT_RADIUS_ULNA_CONTROL_EVIDENCE`.

This does not prove the mesh lacks radius/ulna form, nor that the twist helpers cannot distribute an authored forearm twist. It establishes only that the pinned skeletal inventory does not provide evidence for separately bound radius and ulna controls. A generic radioulnar test must remain blocked until segment landmarks/frames and control semantics are independently established.

## Implementation and limits

- `scripts/cloud_body_analysis/forearm_chain_readiness.py` validates the three pinned inventories, exact bilateral authored hierarchy, finite coordinates, empty recorded constraints, and consumed member hashes. It emits JSON/Markdown without touching Blender or model assets.
- Six initial synthetic regressions were observed RED before implementation and GREEN after. Fresh-context review then found three Important evidence-integrity gaps: hash and parse used separate reads; radius/ulna-named controls could coexist with a false “not observed” conclusion; and helper/cross-model semantic drift did not fail closed. Three additional regressions reproduced these cases RED. The hardened audit reads each member once for hash+parse, recognizes `_`/`.`/`-` name separators, rejects unexpected radius/ulna controls, requires exactly two deforming quaternion twist helpers per suffix, and rejects cross-model chain mismatch. Focused `9/9` and actual pinned replay PASS.
- The workflow comparison job will run the audit against the current run's three native inspection artifacts. Cloud execution is pending; the historical replay above is actual pinned evidence, not a synthetic anatomy result.
- No elbow flexion, pronation/supination, skin deformation, muscle/tendon behavior, return-to-neutral, contact, or exercise acceptance was tested. Population ROM means remain descriptive and are not limits.
- No original `.blend`, skeleton, weights, shape key, permanent muscle ID, attachment, highlight, PT-App, production asset, version, merge or deployment changed.
