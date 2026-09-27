# First-party standalone roadmap

## Goal

Produce a distributable Home Gym PT product whose shipped runtime and shipped assets contain no third-party code, libraries, meshes, textures, rigs, animations or other third-party creative assets.

Development tools may remain external tools (for example Blender, Git, Python, Node, TypeScript compilers, GPT/Claude) provided their code/assets are not incorporated into the distributable product. This roadmap separates **shipped-product independence** from the optional later goal of **source/build-tool independence**.

This document is a project-engineering plan, not a legal opinion. Final commercial release should still receive an appropriate licence/provenance review.

## Two independence levels

### Level 1 — distributable independence (required)
The product shipped to end users contains only:
- project-authored runtime code;
- project-authored models, rigs, materials, textures and animation data;
- project-authored exercise/generation/validation data;
- open file-format data such as GLB/JSON without bundling third-party implementation code.

No React, Three.js, React Three Fiber/Drei, Zustand or other third-party runtime implementation may remain in the production bundle.

### Level 2 — source/build independence (optional later)
The repository can also be built/tested without third-party developer packages. This would require replacing build/test/compiler tooling such as Vite, Vitest, Playwright and TypeScript itself. This is not necessary merely to keep third-party code out of a shipped runtime, and should be deferred until Level 1 is complete unless there is a specific distribution requirement.

## Current known runtime dependencies

Direct dependencies in package.json at source HEAD 47187360b5d631d438a6b33b284ad06732e244cb:
- @react-three/drei
- @react-three/fiber
- react
- react-dom
- three
- zustand

Current dev dependencies:
- @types/node
- @types/react
- @types/react-dom
- @types/three
- @vitejs/plugin-react
- playwright
- typescript
- vite
- vitest

The package lock also contains transitive MIT / Apache-2.0 / BSD-3-Clause / ISC dependencies and one CC-BY-4.0 development data package (caniuse-lite). These are acceptable as historical/dev dependencies but must not be confused with a first-party distributable.

## Current asset provenance risk

The current production/high-detail male line is derived from an imported source character. Project documents explicitly state that the production path preserved imported source mesh/skeleton/bind/weight/proportion data before later project modifications.

Therefore:
- V5/V6/V7/V8/V13e/V15f and descendants remain **legacy/reference lineage** for first-party-ownership purposes.
- They may be used as engineering/visual validation references where lawful.
- They must not be treated as the final clean-room distributable character merely because many vertices, weights or regions have been modified.
- No geometry, topology, UVs, weights, source skeleton positions, textures or materials may be copied from that imported lineage into the first-party character.

## Immediate roadmap change

### Phase 0 — finish V15f as a reference benchmark
Complete the already-near-finished V15f whole-hand audit and final matched visual review.

Reason:
- the work is almost complete;
- it captures valuable anatomical/quality targets;
- it gives a strong regression benchmark for the replacement model.

Do not spend additional long-lived production effort on grip/shoulder/appearance changes to the legacy character after this reference benchmark unless explicitly needed to derive a non-copying specification.

### Phase 1 — freeze the legacy character lineage
Create a machine-readable and human-readable record marking:
- imported/legacy source lineage;
- last accepted/reference checkpoints;
- what may be measured;
- what must never be copied into the clean-room asset.

No legacy GLB/Blend becomes the new distributable character.

### Phase 2 — create Home Gym PT Male ORIGINAL v1 from a blank mesh
Start from a genuinely blank/new mesh and the project's own anatomical specification.

Allowed inputs:
- human anatomical measurements/ranges expressed numerically;
- project-authored canonical bone hierarchy and joint semantics;
- generic anatomical knowledge;
- project-authored contact/clearance/deformation requirements;
- measured acceptance criteria extracted from the legacy model (for example total height, hand span target, joint ranges, contact locations expressed as abstract requirements).

Not allowed:
- copying vertices/faces/topology from a legacy GLB/Blend;
- shrink-wrapping or retopologising directly over the legacy mesh as the source of shape;
- transferring skin weights;
- transferring UVs;
- transferring textures/materials;
- transferring source-rig bone transforms/proportions when those came from the imported source;
- using nearest-surface/nearest-vertex projection from legacy geometry to generate the new surface.

The clean-room asset must have its own:
- body topology;
- hands/fingers;
- face/head;
- feet/toes as needed;
- garment topology;
- UV layout if textures are used;
- materials;
- skin weights;
- bind pose.

### Phase 3 — validate ORIGINAL v1 before further polish
Run the existing project validation concepts against the clean model:
- canonical-rig compatibility;
- joint-range stress;
- floor/hand/foot contact;
- push-up;
- curl;
- press;
- pull-up;
- squat/lunge;
- collision/clearance;
- bare/dressed equivalence;
- deformation/fold checks;
- whole-body movement-envelope tests.

Do not tune exercise mechanics merely to hide defects in the clean mesh.

### Phase 4 — continue character finishing on the clean model
Only after the clean model becomes the accepted model:
1. grip fitting;
2. skin/material appearance;
3. shoulder/chest/back/armpit topology;
4. final shoulder/scapula weighting;
5. palm/thumb/scapular motion activation;
6. whole-body motion stress test;
7. final character acceptance.

This prevents duplicated work on a character that cannot be the final first-party asset.

## Runtime replacement order

The replacement order should minimise simultaneous risk.

### R1 — remove Zustand
Replace the small state-management dependency with a project-authored typed store/event system.
- Preserve undo/redo and editor behaviour.
- Add behavioural tests first.
- Remove Zustand only after parity.

### R2 — remove Drei helpers
Replace OrbitControls/helpers/loaders/utilities used from @react-three/drei with project-authored equivalents or direct lower-level internal code.
- Inventory exact imports before implementation.
- No visual or camera-behaviour change accepted without explicit evidence.

### R3 — remove React Three Fiber
Replace @react-three/fiber with a project-authored render loop/scene bridge.
- Keep existing scene semantics during transition.
- Do not remove Three.js in the same step.

### R4 — remove React / ReactDOM
Move UI/editor panels to project-authored DOM/component/event code.
- Preserve accessibility, keyboard controls, timeline state and mobile inspection behaviour.
- Remove React only when no runtime import remains.

### R5 — remove Three.js
This is the largest software task and should be last.
Replace, in controlled slices:
- vectors/quaternions/matrices;
- bone hierarchy and skinning transforms;
- animation sampling;
- camera/projection;
- geometry buffers/material handling;
- WebGL/WebGPU renderer;
- picking/controls;
- GLB parsing/writing if currently using Three.js GLTF infrastructure.

The existing deterministic exercise engine and validation data should remain independent of renderer implementation wherever possible.

After parity, delete Three.js and all transitively runtime-required packages.

## Distribution gates

A release may be labelled first-party standalone only when all are true:

### Code
- production package/bundle contains no third-party runtime implementation;
- source scan finds no runtime imports from removed libraries;
- generated production JS contains no bundled third-party licence banners/code;
- dependency audit classifies remaining packages as development-only, or zero packages for Level 2.

### Assets
- final character provenance starts at a blank/original asset;
- no legacy source geometry/weights/UV/material fingerprint matches beyond coincidental numerical values;
- all equipment models are confirmed project-authored;
- all textures/fonts/audio/icons shipped are project-authored or replaced;
- all animations are project-generated/project-authored.

### Documentation
- ASSET_PROVENANCE.md records every shipped asset's origin;
- FIRST_PARTY_COMPONENT_MANIFEST.json records each shipped component and authoring source;
- THIRD_PARTY_REFERENCE_ONLY.md lists tools/reference materials that are not shipped.

## Parallelisation

The clean-model track and runtime-replacement track can run in parallel because they touch different concerns.

Recommended use of scarce Blender/Work time:
- Blender/Work: clean-room mesh creation, weighting, direct 3D inspection.
- normal source Work: dependency replacement and parity tests.
- ordinary chat/GitHub preparation: inventories, manifests, scripts, handoffs, acceptance criteria.

## Current decision

Do not throw away the V15f work. Finish its final audit as a **reference benchmark**, then pivot the character-production line to the clean-room ORIGINAL model before doing expensive final grip/shoulder/appearance work.
