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
