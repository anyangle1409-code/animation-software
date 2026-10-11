# Lane G1c — first-party glTF UV0 source coords → live WebGL2 fragment interpolation

**11 October 2026 · diagnostic-only project-authored mesh data · DO NOT represent UV coordinates as approved ORIGINAL-v1 human skin or texture support**

## Implementation

- `src/viewer/firstPartyGlbUV0.mjs`: first-party, finite, bounded, read-only GLB embedded BIN `TEXCOORD_0` accessor reader, supporting glTF `FLOAT VEC2`, normalized unsigned BYTE VEC2, normalized unsigned SHORT VEC2 with strictly checked accessor layout, byte/alignment/stride, binary bounds and per-primitive vertex count. UVs are preserved in source glTF convention (no invented V flip), range restricted to magnitude <=1024. Does not load, fetch, decode or create any image/texture.
- `src/viewer/firstPartyGlbSkinnedBatches.mjs`: new explicit opt-in `allowSourceUV0:true`, requiring UV0 on EVERY skinned primitive. Decodes/validates UV0 while keeping source bytes untouched, removes this single previously unsupported attribute **only from the temporary copied single-primitive GLB**, passes every mesh geometry/joint weight/indices/inverse bind through inherited strict original validator, and confirms UV vertex-count parity. All unknown higher UV sets, textures, extension/media/assets/morphs remain rejected. Compatible with independently verified source matte RGBA material mode, but the UV0 diagnostic shader is separate.
- `src/viewer/firstPartyUV0WebGL2.mjs`: original WebGL2 shader and typed attribute/index GPU lifecycle. Source TEXCOORD_0 survives interpolation to a diagnostic fragment `vec4(clamp(uv,0..1), 0.14, 1.0)`. Atomic validation before a single frame clear, up to 8 independently skinned indexed mesh parts, disposal and context-loss recovery. **This is a visual UV-coordinate diagnostic, not actual texture rendering, PBR, original human shader/material, inverse handedness conversion or skin release approval.**
- Original `tests/support/buildSyntheticUV0Glb.mjs`: creates distinct project-authored two-mesh test geometry with separately embedded f32/int UV accessors in the GLB BIN; no purchased character, restricted CT, natural-human texture or third-party embedded assets.
- `tests/firstPartyGlbUV0.test.mjs`: fail-closed tests for normalization, source layout, invalid buffer metadata/stride, mismatched vertex count, nonfinite/extreme coordinates, second-mesh missing UV, unexpected UV1/joint influences, forbidden images, unchanged source bytes and fake GPU resource/camera/context lifecycle.
- `scripts/verify-first-party-uv0-browser.mjs` & `.github/workflows/first_party_glb_uv0_webgl.yml`: actual headless Chromium native WebGL2 tests two distinct GLB-sourced UV regions in one depth frame, confirms simultaneous **red-channel dominant and green-channel dominant** pixels via `gl.readPixels`, with animated original four-weight CPU bone skinning from verified explicit bind names and palette order. All previous source-owned GLB/CPU/native GPU tests, editor typecheck/build and no-vendor source checks also run in CI.

## Explicitly absent

- Original model's accepted real-world skin/muscle/rig geometry, certified source rights, clinical anatomical correctness;
- glTF texture arrays, sampler state, image/PNG/JPEG decode, NPOT behaviour, actual baseColorTexture handling, alpha blending/cutout, metallic-roughness PBR and normal tangent maps;
- original GPU joint palette/vertex skinning, morph corrective shapes, whole-body original exercise appearance, third-party-free **production** editor with Three removed;
- any modifications to Work W1–W7 Blender/CT registration, c001–c004 candidates, a003, CP1 anatomical Gate6, or existing PT-App media placeholders.

These restrictions must not be relaxed merely to make a complicated production GLB load. The original `three` dependency and current editor remain unchanged while critical parallel Work anatomy effort proceeds. After verified UV path, the next G1 task is bounded source-owned texture image/PNG handling; G2 GPU palette skinning can run independently on original synthetic meshes.

**Anatomical readiness remains historically 0 READY / 9 PARTIAL / 3 BLOCKED until Work demonstrates change from independent source evidence.**
