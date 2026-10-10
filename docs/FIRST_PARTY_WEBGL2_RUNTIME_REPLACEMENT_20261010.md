# First-party WebGL2 renderer replacement — starting now, isolated proof stage

**Owner objective:** the Home Gym PT standalone animation system must run on its own application-owned runtime, without Three.js or other third-party libraries in the shipped PT product. Keep Blender, scientific papers, original CT surfaces and development tooling separate from the final executable.

## Audit before work

On the live animation software branch, `package.json` still declares `three ^0.180.0` as one runtime dependency. Its remaining import is isolated at `src/core/threeRuntimeBoundary.ts` (the migration allowlist explicitly permits **at most one** `three` direct import). React and R3F imports have already been reduced to zero. The real live studio uses a first-party DOM host, state, frame scheduling and FK evaluator but the actual 3D renderer, scene entities, materials, texture processing, GLB character and GPU skinning are still backed by Three via the gateway. Therefore deleting the package right now would break the editor's visible model, interactive tools and exercise demonstrations.

## Executed stage: first native GPU renderer, opt-in proof

Added:
- `src/viewer/firstPartyWebGL2SkeletonPreview.mjs`: project-authored **WebGL2 GPU shaders**, shader compilation/link gates, vertex arrays and GPU buffers, explicit resource disposal and restored-context re-creation. Implements independent column-major perspective/view/projection, 3D FK bone endpoint packing, direct GPU line drawing via `gl.LINES`. No Three.js, React, shader library or new dependency.
- `src/viewer/firstPartyWebGL2SkeletonPreview.d.mts`: typed API into the TypeScript studio, no vendor types.
- `src/viewer/nativeWebGL2SkeletonPreviewRuntime.ts`: uses the **existing first-party exercise clip resolver, IK/constraint pose evaluation, studio playback state and HgSceneLifecycle** to feed native GPU points at animation-frame cadence. This is live actual body skeleton movement, not a static illustrative shape.
- `src/viewer/firstPartyViewportDom.ts`: isolated opt-in **development-only** selection. Open the existing Vite editor at `http://localhost:5173/?hgptNativeSkeletonPreview=1` (use your actual Vite port if different). The normal app and exported release still select the existing Three-backed viewer by default. The opt-in preview shows **posed skeletal line segments only**, with diagnostic data attributes `hgptNativeRenderer`, `hgptNativeBoneCount`, `hgptNativeFrame`, and `hgptNativePreview`. It deliberately has **no character surface, muscles, proper lighting, weights, bone picking, orbit UI, background floor or mesh deformation**.
- `tests/firstPartyWebGL2SkeletonPreview.test.mjs`: no-dependency adversarial numeric and fake-GL lifecycle tests. Includes perspective near/far mapping, camera matrix, left/right mirroring, real posed endpoints, invalid/degenerate bone rejection, context-loss/restoration and unavailable WebGL2. Run with `node --test tests/firstPartyWebGL2SkeletonPreview.test.mjs` on modern Node.
- `.github/workflows/first_party_native_webgl2_skeleton_preview.yml`: verifies pure Node tests **without npm install**, proof of no vendor imports, and the existing TypeScript typecheck/production editor build with its current dev toolchain. No permanent npm dependencies are introduced.

**Critical distinction:** the project has **NOT yet removed Three.js from package.json**, since the character mesh and lighting renderer still use its gateway. This branch replaces a **bounded, working GPU slice** first and keeps vendor and first-party renderer side-by-side. It is an **actual first-party rendering implementation**, not a claim of zero dependencies across the entire studio. The spine, anatomical mesh, Blender files and application shell are not moved or modified. All live production defaults remain unchanged.

## Hard pass gates before turning off the vendor gateway

1. Verify rendered skeleton in a real WebGL2 browser, not only the fake-GL unit runner. At least front, side, rear, both-arm exercise and bilateral posture regression; compare posed FK endpoints to the validated solver. Shader functioning alone does not validate anatomy.
2. Introduce project-owned **scene entities/camera/interaction parity**: orbit, pointer ray picking, gizmos, equipment, timeline, editing and overlays; preserve disposal/performance.
3. Implement first-party **mesh rendering and smooth skeletal skinning** for ORIGINAL-v1: indexed triangles, per-vertex skin indices and normalized weights, matrix-palette transforms, normals, material and lighting, transparent/opaque order and GLB/glTF parsing where permitted. Test broad exercise families and shoulder/chest/armpit deformation against independent real-life references. A joint-wireframe renderer is not a substitute for this.
4. Implement robust WebGL context loss and restore, device pixel ratio/resize, browser/device/low-power fallback, verified vertex/matrix parity, and on-device performance acceptance. No use of code secretly copied from Three's source.
5. Only after those gates pass, move the default studio viewport to our renderer and remove the single surviving `src/core/threeRuntimeBoundary.ts` dependency, `three` package entry, vendor types and generated bundles; make source and package guard ceiling **zero**. The entire built product must pass the existing repo-first-party release allowlist, offline/network, strict migration and browser acceptance checks.
6. Preserve the 304 temporary videos until actual first-party animation replacements are approved in **PT-App**. Clean historical media from redistributed source history at final release. Other development services (GitHub, Blender, Node, Vite) are separate from shipped app runtime, but no copied third-party creative assets may cross the boundary.

## Verified status summary

**Initial stage only:** native GPU 3D line renderer and real first-party FK-pose feed exists on an isolated draft branch. It does NOT mean Three.js was deleted from the entire animation software, cannot create a finished realistic model, and carries no CP1/anatomical acceptance. The user-facing PT-App already has no npm dependency and is untouched. Anatomical project readiness remains **0 READY / 9 PARTIAL / 3 BLOCKED** until Work/Claude source measurements and Blender evidence close actual blockers.

**Parallel work coordination:** Do not modify Work's active `codex/source-skeleton-blender-measurements-20261010` head or Claude's anatomical candidate branches, and do not merge legacy V-series. The renderer spike is safe to test independently of their original-model progress. The ultimate goal is a genuinely original body, first-party runtime software, independent science and full exercise movement.

## Independent zero-Three exercise runtime entry (second demonstrator)

To distinguish **actual first-party runtime isolation** from merely bypassing the Three viewer at draw time, this branch also contains a second, independent development-only HTML entry:

- `native-webgl2-preview.html`
- `src/viewer/nativeWebGL2StandaloneEntry.ts`

Navigate with the existing development server to `http://localhost:5173/native-webgl2-preview.html` (or whichever local port serves Vite). This entry does **not import the editor app, Three scene/renderer gateway, React or R3F**. Its imports are the project's own humanoid rig, `PoseEvaluation`, exercise definition library, first-party exercise generation, FK/IK/constraint-aware `resolveFrame`, and the independent native GPU line shader. It animates a real authored exercise continuously with browser `requestAnimationFrame` and `ResizeObserver`. This path is a *real end-to-end first-party dependency-free rendering slice* for the skeleton only; it deliberately **cannot render the finished original skin mesh or substitute for the editor**.

Real Chromium CI explicitly opens this isolated page and verifies nonzero bone count, dynamic pose/frame updates, a nonblank canvas size, absence of browser exceptions, and **zero browser module fetches matching Three/React-related vendor paths**. It separately checks the default full editor has not lost its existing rendering. An evidence screenshot is diagnostic **only**, not a claimed human-body model or clinical correctness.

**Why this distinction matters:** the opt-in native preview embedded in the standard editor may *load* the old renderer modules transitively because the editor also imports its default Three-based controller. The independent HTML entry is the demonstration which isolates the new complete source-module graph instead of simply avoiding the old renderer's draw calls. Both paths remain development-only, and no current final PT-App runtime adds a dependency.
