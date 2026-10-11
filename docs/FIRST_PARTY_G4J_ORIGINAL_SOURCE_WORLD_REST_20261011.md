# G4j — ACTUAL original Work glTF hierarchy WORLD REST binds: independent 6-joint screen

**11 October 2026, Chat Lane G.** This is source model provenance and mathematical rig-bind testing, not anatomical/clavicle-muscle approval.

## Why

The verified real Blender shoulder pilot GLB from Work W1 [PR #68](https://github.com/anyangle1409-code/animation-software/pull/68) contains six named joint controls `clavicle_left/scapula_left/humerus_left/clavicle_right/scapula_right/humerus_right`. Its nodes are **genuine nested glTF scene joints with TRS transforms**, not flat identity world transforms. Source inverse bind matrices are stored as glTF **column-major 4×4** binary accessor data. Passing a synthetic G4 rig with identity rest transforms is not legitimate verification of these original source bones. Neither should Chat assume Work's native Blender Z-up, row-major diagnostic pose matrices are already glTF Y-up world matrices.

## Implemented

`src/viewer/firstPartyOriginalGltfRestWorld.mjs` takes exact source GLB bytes plus the strictly existing verified G4i diagnostic source scene, reads the original source joint graph and derives **the actual glTF world rest matrix** for each joint by composing the original parent hierarchy. It uses first-party WebGL matrix multiplication and normalized quaternion-to-column-major rotation, with bounded proper rigid local/global matrix constraints. It refuses cyclic/double-parent graph, nonfinite matrices, nonunit quaternions, reflections, nontrivial scales and any joint order different from the already validated original source GLB skin order.

The output maps each true source joint name to its **unmodified glTF Y-up world rest 4×4 matrix**. It independently calculates `WorldRest × originalSourceInverseBind` for all six, requiring maximum component residual ≤0.0001. These rest matrices can then be used to build the existing G4 SHA-bound model manifest, without artificial joint centre relocation or guessed anatomical axes.

A new original **actual W1 asset** smoke test extracts the existing CI artifact #11706909894, verifies the exact SHA `fda9c5e653044988fd1e5c58fe352f074071c4be008eceba702bbbef96a4ea5f`, plus author-declared six joint names and unapproved source flags. It then passes the original 18 meshes through G4i pilot decoder, derives all six glTF world rest matrices and performs the **full** previously established G4 manifest/rest/inverseBind/source SHA validator. Only JSON metrics/report are uploaded; the original Blender, GLB and render bytes remain untouched and are not rehosted.

Unit tests check ordinary synthetic 18-mesh worldRest×IBM, changed joint rest, false quaternion, reflected frame and forged source scene. The actual original Work asset test is the decisive one; synthetic results alone are not sufficient to declare success. After exact-head Actions success, record the six source names and measured residuals as mathematical import correctness.

**Important unchanged boundaries:** no Work's seven native source poses have been converted from Z-up row-major to glTF Y-up column-major; source glTF rest is not anthropometric approval; no evidence of real shoulder biomechanics under load, correct scapular rhythm, muscle/skin deformation, exercise contact, full adult male anatomical mesh, reviewed original rights or production readiness. Work's newer [PR #72](https://github.com/anyangle1409-code/animation-software/pull/72) provisional scapular shape remains distinct.

## Next

After real asset 6-joint rest × inverseBind parity passes, build **actual original 18-mesh native GPU diagnostic rendering** with original source untextured colours, correct material sidedness and clear view/bounds; compare one neutral pose and authored source glTF motion frames **only if** source-grounded basis conversion is numerically verified. Continue to preserve original Work skeleton geometry and the PT App's media unchanged; no release promotion.
