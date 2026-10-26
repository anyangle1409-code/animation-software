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

Two focused behaviors were observed RED before implementation and GREEN after: separation of stored/evaluated quantities and exact bilateral endpoint enforcement. Review hardening also rejects boolean/nonfinite activation masquerading as numeric evidence. Focused24/24, full267/267 diagnostic tests and7/7 replay guards pass.

Run `40374313339` at commit `cfd0e219723554ef29d6f140795afa1648e34937` completed SUCCESS 7/7. Both endpoint keys have `relative_key=Basis`, an empty vertex-group string, and zero stored-coordinate delta across all219,974 vertices. Clearing either key individually changes zero evaluated vertices and leaves the terminal residual exactly unchanged. Exact terminal state restoration passed.

Conclusion: bilateral S3_125 are unmuted, numeric value1.0, but stored-coordinate-equivalent to Basis and therefore no-op endpoint keys in this W8 source. The zero family effect is not bilateral cancellation. This may be an intentional endpoint that terminates S3 interpolation; it does not authorize deletion or source modification.

Pose artifact `12673313863` was independently downloaded, CRC checked and rehashed as `129ecc9bc07544e7f3bc0954cb12a531c90eb4e650ea03aa529c6d24db9cd4c2`;71 members/66 PNG/no `.blend`. After stripping only this new diagnostic and limitation, the prior report equals run40372539682.
