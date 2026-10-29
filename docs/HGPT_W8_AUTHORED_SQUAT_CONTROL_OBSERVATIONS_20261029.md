# W8 authored squat-control observations — 2026-10-29

## Scope

This is a read-only observation of the immutable W8 reconstruction (`2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`) under the frozen r57 benchmark code (`025d5f28fa7eba2064fba565b1c9b60119cdd2cb`). The probe opens the source with script auto-execution disabled, runs the existing nine authored squat samples in memory, records controls after the same runtime driver call used by the preserved diagnostic, and never saves a `.blend`.

The values below are authored-control observations. They are **not** ISB joint-coordinate angles, independently verified anatomical joint centres, pressure/force measurements, balance evidence, clinical limits or movement approval.

## Verified cloud execution

- Implementation commit: `30a2eaa5c0d661adb6ea5367aec91fcdcd23a09f`.
- GitHub Actions run [40857162884](https://github.com/anyangle1409-code/animation-software/actions/runs/40857162884): **SUCCESS 7/7**.
- Pose job `123390906355` executed all nine native samples. Its new focused suite passed 11/11; the localization job passed the complete 330/330 suite.
- Squat artifact `12890610821` independently downloaded, ZIP CRC clean, and SHA256 matched GitHub: `4a90f5bfb042140fc2136d9d1a91f455aa1f076c05ffb8679db2e225a54f3043`.
- Embedded JSON SHA256: `79331c557fe8ced962f154ed5dab7dba1693b50404fdec5da62af6f418a68f05`.
- Embedded Markdown SHA256: `c10cc5eb8019c23f142522a45be85f8a026164b5ff0d37f756dbbcee6bba4383`.

## Native observations

The authored targets use the frozen smoothstep path from rest to 25° pelvis forward tilt, 10° spine extension, 110° hip flexion and 110° knee flexion. Those targets describe the project path, not measured anatomical angles. The measured authored ankle value and foot-head world trajectories are:

| Sample | Authored ankle DF° (not ISB) | l foot-head X mm | r foot-head X mm | foot-head separation mm | lowest evaluated body Z mm (not contact) |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.000002 | -91.999993 | 91.999993 | 183.999985 | -1.423313 |
| 1 | 1.076256 | -90.573147 | 90.573147 | 181.146294 | -1.309167 |
| 2 | 3.913890 | -86.879946 | 86.879946 | 173.759893 | -0.970709 |
| 3 | 7.924802 | -82.101278 | 82.101278 | 164.202556 | -0.609452 |
| 4 | 12.518321 | -77.777497 | 77.777497 | 155.554995 | -0.609488 |
| 5 | 17.104715 | -75.190105 | 75.190105 | 150.380209 | -0.609461 |
| 6 | 21.099769 | -74.605525 | 74.605525 | 149.211049 | -0.609467 |
| 7 | 23.923236 | -75.173870 | 75.173877 | 150.347747 | -0.609518 |
| 8 | 24.993933 | -75.598121 | 75.598128 | 151.196249 | -0.609549 |

- Bilateral thigh, shin, foot and toe unsigned local-delta magnitudes match exactly at the artifact's serialized precision for all nine samples. This is authored symmetry, not anatomical side certification.
- Terminal unsigned local magnitudes are thigh `109.999992°`, shin `109.999992°`, foot `25.167521°`, toe `0°`; the measured authored ankle value is `24.993933°`. Matrix-basis magnitudes are not signed joint-coordinate components.
- Fore–aft and vertical foot-head positions stay within `0.000071 mm` of sample 0, but each foot head moves inward by as much as `17.394468 mm` at sample 6. Their separation narrows by `34.788936 mm` at sample 6 and remains `32.803737 mm` narrower at sample 8.
- The frozen benchmark's root translation therefore preserves the observed sagittal/vertical ankle-head placement to numerical precision but does **not** preserve mediolateral foot-head placement. A literal claim that both ankle heads remain at their complete rest positions is not supported by the runtime evidence.
- The evaluated body's lowest world Z rises by `0.813764 mm` from sample 0 to sample 8. This is a lower-envelope observation only; it does not establish floor location, pressure, force, slip or verified ground contact.
- The single `foot` plus `toe` control chain cannot establish talus/calcaneus or hindfoot/midfoot/forefoot coordination. No corresponding separately named controls were present in the prior three-model rest inventory.

## Ruling and next test

Status remains `READ_ONLY_AUTHORED_SQUAT_CONTROL_STATE_ANATOMY_NOT_APPROVED`. The newly measured mediolateral foot-head drift is a reusable full-body coordination defect to investigate before claiming planted feet, balance or ground contact. It does not authorize a rig, weight, shape-key or source-model edit.

The foot-plant decomposition requested here has now been completed and is recorded below. No corrective deformation is authorized.

No original `.blend`, mesh, skeleton, weights, driver, shape key, permanent muscle ID, attachment, highlighting, PT-App, production asset, PT_MODEL_VERSION 1.0, Claude-owned branch, merge or deployment changed. Muscle attachment/highlighting remain deferred; 46 landmarks remain unbound and 0/19 generic motions approved.


## Foot-plant solve decomposition — corrected native verification

The follow-up probe wraps the unchanged frozen \`_plant_feet\` call and observes evaluated control state immediately before and after it. Implementation commit \`aac74b36d40098756c4c2a82aef496fc436b572d\` added the decomposition. Run [40858906795](https://github.com/anyangle1409-code/animation-software/actions/runs/40858906795) completed SUCCESS 7/7, but independent artifact review found that its pre-solve observation preceded Blender's dependency-graph update and therefore contained stale rest-state heads. That run remains a successful CI execution, but its pre-solve evidence is superseded and must not be used.

Corrective commit \`b268375790150a30745de9c88a3d4c92728e7691\` requires an evaluated dependency-graph update before both observations. Replacement run [40919982094](https://github.com/anyangle1409-code/animation-software/actions/runs/40919982094) completed **SUCCESS 7/7**. Job IDs: localization \`123610262859\`, pose \`123610263090\`, V14 \`123610263160\`, R120 \`123610263190\`, W8 \`123610263334\`, comparison \`123610905509\`, driver \`123613572401\`. Cloud logs confirm 333/333 localization tests and pose suites 29/29 + 14/14 + 19/19 + 6/6 + 10/10.

Corrected squat artifact \`12917508191\` was independently downloaded, CRC-checked and SHA256-matched GitHub: \`718eee9b5ea8b5fedc76e091a5f58cd59389ba44a7b9ca14467d9262c402de2f\`. Embedded JSON SHA256 is \`998c3db075317a4549d7130c965bf38e08d3ad147fe3669214465d5303c47b69\`; Markdown SHA256 is \`e97810311ff7b4b9e6b9e5e843889e2b0d0b3d7e36e4dedd6d04eb1fa1da83bd\`.

At sample 6, immediately before the solve, authored foot-head residuals from captured rest targets are:

- suffix \`l\`: \`(+17.394640, -229.035827, +292.100161) mm\` in world X/Y/Z;
- suffix \`r\`: \`(-17.394312, -229.035840, +292.100161) mm\`.

After the unchanged solve they are:

- suffix \`l\`: \`(+17.394468, +0.000001, +0.000052) mm\`;
- suffix \`r\`: \`(-17.394468, +0.000024, +0.000030) mm\`.

Across all nine samples, the magnitude of the mean bilateral post-solve residual is at most \`0.000058 mm\`. The shared fore-aft and vertical residual is therefore removed to numerical precision, while the equal-and-opposite mediolateral residual cancels in the bilateral average and remains on each side. This directly localizes the inward foot-head drift to a limitation of using one averaged root correction for two opposing lateral residuals. It does not prove an anatomical ankle error, because the authored foot heads are still not independently verified joint centres.

The recorded root matrix-basis translation is expressed in the root control's local basis and must not be compared component-for-component with world-space foot residuals. No contact, balance, pressure, force, friction or movement approval follows from the near-zero bilateral mean.

Next safe work is to measure the evaluated foot/toe-dominant skin support envelope at the same nine in-memory samples and compare it with these control residuals. This should remain descriptive and must not invent a contact or balance threshold.
