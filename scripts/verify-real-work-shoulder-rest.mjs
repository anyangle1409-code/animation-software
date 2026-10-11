#!/usr/bin/env node
/**
 * G4j: actual Work W1 #68 GLB full original 18-mesh/SHA/rig-rest preflight.
 * Native Work Z-up/row-major motion is NOT used or converted here.
 * Reuses G4g all-file artifact checks and G4i strict original source parser.
 *
 * Usage: node scripts/verify-real-work-shoulder-rest.mjs <W1-extracted-artifact-directory> [report.json]
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {parseRestrictedBatchedSkinnedGlb}
  from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
import {deriveOriginalSourceGLTFRestWorld}
  from '../src/viewer/firstPartyOriginalGltfRestWorld.mjs';
import {digestOriginalGlbSha256,
  HGPT_PROTOTYPE_HANDOFF_KIND,
  validateProvisionalModelHandoff}
  from '../src/viewer/firstPartyPrototypeModelHandoff.mjs';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const WORK_GLB='PROVISIONAL_FUNCTIONAL_SHOULDER_v1.glb';
const EXPECTED_SHA='fda9c5e653044988fd1e5c58fe352f074071c4be008eceba702bbbef96a4ea5f';
const dir=process.argv[2];
if(!dir)throw new Error('Usage: node scripts/verify-real-work-shoulder-rest.mjs <W1-artifact-dir> [report.json]');
const root=path.resolve(dir),work=JSON.parse(
  fs.readFileSync(path.join(root,'pilot_manifest.json'),'utf8'));
const buf=fs.readFileSync(path.join(root,WORK_GLB)),immutable=Buffer.from(buf);
assert.equal(sha(buf),EXPECTED_SHA,'do not bind an unverified/newer original model by stale SHA');
assert.equal(work.files_sha256[WORK_GLB],EXPECTED_SHA,
  'Work source manifest GLB digest must match real model bytes');
assert.equal(work.status,'PROVISIONAL_SHOULDER_ONLY_NOT_ORIGINAL_HUMAN');
assert.equal(work.anatomy_approved,false);
assert.equal(work.motion_approved,false);
assert.equal(work.production_approved,false);
const bytes=buf.buffer.slice(buf.byteOffset,buf.byteOffset+buf.byteLength);
const scene=parseRestrictedBatchedSkinnedGlb(bytes,{
  allowProvisionalPilot:true,allowSourceFlatColors:true,
  allowSourceUV0:true,allowSourceNormals:true,
});
assert.equal(scene.batches.length,18);
const rest=deriveOriginalSourceGLTFRestWorld(bytes,scene);
assert.equal(rest.sourceJointCount,6);
assert.deepEqual([...rest.orderedSourceJointNames].sort(),
  Object.keys(work.rig_mapping).sort(),
  'Work declares all the same exact source bone identities');
const sourceToRuntimeBone=Object.fromEntries(
  rest.orderedSourceJointNames.map(name=>[name,name]));
const rigRestWorld=Object.fromEntries(
  rest.orderedSourceJointNames.map(name=>[
    name,rest.sourceWorldRestByName[name]
  ]));
const manifest={
  kind:HGPT_PROTOTYPE_HANDOFF_KIND,
  candidateId:'PROVISIONAL_FUNCTIONAL_SHOULDER_v1',
  status:'PROTOTYPE_ONLY',
  glb:{sha256:EXPECTED_SHA,layout:'pilot',sourceFeatures:{
    flatColors:true,uv0:true,normals:true
  }},
  frame:{unit:'metre',up:'Y',handedness:'right',
    basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
  rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
    thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
  rig:{sourceToRuntimeBone,
    runtimeBoneNames:[...rest.orderedSourceJointNames],
    restWorldByRuntimeBone:rigRestWorld,
    lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED'},
  releaseApproved:false,
};
const verified=await validateProvisionalModelHandoff(bytes,manifest);
assert.equal(verified.numberOfPrimitives,18);
assert.equal(verified.scene.audit.numberOfMeshes,18);
assert.equal(verified.audit.allGLBPrimitivesDecodedAndBound,true);
assert.equal(verified.audit.explicitRestWorldInverseBindNumericalParity,true);
assert.ok(verified.audit.maximumRestMatrixResidual<=1e-4);
assert.ok(rest.maximumWorldInverseBindResidual<=1e-4);
assert.deepEqual(verified.sourceJointNames,[...rest.orderedSourceJointNames]);
assert.equal(verified.audit.medicallyApprovedHumanSkeleton,false);
assert.equal(verified.audit.modelProductionReady,false);
assert.deepEqual(buf,immutable,'never rewrite original Work bytes');
const result={
  kind:'hgpt-g4j-actual-work-original-glb-world-rest-and-rig-screen-v1',
  modelFile:WORK_GLB,originalSha256:EXPECTED_SHA,
  sourceAuthor:'WORK_PROVISIONAL_SHOULDER_ONLY',
  originalMeshCount:verified.scene.audit.numberOfMeshes,
  originalPrimitiveCount:verified.numberOfPrimitives,
  sourceJointCount:rest.sourceJointCount,
  orderedSourceJointNames:[...rest.orderedSourceJointNames],
  maxWorldRestTimesInverseBindResidual:rest.maximumWorldInverseBindResidual,
  maxG4RigRestResidual:verified.audit.maximumRestMatrixResidual,
  gltfFrame:rest.frame,
  sourceBytesUnmodified:true,actualOriginalGLBPassedG4SHAAndRig:true,
  sourceWorkNativePoseFramesRegistered:false,
  physicalBoneJointCentresIndependentlyVerified:false,
  sourceRightsForReleaseApproved:false,
  originalFullBodyHumanReady:false,
  originalWholeBodyDynamicsValidated:false,
  originalHumanModelReleaseApproved:false,
};
const out=path.resolve(process.argv[3]||
  'reports/work-pilot/actual-work-g4j-glb-world-rest.json');
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
