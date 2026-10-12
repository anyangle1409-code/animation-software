# G4x: Native ORIGINAL_v1 vertex texture preflight

Adds a missing capability gate to G4w: the native first-party 67-joint RGBA32F vertex shader reads bone matrices from a texture, requiring at least one **vertex-stage texture image unit**. The earlier basic WebGL2 probe checked palette texture width and vertex attributes but could report an unsupported device as basically capable even when vertex texture samplers were unavailable.

The new `MAX_VERTEX_TEXTURE_IMAGE_UNITS` check is strictly additive and fails closed for zero, invalid or unavailable values. Dedicated positive/negative Node regression cases and scoped GitHub CI cover it. The probe still takes a caller-selected local temporary canvas; never loads private GLB bytes, never touches the deployed PT App or Work-owned model.

**Not a shader-compile/draw proof:** even passing WebGL2 texture/attribute checks does not validate actual ORIGINAL_v1 neutral GPU output, animation, biomechanics, mesh proportions or release readiness. No changes to anatomical geometry or existing exercise media.
