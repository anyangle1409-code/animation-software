# G4w — ORIGINAL_v1 WebGL2 device capability preflight

**12 October 2026.** An independent Chat Lane G optional first-party diagnostic on top of G4v PR #89. Nothing is deployed or automatically called. Work owns ORIGINAL_v1 source anatomy and foot/deformation work.

`probeOriginalFullBodyWebGL2({makeCanvas})` takes a caller-supplied factory for a fresh temporary local canvas, asks only for WebGL2, checks whether the texture size can hold the original 67-joint × four-texel matrix palette (268 texels) and whether five vertex input attributes are available. It returns a bounded structured reason when capabilities are absent and voluntarily loses its temporary context where supported. It never reads the review GLB, sends network requests, modifies a live rendered canvas, runs animation, enables fallback renderers, asserts anatomical approval or proves the original model was GPU drawn.

Six Node tests exercise context unavailable, too-small palette, too-few attributes, context release, successful non-approval and thrown context errors. Dedicated exact-head GitHub Actions workflow also repeats the existing G4v local-load cancellation tests.

**Critical limitation:** Passing a basic device capability probe does not guarantee shader compilation, WebGL2 RGBA32F texture upload, original GPU skeletal rendering, iOS battery/performance or real 67-joint neutral screenshots. Source SHA, actual full-body GPU neutral proof and accepted human movement remain separate release gates. This diagnostic should only be integrated into an optional review UI after real device confirmation. No private body mesh assets or medical CT are republished.
