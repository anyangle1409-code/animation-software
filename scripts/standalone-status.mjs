#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const pkg=JSON.parse(fs.readFileSync(path.join(ROOT,"package.json"),"utf8"));
const deps=Object.keys(pkg.dependencies||{}).sort();

const exists=(p)=>fs.existsSync(path.join(ROOT,p));
const prepared={
  firstPartyStore:exists("src/core/store.ts"),
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
  originalV1Scaffold:
    exists("scripts/init_original_v1_blender.py") &&
    exists("scripts/generate_original_v1_clean_scaffold.py") &&
    exists("scripts/audit_original_v1_blender.py"),
};

let next;
if(deps.includes("zustand")){
  next="Verify the prepared first-party store, then remove direct Zustand.";
}else if(deps.includes("@react-three/drei")){
  next="Integrate the prepared Grid, Orbit and Transform gizmo adapters incrementally; remove Drei only after zero imports and visual/touch parity.";
}else if(deps.includes("@react-three/fiber")){
  next="Integrate StudioSceneHost/frame-loop adapters and remove React Three Fiber.";
}else if(deps.includes("react") || deps.includes("react-dom")){
  next="Migrate the editor/viewer UI to project-owned DOM bindings and remove React/ReactDOM.";
}else if(deps.includes("three")){
  next="Finish first-party rig/GLB/renderer integration and remove Three.js.";
}else{
  next="Runtime dependency count is zero. Run final provenance, production-output, allowlist and offline acceptance gates.";
}

const result={
  authority:{
    startHere:"docs/CURRENT_HANDOFF.md",
    projectAuthority:"docs/PROJECT_AUTHORITY.md",
    operatingContract:"docs/AI_OPERATING_CONTRACT.md",
    decisionLog:"docs/DECISION_LOG.md",
  },
  branchTarget:"work/standalone-first-party-audit-20260927",
  sourceIntegrationTarget:"chatgpt/absolute-retarget-imports @ 47187360b5d631d438a6b33b284ad06732e244cb",
  directRuntimeDependencies:deps,
  directRuntimeDependencyCount:deps.length,
  completed:{
    directZustandRemoved:!deps.includes("zustand"),
  },
  prepared,
  next,
  commands:{
    verify:"VERIFY_STANDALONE_PREP.bat",
    audit:"npm run audit:standalone",
    originalV1:"PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat",
    finalRelease:"npm run audit:release",
    branchCleanup:"CLEANUP_CONTAINED_BRANCHES.bat --apply",
  },
  reminder:"Prepared does not mean integrated. Follow docs/CURRENT_HANDOFF.md and do not remove a dependency until its live imports are zero and the full suite/build/behaviour gates pass."
};

console.log(JSON.stringify(result,null,2));
