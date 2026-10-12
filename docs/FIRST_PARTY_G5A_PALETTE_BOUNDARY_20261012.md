# G5a — first and final joint palette address bounds

12 October 2026. Independent Chat Lane G work, stacked on G4z #94. The isolated first-party diagnostic GLSL 3.0 vertex shader now uses a dynamic uniform bone index, clamped to 0..66 and multiplied by four RGBA32F texels per matrix. Both first (0..3) and last (264..267) entries are addressable within the expected 268×1 palette. Source tests verify shader contains dynamic addressing and four contiguous matrix columns, and check exact last-texel integer bounds. Focused CI runs prior compile/link mock tests and palette-upload/device checks.

This deliberately does not modify the existing production full-body shader, original GLB, skeletal targets, foot mesh, Blender work, PT App or dependency policy. Node test verification **is not actual GPU execution**; hardware GLSL compile and authentic 67-joint full-body proof remain separately pending. This does not validate surface deformation or anatomical fitness.
