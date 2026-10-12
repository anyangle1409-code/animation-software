# G4w — original local GLB first-frame camera consistency

**12 October 2026 · Chat Lane G · draft / nonrelease.** This branch stacks on [G4v PR #89](https://github.com/anyangle1409-code/animation-software/pull/89) (all five exact-head CI workflows succeeded). It makes the viewer respect camera changes that occur during an asynchronous owner-selected ORIGINAL_v1 GLB file read and exact SHA validation.

## Problem
Previously the local DOM adapter passed `cameraSelector.value` when beginning `File.arrayBuffer()`. Changing the selector before loading finished could cause the first GPU frame to draw from that earlier camera.

## Fix
`openOriginalFullBodyOwnerLocalReview` keeps its original validated default `view` and adds an optional synchronous `currentView` callback. The DOM adapter passes a closure reading the present selector. The initial camera selection is resolved **after** exact SHA and G4s preparation and immediately before the first G4t-authenticated WebGL2 draw; the selected view still passes the existing five-camera allowlist and the cancellation guard. This avoids a false first-view result without double-reading 1.5 MB of private source data or weakening original rig/morph/rights gates.

## Evidence limitations
Node regression tests check provider input rejection before reads, no callback invocation before source SHA, and camera changes while loading without fake GPU success. The original GLB is deliberately absent from public Git; tests do not prove actual WebGL2 hardware display. Exact-head CI includes inherited source SHA/immutability and studio typecheck/build. This is a review-only input correction and neither changes Work's anatomical skeleton/foot 30.9157 cm nor approves motion, original rights, released animations or the production app.

Next: authenticated original private GLB on a WebGL2-capable machine for real 5-camera PNGs, numerical body palette readback and visual foot/shoulder review; do not mark functional anatomy approved from a static viewer.
