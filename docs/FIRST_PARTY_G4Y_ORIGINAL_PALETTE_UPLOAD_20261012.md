# G4y — genuine WebGL2 palette upload preflight (opt-in)

Adds `probeOriginalPaletteFloatUpload({makeCanvas})` as a separate first-party diagnostic on top of G4x. It checks basic WebGL2 capabilities in a temporary context, then requests a fresh separate context and attempts an actual `268 x 1` `RGBA32F` floating-point texture upload, matching the 67-joint × 4-texel matrix palette dimensions used by the existing first-party skinning shader. Checks `gl.getError()`, deletes the temporary texture and requests context loss to release resources. No private GLB bytes are loaded and no human mesh is drawn.

Five Node tests use a recorded stub context to verify the exact texture dimensions/data format, failure on GL upload error, allocation failure, missing capability and teardown. Node tests alone do **not** establish that the action succeeds on actual hardware. The code is not a default app component and does not alter model/feet/anatomy/animation, the PT App, rights or approved software baseline.

**Distinct remaining milestones:** real browser execution of this diagnostic, authentic private ORIGINAL_v1 GLB authentication, actual full-body 67-joint GPU neutral image/transform-feedback proof, biomechanical movement validation, release approval and iPhone battery/performance. No vendor rendering dependencies are introduced.
