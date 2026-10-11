# G2c — first-party GPU-skinned original source normals

**11 October 2026 · standalone diagnostic human-renderer prerequisite · no production or clinical approval**

Stacked onto the previously verified strict-source NORMAL GLB [PR #57](https://github.com/anyangle1409-code/animation-software/pull/57), first-party matrix palette skinning PR #55 and earlier native GLB/UV/material milestones, without modifying Work's private CT, Blender or anatomical candidate work.

## Implemented

- `src/viewer/firstPartySkinnedNormalReference.mjs`: independent project-owned CPU *reference only*, validating finite near-unit source normal per vertex and computing `normalize(sum_i(weight_i × mat3(worldPose_i × inverseRestBind_i) × sourceNormal))` for exactly four indexed bone influences. Refuses near-zero vector cancellation. Separate from existing CPU positional skin reference and GPU shader.
- `src/viewer/firstPartyGpuPaletteSkinning.mjs`: new original `aNormal` vertex attribute (location 4) and actual source-normal **bone-matrix-weighted vector output** `vSkinnedNormal` in WebGL2 GLSL. Maintains real GPU position skinning and indexed draw. `renderBatches(..., {normalPreview:true})` now *strictly requires source unit normals on every mesh*, and shows a simple single-direction diffuse grayscale diagnostic; default UV0 preview mode retains previous behaviour. This is NOT PBR or physically accurate skin light scattering.
- Same real GPU program exports **two separate transform-feedback vertex varyings**: skinned position and skinned normal. Source input is deindexed only for WebGL2-compatible parity capture, never CPU-skinned in the rendering path. Both streams must be captured from the actual GPU, then compared against independent CPU normal/position reference; original normal-mode default is not automatically enabled by missing source.
- Adversarial Node tests cover neutral pose, rigid 90° source normal rotation, fractional multibone blends, degenerate cancellations, invalid non-unit source data, cross-part atomic rejection and distant joint index 127 in a 128-bone palette.
- Actual Chromium browser must compare 20 frames × 2 source GLB mesh normals to CPU LBS with numerical tolerance <1e-5 source test model units, plus separate 128-bone four-nonzero-influences normal check, GPU framebuffer bright/dim source normal lighting pixel readback, zero GL/browser/vendor exceptions.
- Full existing studio TypeScript + build regression is retained. No Third/React/R3F modules added; production editor continues using Three until real skin texture/deformation/performance/interaction parity and approved ORIGINAL-v1 character.

## Deliberate limitations

Only original synthetic 2-triangle source glTF models and source-authored normals used. This **approximates normal transformation using four weighted rigid joint rotation matrices**, not exact normals of the deformed skin surface under all deformations, nor bone muscle bulge, blendshapes, normal maps, tangent-space/material UV textures, directional irradiance or anatomical validation. Genuine shoulder/axilla/chest realism and original skin weights remain Work-owned, subject to independently approved real human-source evidence. Current anatomical readiness remains unchanged unless Work reports verified data.

Do not merge this draft into production until all dedicated Node/browser normal parity tests pass. This software gate alone does not permit removing Three.js or the remaining PT-App temporary exercise media.


## Live Chromium and independent mathematical verification

Implementation head `7670e05795f63ab232441f324ed3fff7c6f01e9d` tested on [GitHub Actions run 38139395007](https://github.com/anyangle1409-code/animation-software/actions/runs/38139395007): **all three jobs PASS**, **132/132 original zero-npm-install Node tests**, full unchanged editor TS typecheck + production build PASS. No vendor runtime module imports.

Real Chromium/WebGL2 GPU shader rendered 20 normal-lit frames and made 40 genuinely indexed two-mesh draw calls, then measured **41 actual transform feedback triangle-normal samples** against a separate CPU four-bone directional normal oracle. Worst source-space synthetic absolute component deviation = **1.1920928955078125e-7**. Separate 128-bone RGBA32F palette, four-nonzero-influences normal test using indices 0/31/64/127 had **0 recorded maximum component deviation**. GPU normal length stayed between **0.9999999157 and 1.0000001054**.

The shader ran a *diagnostic*, NOT physically based Lambertian brightness mode. Same 960×540 GPU framebuffer contained **7,680 bright +Z pixels and 7,813 medium-bright +Y pixels** from different source-authored normals. Browser GL error=0, browser exceptions=0, console errors=0 and Three/React/R3F vendor requests=0. [**Project-owned original synthetic screenshot and machine-readable GPU normal parity report**](https://github.com/anyangle1409-code/animation-software/actions/runs/38139395007/artifacts/11702331239).

**What remains unverified:** exact surface tangent/bitangent/normal-map transforms, all human muscle bulge and skin discontinuities, photorealistic PBR, source texture sampling, mobile/WebGL2 device performance, complete 206-bone anatomical physical correspondence and original model intellectual-property release, app integration, editor interaction/raycast/camera parity, and final removal of the production editor's Three.js dependency. No source human skin mesh or CT data used by this GPU test.
