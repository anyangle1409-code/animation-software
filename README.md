# Home Gym PT Animation Studio

Home Gym PT is a deterministic 3D exercise-animation authoring system built around structured exercise definitions, a canonical humanoid rig, IK/contact constraints, equipment attachments, technique validation, and reusable animation export.

## Current project authority

The project is in a first-party standalone transition. Do **not** infer current state from historical branches or old handoffs.

Start here:

1. [Current handoff](docs/CURRENT_HANDOFF.md)
2. [Project authority](docs/PROJECT_AUTHORITY.md)
3. [AI operating contract](docs/AI_OPERATING_CONTRACT.md)
4. [Frozen decision log](docs/DECISION_LOG.md)

On a laptop, begin every work session with:

```bat
STANDALONE_STATUS.bat
```

## Standalone target

The required distributable must contain:

- zero prohibited third-party runtime implementation;
- zero legacy/third-party-derived production character content;
- zero remote runtime resource dependency;
- only approved first-party production assets.

External development tools such as Blender, Git, Python, Node, TypeScript tooling, GPT, and Claude may be used during development.

## Current transition state

Direct Zustand has already been replaced by the project-owned store. Five direct runtime dependencies remain during controlled migration:

- `@react-three/drei`
- `@react-three/fiber`
- `react`
- `react-dom`
- `three`

Drei has zero current source imports but is intentionally retained until the physical Grid/Orbit/Transform parity gate passes. R3F, React/ReactDOM, and Three are removed only after their project-owned replacements reach the live production path with parity evidence.

The legacy/imported character line and MakeHuman-derived built-in body are not eligible for the final standalone character. The clean-room production line is **ORIGINAL v1**, targeting the independent **63-bone `hgpt_canonical_v4_original`** rig.

## Engine capabilities

The repository currently contains 28 exercise definitions spanning curls, presses, rows, squats/lunges, calf work, hinges, carries, trunk flexion/rotation, anti-rotation, vertical pulling, and related variants.

Core capabilities include:

- deterministic pose/clip generation;
- 63-bone runtime rig architecture and first-party v4 candidate;
- forward and inverse kinematics;
- contact locks and equipment sockets;
- anatomical joint limits;
- exercise-family generation;
- technique validation;
- timeline/editor tooling;
- muscle diagnostics;
- retargeting and GLB/JSON export;
- first-party store, math, frame-loop, GLB, camera/orbit/grid/gizmo foundations;
- clean-room Blender generation/audit tooling;
- deny-by-default release/provenance/network guards.

## Commands

```bash
npm install
npm run dev
npm run typecheck
npm test
npm run build
npm run audit:standalone
npm run audit:release
```

Windows status/verification entry points:

```bat
STANDALONE_STATUS.bat
VERIFY_STANDALONE_PREP.bat
PREPARE_ORIGINAL_V1_O2.bat
```

## Architecture

The animation core is data-driven:

```text
ExerciseDefinition
      |
      | generateClip
      v
StudioClip
      |
      | resolveFrame(time)
      v
ResolvedFrame
      |
      +--> pose / IK / contacts / equipment
      +--> viewer
      +--> technique checks
      +--> exporters
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the module-level design.

## Historical/reference material

Historical branches and legacy character assets are engineering evidence only. They are not current implementation instructions and must not be used as production source material unless the current handoff explicitly authorises a narrow reference use.
