# G4z shader compile/link diagnostic

12 October 2026; independent first-party Chat Lane G. Adds an **opt-in local-only WebGL2** vertex shader compilation/link diagnostic for the same technical class as the ORIGINAL_v1 67-joint matrix-texture palette: GLSL ES 3.0 vertex-stage `texelFetch`, highp sampler2D and four texels per bone transform. The shader is a minimal diagnostic, **not** the original full rendering shader, nor source-authenticated GPU proof. Temporary shader/program/context resources are released.

Five mocked WebGL2 Node regression cases cover missing context, success, compile failure, link or GL failure and disposal. The branch CI also executes existing palette-upload and device capability tests. No original private GLB, mesh, animation, PT App or Work-owned foot geometry has been modified.

Next blocking acceptance remains **actual native original 17,946-vertex/67-joint WebGL2 draw**, performance and visual review. Unit tests with mocks are not hardware GPU verification and cannot approve anatomy, biomechanics or release.
