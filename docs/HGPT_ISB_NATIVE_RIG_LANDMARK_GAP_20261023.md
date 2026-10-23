# Home Gym PT — native rest-rig axes and ISB landmark gap analysis
**23 October 2026 — pinned native read-only evidence; anatomical certification NOT GRANTED.**

## Research basis

Wu et al., 2005, ISB Part II (shoulder, elbow, wrist, hand): https://pubmed.ncbi.nlm.nih.gov/15844264/ . The standard differentiates **humerus relative to scapula (glenohumeral)**, **scapula relative to thorax**, and **humerus relative to thorax** motion. These are not interchangeable coordinates; a single `shoulder_elevation` scalar cannot stand in for all three. For the shoulder girdle, anatomical segment frames depend on physically defined landmarks, not an armature's arbitrary bone roll.

Wu et al., 2002, ISB Part I (ankle, hip, spine): https://pubmed.ncbi.nlm.nih.gov/11934426/ . A named clinical joint angle must be measured in a defined segment/joint coordinate system; the existing rig's XYZ rotation channel alone does not meet this condition.

Senk & Chèze, rotation-sequence study (2006): https://pubmed.ncbi.nlm.nih.gov/16274906/ . Euler angle sequences can be singular or ambiguous; preserve original quaternions and explicit reporting conventions rather than interpreting one raw Euler component as a clinical joint motion.

**Permanent unbound landmark checklist:** [HGPT_ISB_LANDMARK_REQUIREMENTS_V1.json](anatomy/HGPT_ISB_LANDMARK_REQUIREMENTS_V1.json) covers **46 bilateral/midline named anatomical targets**, including thorax IJ/PX/C7/T8, scapular TS/AI/AA, clavicle SC/AC, humerus GH centre/epicondyles, radial/ulnar styloids, pelvis, femur, ankle and foot candidates. The lower-body/foot candidates are explicitly **not claimed to be exact ISB definitions until each is checked in the primary standard**. Every mesh vertex, model bone, coordinate frame and side-evidence binding is NULL, and every anatomical approval is FALSE. GH and femoral head centres require reviewed estimation methods rather than guessed bone-head positions.

## Read-only cloud Blender evidence

[GitHub Actions run 40029398965](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965), pinned commit `e5cd2c569261c229f82e3819603f5cc378abf15f`, **overall FAILED**. Three native Blender jobs W8/V14/R120 and the old cross-model comparison succeeded. The fifth localization job failed because one synthetic test searched the module docstring for `bpy.ops` and falsely interpreted the sentence `No bpy.ops` as a call. **73 tests: 72 pass, 1 false-positive test failure**. It was not a Blender failure or source mutation. The test now parses Python AST and inspects actual operator calls; [run 40030373550](https://github.com/anyangle1409-code/animation-software/actions/runs/40030373550) completed **SUCCESS across five jobs** after this fix.

All three new `rig_rest_axes_metadata.json` artifacts were downloaded from the first run and independently inspected:

| Model | Artifact ID | ZIP SHA256 (matches GitHub) | JSON member SHA256 |
|---|---:|---|---|
| W8 | [12534047239](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965/artifacts/12534047239) | `adaba1780dcde12b589f590bc6de7ae2227485471f9ff0817a56dff888188267` | `01ef8a7cf4eab8ea8eb29d2fcb2f5cd310ce8a936062624b06868a2e38b7b677` |
| V14 | [12534147742](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965/artifacts/12534147742) | `098c34ab14d8e14dbf21735b11808067df4296247dcc7efb7e9420b7b43545a9` | `4f4927fd0e31c6418cd78b5763f4450de574689247379bcd628361b5a1781998` |
| R120 | [12534222622](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965/artifacts/12534222622) | `17266fbc256cc775ce21c16b556d6a0fbff36499a1f2f78d05a6c058d6e56018` | `7a77b55f51f592eef42a293583b4974212e7594834644962b496c6b877acc13f` |

The source SHA256 fields match pinned preserved `.blend` hashes; `original_source_unchanged=true` for each. Each has **77 bones**, 58 quaternion-mode and 19 XYZ-mode pose bones, one enabled Armature modifier and **zero saved pose constraints**. The rest-bone names, parent hierarchy, body-local head/tail coordinates, bone-local X/Y/Z axes, pose rotation modes, constraint lists and modifier metadata were **identical in all three candidate reports** at recorded precision. This is an important reduction in debugging uncertainty: mesh/corrective differences between W8/V14/R120 need not be blamed on differing rest-bone matrices in this read-only inventory. **It does not establish identical animation behaviour, anatomical correctness or bone deformation weights.**

### L/R geometric symmetry proxy, NOT anatomy proof

In the W8 rest rig there are **35 paired `_l/_r` bone names**. The maximum reflected-X **head** residual is **2.433 mm** for `muscle_pec_l` vs `muscle_pec_r`, while their **tail** residual is about **0.00015 mm**. The corresponding body-local pec head coordinates are `(-0.02121650, -0.03761698, 1.42468703)` and `(+0.01878350, -0.03761698, 1.42468703)` metres. Other named paired head residuals were under ~0.00021 mm in this archived precision. This isolated asymmetry is a **targeted review flag**, not evidence that the pec attachment is anatomically wrong: these are authored helper controls, not reviewed anatomical muscle origins.

Anatomical left/right mapping still requires independently established model front/back and real segment landmarks. Bone labels `_l/_r` and signed X coordinates are insufficient by themselves.

### New repeatable cross-model guard

`scripts/cloud_body_analysis/compare_rig_axes.py` and `tests/test_compare_rig_axes.py` compare all three pinned reports, verify every unit/orthogonal bone-local basis, model SHA, no-unearned-approval flags, complete bone metadata and exact rig metadata fingerprints. The `compare-rest-audits` workflow now uploads `rig_rest_axis_comparison.json` and `rig_rest_axis_comparison.md` to the same phone-readable artifact. A mismatch is reported and fails the comparison job; matching metadata is explicitly labelled **NOT ANATOMICAL APPROVAL**. At time of authoring, the new integration job was **pending** and its success is not assumed.

## Next independent work

1. Map the unbound ISB landmark checklist to actual 3D geometry **only with evidence**: verified camera/front-back, visible bone surfaces and anatomical review. Do not use nearest vertex to a rig helper as an attachment.
2. Establish neutral pose, segment frames, rotation order and joint axes for scapula/clavicle/GH, elbow/forearm and pelvis/hip/knee/ankle. Review bilateral anatomical side separately.
3. Measure real *posed* native joint trajectories and deformation under shoulder press, curl/supination and squat, including elbow narrowing and axilla continuity. Compare original shape-key activation and cap helper rotations in memory. Use existing native triangle failure evidence, never relax thresholds.
4. Only after axis and landmark verification, test isolated joint and coupled motion envelopes, muscle paths, activation independent from pose, contact and skin deformation. Literature means are reference observations, **not** imposed joint stops.
5. Keep original W8/V14/R120 `.blend` source artifacts, existing Claude lane, PT-App and production untouched; no merge/deploy. Muscle highlighting remains deferred.

**Conclusion:** All three models demonstrably share the same **rest rig metadata** at recorded precision. Their **actual human joint axes and skin movement are not validated**. The next meaningful step is calibrating real anatomical frames and diagnosing actual pose deformation—not guessing limits from population tables.
