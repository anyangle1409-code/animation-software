# Noncanonical rib 3D source-convention preflight — 10 October 2026

**Project:** Home Gym PT ORIGINAL-v1. **Base:** immutable whole-body anatomical audit 7761a12d684f576bf49a0bac7563d5b5ae9b8998, NOT main. This is a read-only, source-first diagnostic, **not a skeleton correction, rib mesh, full 3D rib, breathing motion or ROM certificate**.

## Why this is necessary

Work's real Blender 5.2.1 audit independently reproduced T001 spinal control centre-gap improvements, but ribs are still straight control rods. It confirmed no independently identified anatomical bone surfaces. The spine experiment did not fix the rib-10 anterior height residual (about +29.3 mm), rib head/tubercle surfaces, cartilage, or costal anatomy.

Primary source: [Holcombe et al., J Anat 2017](https://onlinelibrary.wiley.com/doi/full/10.1111/joa.12632), DOI 10.1111/joa.12632, section "Rib plane and orientation parameters". Each rib has its own plane and is transformed from a neutrally inferior-hanging configuration by successive **pump-handle, lateral swing, then bucket-handle** rotations. Bucket handle rotates about the already rotated longitudinal x-axis, with left/right sign convention. These angles describe the rib's STATIC orientation, not physiological motion or breathing range.

### Newly quantified unsafe shortcut

If published PH and LS level means were incorrectly treated as independent FINAL angles to orthogonal coronal/sagittal planes for a single vector, its lateral+anteroposterior components would require:

    sin(PH)^2 + sin(LS)^2 <= 1

Six of 12 independently averaged rib levels FAIL that shortcut: **1, 8, 9, 10, 11, 12**. Rib 12's mean LS is 94 degrees, another warning against treating every mean as an acute, independently defined line-to-plane angle. **This is not an error in the Holcombe source.** The published rotations are sequential; independently averaged model parameters are not simultaneous observations from a single human. It is the simple independent-angle transform that is unsafe.

### Newly added tools

- Immutable exact original model Git blob check (044da0b1896c342328b54d410db46f8139b673db), independent SHA-256 in report. Reject changed source bytes or line endings rather than silently accepting alternatives.
- Diagnostic proper orthonormal orientation frames for all 12 source mean rib levels on both anatomical sides, in explicitly stated HGPT frame (+X anatomical left, -Y anterior, +Z superior). The source rotation order and bucket-handle side convention are visible, but the actual patient/HGPT registration remains unverified.
- Explicit counterexample for the independent-angle shortcut, preserving the source model's correctness.
- Optional cubic Bernstein out-of-plane deviation basis for normalized **full rib arc length**, using the published equation: z(u) = 3 ZA u(1-u)^2 + 3 ZB u^2(1-u). Secondary direct methodology source: [Age-related changes in thoracic skeletal geometry of elderly females](https://www.tandfonline.com/doi/full/10.1080/15389588.2017.1309526), DOI 10.1080/15389588.2017.1309526. **ZA/ZB coefficients are not supplied by the pinned nine-parameter 2017 dataset** and are never invented or applied to a distal-only partial curve.
- Null physical bone surface, proximal rib, 3D out-of-plane coefficients and head/tubercle/contact fields; no canonical promotion.

This is intentionally a **frame hypothesis** rather than full source-to-HGPT proof. Neutral hanging reference, patient lateral-vector convention and signs require independent source-figure and Blender review.

## Reproducible commands

Use Python 3.11+ in this isolated worktree, without numpy or bpy:

    python -m unittest -v scripts/test_rib_3d_source_preflight.py
    python scripts/anatomy_fit/rib_3d_source_preflight.py

To write a new PRIVATE file OUTSIDE Git (must not exist):

    python scripts/anatomy_fit/rib_3d_source_preflight.py --out "C:\Users\YOUR_USER\Documents\HGPT-private-rib-frames.json"

Regression suite verifies real original source level values, all 12 x both sides, 6 unsafe shortcut cases, correct handedness, proper rotations, bad inputs, source tamper refusal, full-arc curve basis and nonpromotion.

## Laptop / Blender closure

1. Verify the 2017 reference rotation convention against Figure 2, patient ribcage lateral vector and actual T001 body views. Do not install an unconfirmed axis transform.
2. Independently resolve the 2016 proximal rib Eq. 2.18 conflict before generating full centrelines.
3. Obtain appropriate ZA/ZB, osseous 3D rib orientation, patient thorax registration, rib-head/tubercle, joint and cartilage surfaces.
4. Run source-surface tests, contact/clearance and compound pose checks with PR #24's actual Blender intake when real bone surfaces exist.

**Readiness unchanged: 0 READY / 9 PARTIAL / 3 BLOCKED.** No modification of a003/c001-c004, c005, Work/Claude files, production Blender scene, runtime bones or mesh.
