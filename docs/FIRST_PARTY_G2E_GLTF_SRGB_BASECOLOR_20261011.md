# G2e — glTF sRGB baseColor transfer in native moving GPU skin

**11 Oct 2026 • Home Gym PT, independent Chat-owned first-party Lane G renderer.** This milestone builds on the verified G2d moving PNG/textured skin shader of [PR #63](https://github.com/anyangle1409-code/animation-software/pull/63). It is a narrow **colour-correctness preview**, not a human/medical/character acceptance.

## Why

The source GLB embedded PNG baseColor texture contains sRGB-encoded channels while the glTF baseColorFactor represents **linear** material colour. Multiplying encoded 8-bit channel values directly by the factor, as in the earlier diagnostic preview, is incorrect. For example, a 247/255 red texel and linear factor .5 is roughly **182/255** when correctly transferred back to sRGB, NOT **124/255** from encoded-byte multiplication.

## First-party change

- The native GPU skinning WebGL2 shader now supports an explicit **opt-in** glTF sRGB baseColor path while preserving the old unaltered source UV, source normal and legacy RGBA8 texture/pose diagnostic modes.
- New setSourcePngBatches(originalParts, {colorSpace:'gltf-srgb'}) stage uses strictly validated local G1e original PNG bytes, native ImageBitmap with imageOrientation flipY, premultiply none, browser colourSpaceConversion none, and WebGL UNPACK_COLORSPACE_CONVERSION_WEBGL NONE. It uploads these source textures as WebGL2 SRGB8_ALPHA8 on texture unit 1; the native float32 original bone-palette remains on unit 0.
- The GPU automatically converts the sRGB texture samples to **linear**, applies the original validated material baseColorFactor in linear, and the GLSL piecewise IEC sRGB output function encodes the unlit result for the ordinary RGBA8 screenshot/framebuffer. The output conversion deliberately does **not** purport to implement HDR, display-P3, tone mapping, physically based BRDFs or compositing.
- renderBatches(..., {texturePreview:true, colorManagedTexturePreview:true}) is required for these uploaded sRGB textures. A legacy RGBA8 source cannot be rendered through the managed shader, and a managed source cannot use the legacy direct-byte tint. Unsupported colour modes fail closed. No automatic conversion or quiet backwards change of previous preview semantics.
- The unchanged source GLB geometry, material metadata, rig joint centre/axes and source texture bytes are not modified; neither external files nor third-party runtime modules are loaded.

## Browser acceptance test (synthetic original fixture)

A generated two-skinned-mesh binary GLB has two embedded RGB PNGs created solely by test code, with one material's factor set to linear [.5,.5,.5,1] and its source red channel exactly 247. Real Chromium performs native GPU drawElements and readPixels in both the **legacy** and **managed** renderer modes in the same canvas, measuring mean red output against independent JS piecewise sRGB EOTF/OETF oracle rather than comparing two copies of the shader.

The test then animates eight subsequent frames in the managed mode and verifies that the actual red texture remains colour-correct while the skinned triangle's red centroid moves horizontally. It also asserts wrong mode/texture internal format pairs are refused, whole source GLB bytes stay unchanged, both source textures remain visible, no WebGL errors/browser exceptions/network third-party fetches, and produces a phone-viewable actual browser framebuffer PNG and machine report artifact. CI also repeats G2d GPU/CPU four-weight pose parity and unchanged studio strict typecheck/build.

**Only mark software milestone VERIFIED once the exact branch-head GitHub CI is fully green.**

## Important unchanged blockers

The original character/Blender geometry from Work has not yet been imported; the proof is synthetic two-joint texture sampling, NOT realistically shaped clavicles, scapulohumeral rhythm, shoulder/axilla correctives, physiological motion under load, original skin normals under all lighting, texture asset rights, real phone PBR/material quality, or release-grade first-party studio replacement. Work owns anatomical shape and human movement validation; Chat owns format handling and rendering.

Next candidate Lane G tasks: material/lighting/normal/sRGB integration beyond unlit source baseColor, targeted real Work provisional GLB importer gaps once Work publishes a safe model, and eventual native PT-App functional parity with zero shipped third-party sources.
