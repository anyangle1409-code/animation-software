# G2d — moving GPU-skinned PNG-textured GLB primitives
**11 October 2026 • original first-party Chat Lane G implementation only • synthetic test data**

This stage combines existing first-party four-influence GPU joint-palette skinning (G2c PR #58) with strict embedded PNG source textures, material tints and UV0 (G1e/G1f PRs #61/#62) IN ONE moving, indexed WebGL2 source-mesh shader. It does not edit a skeleton, original human, CT/Blender model or production app.

## Implementation

- The original G1e parser separately validates all GLB source skin weights, inverse binds, UV0 coordinates, 8-bit embedded PNG, material indices, opaque base colours and 2..8 mesh primitives. Those bytes and source bone centres remain unchanged.
- Existing first-party GPU vertex code calculates four-weight skinned position and skinned source normals from a bounded RGBA32F joint matrix texture, with joint world/rest binding supplied explicitly; it never guesses laterality or adjusts human anatomy.
- The opt-in setSourcePngBatches(originalParts) locally copies the strictly checked source PNG bytes, uses native ImageBitmap to decode, validates decoded dimensions, and uploads RGBA8 textures at texture unit 1; joint palettes remain at texture unit 0.
- The new texturePreview:true render mode draws skinned original indexed meshes with source UV0 and GLB baseColor tint in the same shader, checks exact original source mesh and UV references, and refuses unprepared/altered source attachments. Default diagnostic UV0 rendering and source-normal preview remain unchanged. Source normal and texture display modes cannot be simultaneously selected.
- Resource disposal and WebGL context loss clear texture source attachments; no asset downloads, third-party rendering packages, URLs or clinical data are part of this change.

## Genuine browser tests

A project-created two-mesh, two-joint synthetic GLB contains two independently generated source PNG images (red and green) with genuine glTF material/UV/skin metadata. The Chromium smoke test advances 21 joint poses, checks actual browser GPU red/green fragment counts, verifies that the red and green pixel centroids both move horizontally with the source joint matrices, checks actual GPU transform-feedback skinned positions against separate CPU four-influence reference and saves a real GL framebuffer PNG screenshot.

The CI workflow also runs inherited GLB/UV/PNG/rig/normal tests and unchanged animation studio strict typecheck/build. Report the exact current-head pass/fail only after GitHub Actions finishes.

## Not yet achieved

This is not real human mesh, clavicle/scapula movement validation, realistic muscle and skin shape correctives, glTF colour-space-correct sRGB/PBR material, load-aware motion, approved anatomical ranges, Work's human body model, verified distribution rights, actual iOS GPU performance or full replacement of legacy Three.js studio/304 temporary instructional clips. These remain independent development and acceptance gates.

Next Chat task after passing CI: consume the early Work-approved PROVISIONAL original GLB and typed pose frame data through PRs #59/#60 when those exist, then fix genuine model format or skinning/rendering problems without relocating bones. Additional material, shape and equipment support should be guided by real model needs.

Master plan: https://github.com/anyangle1409-code/animation-software/blob/codex/shared-autonomous-master-plan-20261011/docs/HOME_GYM_PT_SHARED_AUTONOMOUS_MASTER_PLAN.md
