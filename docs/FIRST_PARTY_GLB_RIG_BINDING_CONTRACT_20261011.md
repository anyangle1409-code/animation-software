# First-party GLB → canonical rig binding contract — 11 October 2026

**Status: NUMERICAL / SOURCE-COMPATIBILITY DIAGNOSTIC ONLY. Not a validated human model, final canonical bone target or real anatomical frame approval.**

This is independent renderer development stacked on [PR #43](https://github.com/anyangle1409-code/animation-software/pull/43). Work's CT/Blender skeleton and original mesh investigations stay entirely separate. No original model, uploaded/purchased mesh, patient CT, or Blender source was edited or moved.

## What this directly implements

`src/viewer/firstPartyGlbRigBindingContract.mjs` adds a project-owned dependency-free **explicit glTF GLB skin-palette → named runtime rig** mapping and quantitative rest-binding check between the restricted GLB2 decoder and the first-party four-weight LBS/native WebGL2 rendering implementation. It supports a *complete explicitly listed input palette* (one to 128 named joints from the source mesh), not a default guess based on bone spelling.

Checks:
1. The model must have been parsed through the already strict, bounded GLB2 geometry loader. Every source skin joint name must be unique and explicitly mapped once, and the allowed rig's canonical names must be unique. No extra or missing source mappings, fallback mappings, guessed hand laterality, duplicate rig targets, guessed `_l`/`_r` side reversals or prototype-property collisions are permitted.
2. User-provided **actual canonical rig rest-world bone transforms** must exist for every assigned bone, contain finite, well-formed column-major **proper rigid** 4×4 matrices (no scale, shear, reflection or unverified change of coordinate basis), and preserve the source GLB inverse-bind matrices.
3. Validate **`rigRestWorld × sourceInverseBind = identity`** for each skin joint within an **engineering numerical tolerance 0.0001**, not a scientifically established skeletal-anatomy tolerance. Mismatch stops the candidate; it never moves a bone, renames the production rig, modifies the mesh or attempts arbitrary re-scaling.
4. Emit the matching *original source skin joint order* and an explicit `packMappedWorldPalette` to convert subsequent named posed rig-world matrices into the exact packed order expected by the first-party skinning engine. This also checks matrix validity each frame; shuffled object key order cannot silently change skin targeting.
5. Preserve unambiguous **NO ACCEPTANCE** flags: numerically matching a mesh bind to a caller's rig matrices is *not* independent proof of physical scanner→Blender units, anatomical bone length/endpoints, glTF hierarchical transform correctness, side labeling, model rights, full-body deformation, muscles/skin or production acceptance.

First-party adversarial tests: `tests/firstPartyGlbRigBindingContract.test.mjs` checks exact source joint coverage, unmapped/duplicate/unknown identities, malformed/nonrigid/sheared/reflected/rest-displaced matrices, replay pose ordered palette and true decoded GLB → CPU LBS deformation. Both binary data decoder and 3D skinning/GPU code remain dependency-free.

The **real Chromium/WebGL2 regression** `scripts/verify-first-party-glb-browser.mjs` also now runs the original synthetic GLB through explicit name matching and inverse-rest-bind verification, packs posed matrices in validated GLB joint order, and draws indexed deforming triangles in a native browser without requesting any Three/React/R3F runtime module. The synthetic source GLB purposely labels `test_upperarm_l` and `test_forearm_l` and maps them explicitly to nominal `upperarm_l`/`forearm_l` for a **controlled identity-rest test only**; they are not imported or accepted human character bones.

## What is still blocked for the actual human character

- The original Home Gym PT male skeletal coordinates/neutral pose and authored ORIGINAL-v1 GLB body source must both be independently accepted.
- Per-bone GLB node hierarchy/rest transforms, canonical physical coordinate frames and actual matching source inverse bind matrices must be established, not assumed. A model with different rest alignment must fail this stage until a legitimate independent transform/retarget implementation is measured and approved.
- Full mesh including material, UV/normal, submesh, GPU palette skinning, corrective shape keys, dynamic shoulder/chest/armpit, contact anatomy, scene interaction/camera and device/browser performance must be implemented and verified before removing the remaining separate animation-software `three` package.
- No claim that test-model skinning proves anatomical correctness, model rights or production appearance. The PT-App's own existing zero-npm dependency state is untouched; its 304 temporary videos remain until first-party exercise replacements are ready.

**Skeleton readiness remains 0 READY / 9 PARTIAL / 3 BLOCKED.** The completed wrist/foot source scan, CT viewer and spine evidence should not be redone for this software task.
