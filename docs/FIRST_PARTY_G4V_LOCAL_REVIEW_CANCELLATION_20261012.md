# G4v — Cancel stale ORIGINAL-v1 local review loads

**2026-10-12 · Chat Lane G · DRAFT / PROTOTYPE ONLY**  
Stacked on the first-party owner-local original review entrypoint [G4u PR #88](https://github.com/anyangle1409-code/animation-software/pull/88). Changes no Blender files, original source mesh, 67-joint skeleton, anatomical targets, historical foot measurements, licence permissions, PT App media or release flags.

## Problem and reproduction

The existing optional `bindOriginalFullBodyOwnerLocalControls` starts an asynchronous `File.arrayBuffer()` and source SHA/rig parsing. When the owner changes the selected file or disposes the viewer during a slow pending read, a previous asynchronous callback can continue and publish an obsolete status or try to initialise/render a model after that selection was revoked. A lexical `session` reference did not discriminate concurrent completion order.

## Fix / boundary

- A monotonically increasing file-selection generation invalidates every older async callback, preventing stale completion from updating the UI.
- A native `AbortController` cancels the pending `openOriginalFullBodyOwnerLocalReview` call; cancellation is checked *before read*, *after awaited file read*, and *after awaited full SHA/source validation*, before creating WebGL2 or drawing the 17,946-vertex original.
- Newer choices and explicit disposal invalidate and abort older requests; disposal is idempotent, removes DOM listeners, frees any active renderer and marks the UI closed.
- A resolved session from an obsolete callback is disposed rather than installed (defence-in-depth).
- This does **not** promise to interrupt the browser's already ongoing `File.arrayBuffer()` itself or a synchronous GPU draw; the guarantee is no GPU call after an abort observed at an asynchronous boundary.
- Exact original file-size/SHA, rest-only six-zero-morph posture and 67-joint source / G4t post-validation remain unchanged; no synthetic model substitution, third-party renderer or background network request.

## Verification

Dedicated Node regression tests cover (1) already-aborted file, (2) cancellation during pending asynchronous file read, (3) clearing a file choice while a read is pending, (4) disposing during pending read, (5) rejecting an invalid optional cancellation signal. The inherited G4u source SHA/input tests, G4t immutable source-buffer tests and G4s GPU REST input tests run in the new branch-specific CI workflow, with independent studio typecheck/build.

**Acceptance boundary:** Passing those tests establishes cancellation guards and source safety on stubbed file bytes; it does **not** constitute authenticated ORIGINAL-v1 full-body WebGL2 drawing on real hardware, verified human anatomy, corrected 30.9157 cm feet, clinically valid animation, rights approval, native iPhone testing, or customer-ready PT exercise preview. Real GPU proof and original Work movement/mesh acceptance remain blocked independently.

Next safe Chat task after exact-head CI: tighten owner-local diagnostic output for genuine device capability failures and prepare privacy-preserving native GPU evidence recording once authenticated original GLB and WebGL2 hardware are available. Do not deploy this opt-in prototype without appropriate review.
