# First-party indexed 3D mesh and deforming skin — Phase 2 renderer migration

**October 10, 2026 · ISOLATED DRAFT · NOT THE ORIGINAL CHARACTER · NOT YET ANATOMICAL/RELEASE-READY**

This develops the first-party WebGL2 engine toward removal of Three.js without disrupting Work's private CT/Blender anatomical skeleton or the existing production editor.

## Actual implemented software

- `src/viewer/firstPartyIndexedSkinnedMesh.mjs`: independently written indexed triangle rendering with direct WebGL2 `drawElements`, element buffer, normals buffer, configurable camera and first-party GLSL material lighting, original context-loss recovery and disposal. No `three`, `react`, glTF loaders, external renderer or runtime import.
- Source-owned reference **four-influence linear-blend skinning** on CPU: validates immutable-indexed mesh arrays, original inverse-rest-bind matrices, finite rigid 4×4 joint transforms and normalized weights, then computes per-vertex `skinPose = SUM[w_i (worldPoseJoint_i × inverseBindJoint_i × restVertex)]`. The implementation recomputes indexed vertex normals from deformed triangle faces each frame. It rejects invalid triangles, nonfinite GPU data, out-of-range joint indices, invalid weights, inappropriate affine inputs and geometry that collapses to zero-area triangles.
- Rigid rest inverse accepts orthonormal (no-scale) matrices. This stage deliberately does **not** implement muscle physics, normal/shear correction for arbitrary non-rigid transforms, actual cartilage/soft-tissue motion, corrective shape keys, production GLB body topology or GPU skeletal vertex-palette skinning. CPU skinning is a mathematically testable baseline before the production optimized path.
- A deliberately *original procedural two-bone arm sleeve* `makeTwoBoneSkinProbe`, with indexed closed triangulated tube, continuous ring topology and smoothly blended transition weights near the elbow. It is not derived from a purchased/imported/CT/legacy model.
- `src/viewer/nativeWebGL2SkinningStandaloneEntry.ts` and `native-webgl2-skinning-preview.html`: a separate dev-only browser entry, running the original exercise library, first-party clip generator and the existing original rig pose evaluator/IK/constraints. It computes the upperarm_l/forearm_l inverse rest bindings directly from the rig (skeleton remains authority) and displays live deformed indexed triangles in the native GPU pipeline for `dumbbell_bicep_curl`.
- `tests/firstPartyIndexedSkinnedMesh.test.mjs`: zero-dependency Node tests covering rigid transforms, inverse bind cancellation, two-bone 4-influence blending, posed normals, winding, invalid matrix/skin/weights, indexing, UInt32 large-mesh support, simulated WebGL context loss/restoration, compilation failure and original geometric proxy validity.
- `.github/workflows/first_party_indexed_skinning_gpu.yml`: runs both original direct WebGL and new skinning tests **without npm install**, full existing editor TypeScript and build parity, and actual Chromium GPU rendering of the new independent synthetic deforming triangle mesh. Browser harness explicitly checks the new page never requests Three, R3F or React vendor modules, has changing exercise poses, and actually draws indexed triangles.
- The **existing production studio and character viewer remain unchanged**, still using Three.js behind one gateway; the PT-App remains zero-third-party npm runtime dependencies. This side branch does **not** modify package.json or any lockfile. Removal is postponed until native mesh rendering reaches full-body surface/skin/lighting/picking/animation parity.

## Honest verification boundaries

A working two-bone **procedural cylinder** does not make the realistic human model first-party or production-ready. Even an actual shader/browser pass does not validate anatomical positions, muscle deformation or overhead shoulder/axilla relief.

Needed next before retiring Three: original-v1 full-body mesh/topology/provenance approval, canonical skeleton and weights, multiple simultaneous bones/normal material handling, efficient GPU matrix-palette skinning, glTF/GLB parsing independent of external packages, camera/orbit/selection/equipment, blendshape/correctives, device/resize regression, and broad exercise photo/video comparison. Must preserve independent spine, ribs, wrist and foot anatomy readiness gates. No source data may be silently promoted to final mesh.

**Anatomical readiness unchanged: 0 READY / 9 PARTIAL / 3 BLOCKED.** No c005 or production character released.


## Real independent GitHub Actions evidence (actual code, actual Chromium WebGL2)

Verified initial implementation at [Actions run 38088995260](https://github.com/anyangle1409-code/animation-software/actions/runs/38088995260): **all three CI jobs passed**:

- **16/16 new adversarial indexed mesh + four-weight CPU skinning tests passed**, plus **12/12 independently verified skeleton WebGL2 tests**. Both suites require **zero npm packages**; all runtime shader, math, original FK and CPU skinning modules have no `three`, `react` or R3F import.
- Entire animation editor strict TypeScript validation and production build passed unchanged, retaining original Three-backed full character/editor as safety baseline.
- Real headless Chromium WebGL2 compiled vertex/fragment shaders and **rendered 164 indexed TRIANGLES** from the first-party procedurally created two-bone sleeve during actual generated `dumbbell_bicep_curl`. CI observed **8 rendered frames**, pose-space vertex motion max **0.005408 metres** during sampling, 1256×699 canvas, **zero browser exceptions, zero GPU console errors, zero vendor module network requests**. The diagnostic screenshot and JSON report are saved in [artifact 11683871637](https://github.com/anyangle1409-code/animation-software/actions/runs/38088995260/artifacts/11683871637).
- Further hardening requires **orthonormal, right-handed, shear-free rest bind matrices**, including adversarial reflected/sheared test cases; latest commit reruns the same actual-browser jobs.
- A moving simple deformable sleeve is convincing proof the code computes moving vertex positions and invokes GPU triangle rasterization. It is **NOT** proof realistic flesh/muscle geometry, correct anatomy, GPU-performance readiness or final native glTF/GLB compatibility.

This source is separate from the temporary third-party exercise videos in PT-App, separate from Work's private CT/Blender branch, and separate from the original model. A future first-party skinned full-body mesh must match an anatomically accepted skeleton, never drag joint centres to fit this prototype.
