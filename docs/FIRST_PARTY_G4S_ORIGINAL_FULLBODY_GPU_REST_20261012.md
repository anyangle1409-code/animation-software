# G4s — genuine ORIGINAL-v1 67-joint full-body native GPU rest bridge

12 October 2026 • **Chat Lane G, review-only** • parent [PR #85](https://github.com/anyangle1409-code/animation-software/pull/85).

## Progress

Unlike earlier 6-joint 18-mesh shoulder pilot tests, this is a native GPU source-bound entrypoint for Work's **actual ORIGINAL_v1 full-body**: one 17,946-vertex / 35,888-triangle body, 67 runtime skin nodes, preserved original source normals and six sparse shoulder corrective POSITION/NORMAL targets. Full-body reviewed GLB `HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb` is 1,495,720 bytes, mandatory source SHA-256 `d267dac344affb5d52c7155f8d0254794e818a8eab3ad54f7f263694f36c390d`.

`parseOriginalFullBodyReviewGLB` now owns a **private WeakSet-backed authenticity token** after verifying the real GLB bytes, original joints, hierarchy, all inverse binds, rest-world matrices, source normals and all sparse deltas. `prepareVerifiedOriginalFullBodyRestGpu` refuses user-authored JSON lookalikes, demands the EXACT original topology/joint/corrective count, preserves the six original morphs only at REST weight zero and supplies the original mesh, original normals and original source baseColor/double-sided material to the existing first-party GPU skinning renderer. A separate immutable **private-WeakSet** GPU preview is required by `renderVerifiedOriginalFullBodyRestGpu`: it cannot be forged by copying model-data claims from a website. One first-party WebGL2 draw is intentionally a REST-POSE DIAGNOSTIC, with basic two-sided Lambert lighting; source glTF PBR roughness is explicitly not simulated.

**No source UV is authored or claimed.** The existing WebGL2 shader requires a UV vertex attribute even for the untextured original material; it receives GPU-local zeros, but these are *not* a mesh edit or a purported original UV layout. The original Work glTF, runtime skeleton, 206-bone anatomical master, hands and feet remain byte-identical. No vendor dependencies or PT-App production media changes.

## Validation boundaries

GitHub CI verifies that fake SHA/audit/model objects cannot invoke the new GPU-rest draw, and previous source rig/GLB tests plus unchanged studio typecheck/build still pass. **Do not claim the full 67-joint original has been drawn or medically approved from those synthetic/guard CI checks.** The actual Work review model is available privately in the user's ChatGPT Library, not committed to GitHub or the CI checkout. Actual source-backed full-body WebGL2 screenshot/transform-feedback/CPU parity is the next hardware-gated task, and requires a secure rights-controlled transfer to a real browser runner or a verified local run. The older six-joint shoulder PR #79 GPU screenshots do not stand in for this requirement.

Work [PR #84](https://github.com/anyangle1409-code/animation-software/pull/84) independently owns the 30.9157 cm foot length/skeleton conflict and review-only toe skin-weight trial; neither issue may be solved by Chat silently modifying source foot mesh/joints.

## Example (inside an authenticated local preview only)

```js
const original=await parseOriginalFullBodyReviewGLB(
  exactWorkOriginalReviewGLB,{expectedSha256:knownOriginalSha});
const gpuRest=prepareVerifiedOriginalFullBodyRestGpu(original);
const renderer=createNativePaletteSkinnedWebGL2(canvas);
renderer.setSize(900,1200);
const proof=renderVerifiedOriginalFullBodyRestGpu(
  renderer,gpuRest,{eye:[2.5,1.35,4.5],target:[0,.95,0]});
// Renders original *REST* only, not source 206-control anatomical animation.
```

**Next:** the actual source file must pass this G4s pipeline in Chromium with measured source GPU/CPU skinned original normals/positions and three source-equivalent review cameras. Actual Work #84 weight-candidate optional body export is a distinct digest and MUST be treated as a different model rather than swapping one original SHA.
