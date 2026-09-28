#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const pkg=JSON.parse(fs.readFileSync(path.join(ROOT,"package.json"),"utf8"));
const deps=Object.keys(pkg.dependencies||{}).sort();

const exists=(p)=>fs.existsSync(path.join(ROOT,p));
const prepared={
  firstPartyStore:exists("src/core/observableStore.ts") && exists("src/core/store.ts"),
  firstPartyMath:exists("src/core/linearMath.ts"),
  firstPartyGlb:
    exists("src/core/glbContainer.ts") &&
    exists("src/core/gltfAccessors.ts") &&
    exists("src/core/gltfBuilder.ts"),
  firstPartyFrameLoop:exists("src/core/frameLoop.ts"),
  firstPartySkeleton:exists("src/rig/firstPartySkeleton.ts"),
  firstPartyIkOrientation:exists("src/ik/firstPartyOrient.ts"),
  firstPartyPose:exists("src/rig/firstPartyPose.ts"),
  dreiFoundations:
    exists("src/viewer/firstPartyCameras.ts") &&
    exists("src/viewer/orbitModel.ts") &&
    exists("src/viewer/referenceGrid.ts") &&
    exists("src/viewer/transformGizmoMath.ts"),
  originalV1O2:
    exists("PREPARE_ORIGINAL_V1_O2.bat") &&
    exists("docs/ORIGINAL_V1_O2_WORK_HANDOFF.md"),
};

const characterPath={
  cleanProceduralFallback:exists("src/character/procedural.ts") && exists("src/body/profileMesh.ts"),
  derivedAnatomicalLineageAbsent:
    !exists("src/body/anatomical.ts") &&
    !exists("src/character/builtin.ts") &&
    !exists("scripts/generate-anatomical-body.mjs"),
  preservedRecoveryBranch:"archive/pre-makehuman-removal-20260928",
  preservedRecoverySha:"502adedc9fd5c7ddbee1b74cd0472879de6fb047",
};

const r3fSourceRemoved=
  !exists("src/viewer/R3FViewportHost.tsx") &&
  exists("src/viewer/FirstPartyViewportHost.tsx") &&
  exists("src/viewer/firstPartyViewportRuntime.ts");

const nextCloud=deps.includes("react") || deps.includes("react-dom")
  ? "Continue docs/REACT_FIRST_PARTY_MIGRATION_HANDOFF.md. R3F/Drei source imports are zero; migrate React scene composition/editor chrome to project-owned lifecycle/DOM bindings."
  : deps.includes("three")
    ? "Finish first-party rig/GLB/renderer integration and remove Three.js last."
    : "Runtime dependency count is zero. Run final provenance, production-output, allowlist and offline acceptance gates.";

const nextLaptop=deps.includes("@react-three/drei")
  ? "Complete the physical desktop/iPhone Grid/Orbit/Transform parity gate; remove Drei only after that gate passes. Blender track: run PREPARE_ORIGINAL_V1_O2.bat and continue ORIGINAL v1 O2."
  : "Run the exact laptop/Blender task in docs/CURRENT_HANDOFF.md.";

const result={
  authority:{
    startHere:"docs/CURRENT_HANDOFF.md",
    projectAuthority:"docs/PROJECT_AUTHORITY.md",
    operatingContract:"docs/AI_OPERATING_CONTRACT.md",
    decisionLog:"docs/DECISION_LOG.md",
  },
  branchTarget:"work/standalone-first-party-audit-20260927",
  historicalIntegrationBaselineCommit:"47187360b5d631d438a6b33b284ad06732e244cb",
  directRuntimeDependencies:deps,
  directRuntimeDependencyCount:deps.length,
  completed:{
    directZustandRemoved:!deps.includes("zustand"),
    legacyV8RuntimePathRemoved:true,
    derivedAnatomicalRuntimePathRemoved:characterPath.derivedAnatomicalLineageAbsent,
    r3fSourceRemoved,
  },
  prepared,
  characterPath,
  nextCloud,
  nextLaptop,
  commands:{
    verify:"VERIFY_STANDALONE_PREP.bat",
    audit:"npm run audit:standalone",
    originalV1:"PREPARE_ORIGINAL_V1_O2.bat",
    finalRelease:"npm run audit:release",
    branchCleanup:"CLEANUP_CONTAINED_BRANCHES.bat --apply",
  },
  reminder:"Follow docs/CURRENT_HANDOFF.md. Preserve behaviour and provenance; do not remove a dependency until its live imports and required parity gates are clear."
};

console.log(JSON.stringify(result,null,2));
