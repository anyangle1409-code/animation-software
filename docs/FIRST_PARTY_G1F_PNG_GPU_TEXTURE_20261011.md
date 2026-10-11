# G1f first-party native WebGL2 PNG texture rendering
**11 October 2026 • original source data preview • not production human model**

This software-only milestone extends the verified [G1e embedded source PNG decoder/GLB validation](https://github.com/anyangle1409-code/animation-software/pull/61) to native WebGL2 image sampling. It is an independent next step for the owner-approved Lane G plan, not Work's 3D skeleton, CT evidence, rig anatomy or Blender file.

The standalone first-party browser module takes **strictly validated G1e source batches** with embedded PNG image bytes and UV0. It locally creates browser ImageBitmaps from Blob bytes, with explicit source flipY and no premultiply or browser colour conversion, verifies source PNG header dimensions against decoded image dimensions, uploads RGBA8 to actual WebGL2 texture objects, sets the previously constrained linear clamp-to-edge sampler, and draws original source indexed triangles with the source UV0 and flat base-colour tint. Source includes multiple distinct model meshes and their textures in the same depth-tested frame. No image URLs, vendor media libraries, Three.js runtime, external download or user-supplied arbitrary remote textures are used.

Important limitations: this is **the original static mesh / supplied positions texture preview**, not GPU skeleton motion in the same new shader, morph-driven mesh correctives, glTF sRGB/PBR correctness or full image/compression support. The G1e source validator checks PNG signature/IHDR/CRC/chunk structure; Chrome's native ImageBitmap actually decodes the original PNG. G1e deliberately rejects all PNG ancillary chunks, palette, interlace, large textures, unknown extensions and non-clamp/nonlinear samplers until independently supported. A valid PNG might still be rejected under this restrictive early gate.

The dedicated actual Chromium test script creates original red and green 2×2 PNG images entirely in first-party test code with Node's built-in zlib and an independent CRC32. It embeds both PNG images in a genuine tiny binary glTF file, then tests the entire path:

1. Strict multi-mesh GLB G1e source PNG/material/UV data validation.
2. Browser ImageBitmap decode directly from the validated embedded bytes.
3. Actual native WebGL2 RGBA8 upload, source UV interpolation and indexed drawElements.
4. GPU readPixels from the framebuffer; verify independently that the two source images produce distinct red and green rendered pixels, no GL errors and original source bytes unchanged.

The CI workflow also checks inherited GLB/pose tests, vendor/network import restrictions and unchanged TypeScript Studio build. Only actual passing CI on the exact implementation HEAD proves this software gate; a vendor-free shader or procedural fixture does **not** prove final human exercise imagery. Source PNG skin/shorts/body texture rights remain Work and release-gate issues.

Next necessary engineering: connect the already proven GPU skinned position/source normal shader from [PR #58](https://github.com/anyangle1409-code/animation-software/pull/58) to validated PNG UV/material sampling **in the same moving mesh path**, with vertex+normal+UV/multi-mesh and GPU/CPU pixel parity. After that, consume Work's source-approved provisional ORIGINAL-v1 human GLB on the [PR #59/#60](https://github.com/anyangle1409-code/animation-software/pull/60) contracts; real shoulder/axilla, skin weights, whole-body biomechanics and device performance still require independent validation.
