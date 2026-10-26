# W8 S3 stored-coordinate and individual-effect audit — 2026-10-26

## Purpose

Native evidence shows both terminal S3_125 keys at value `1.0`, unmuted, while clearing both changes zero evaluated vertices at the reset skeleton. This diagnostic distinguishes three possibilities without editing the source:

- the endpoint keys store no coordinate delta relative to their actual relative keys;
- left and right evaluated contributions cancel when cleared together;
- stored deltas exist but another Blender dependency prevents an evaluated effect in this condition.

## Method

- Require exactly `HGPT_S3_SHAPE_l_125` and `HGPT_S3_SHAPE_r_125` as the active S3 endpoint keys.
- For each key, read its actual `relative_key`, optional vertex-group string, and stored coordinates. Measure stored local-coordinate delta to the relative key across the complete key topology.
- Clear each endpoint key individually at the protected reset-skeleton terminal state. Measure evaluated geometry against both the benchmark reference and the observed terminal mesh.
- Before and after each evaluation, require the selected key to remain exactly zero, the skeleton and all other key values/mutes to remain fixed, then restore and verify exact pose/key/evaluated geometry.
- Never save a `.blend` or convert stored-coordinate differences into anatomical deformation claims.

## Interpretation gates

Stored key coordinates are authoring data, not evaluated skin deformation. Individual-clear effects are marginal runtime effects in the presence of every other active terminal corrective. Neither establishes tissue identity, anatomical correctness, skeletal-weight quality, or repair suitability.

## Verification state

Two focused behaviors were observed RED before implementation and GREEN after: separation of stored/evaluated quantities and exact bilateral endpoint enforcement. Review hardening also rejects boolean/nonfinite activation masquerading as numeric evidence. Focused24/24, full267/267 diagnostic tests and7/7 replay guards pass locally. Native values and artifact hashes are pending.
