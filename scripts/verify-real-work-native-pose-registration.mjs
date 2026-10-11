#!/usr/bin/env node
/** G4l REAL original Work #68 pose record Z-up → source GLB Y-up registration. */
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {parseRestrictedBatchedSkinnedGlb}
  from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
import {deriveOriginalSourceGLTFRestWorld}
  from '../src/viewer/firstPartyOriginalGltfRestWorld.mjs';
import {
  HGPT_PROTOTYPE_HANDOFF_KIND,validateProvisionalModelHandoff
} from '../src/viewer/firstPartyPrototypeModelHandoff.mjs';
import {registerWorkNativePoseSamplesToOriginalGLTF,
  readRegisteredWorkPoseFrame}
  from '../src/viewer/firstPartyWorkNativePoseRegistration.mjs';
const arg=process.argv[2];
if(!arg)throw Error('Usage: node scripts/verify-real-work-native-pose-registration.mjs <actual-W1-artifact-dir> [output.json]');
const dir=path.resolve(arg),manifest=JSON.parse(
  fs.readFileSync(path.join(dir,'pilot_manifest.json'),'utf8')),
  modelName='PROVISIONAL_FUNCTIONAL_SHOULDER_v1.glb',
  bytes=fs.readFileSync(path.join(dir,modelName)),
  exactSha='fda9c5e653044988fd1e5c58fe352f074071c4be008eceba702bbbef96a4ea5f';
assert.equal(createHash('sha256').update(bytes).digest('hex'),exactSha);
assert.equal(manifest.files_sha256[modelName],exactSha);
const unchanged=Buffer.from(bytes),
  source=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
const parsed=parseRestrictedBatchedSkinnedGlb(source,{
  allowProvisionalPilot:true,allowSourceFlatColors:true,
  allowSourceUV0:true,allowSourceNormals:true,
});
const rest=deriveOriginalSourceGLTFRestWorld(source,parsed);
const named=Object.fromEntries(rest.orderedSourceJointNames.map(n=>[n,n]));
const rig={
  sourceToRuntimeBone:named,
  runtimeBoneNames:[...rest.orderedSourceJointNames],
  restWorldByRuntimeBone:rest.sourceWorldRestByName,
  lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED',
};
const signedClaim={
  kind:HGPT_PROTOTYPE_HANDOFF_KIND,
  candidateId:manifest.candidate,
  status:'PROTOTYPE_ONLY',
  glb:{sha256:exactSha,layout:'pilot',sourceFeatures:{
    flatColors:true,uv0:true,normals:true
  }},
  frame:{unit:'metre',up:'Y',handedness:'right',
    basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
  rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
    thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
  rig,releaseApproved:false,
};
const verified=await validateProvisionalModelHandoff(source,signedClaim);
const registered=registerWorkNativePoseSamplesToOriginalGLTF(
  verified,rest,manifest);
assert.equal(registered.originalFrameCount,7);
assert.ok(registered.maximumNativeRestToGLTFWorldResidual<1e-4);
assert.ok(registered.maximumNativeSkinVsGLTFSkinResidual<1e-4);
assert.ok(registered.maximumReturnToRestSkinResidual<1e-4);
assert.equal(registered.motionIsRelativeFromRestNotAbsoluteElevation,true);
const frames=Array.from({length:7},(_,i)=>readRegisteredWorkPoseFrame(registered,i));
for(let i=0;i<frames.length;i++){
  assert.equal(frames[i].timeSeconds,manifest.frames[i].time_seconds);
  assert.equal(frames[i].sourceJointWorldPalette.length,6*16);
}
const snapshot=readRegisteredWorkPoseFrame(registered,1).sourceJointWorldPalette;
snapshot[12]=NaN;
assert.ok(Number.isFinite(readRegisteredWorkPoseFrame(registered,1)
  .sourceJointWorldPalette[12]),'source palette must be immutable and cloned');
assert.deepEqual(bytes,unchanged,'original Work source GLB never modified');
const report={
  kind:registered.kind,sourceOriginalGLBSha256:exactSha,
  sourceFullOriginalGLBRigAndInverseBindVerified:true,
  originalWorkArtifactExactHashVerified:true,
  originalWorkPoseRecords:registered.originalFrameCount,
  sourceWorkControlCount:registered.orderedSourceJointNames.length,
  sourceWorkControlNames:registered.orderedSourceJointNames,
  sourceSampleTimes:registered.originalSampleTimesSeconds,
  authoredArmRotationFromRestDegrees:registered.originalArmRotationFromRestDegrees,
  maxSourceRestComparisonResidual:registered.maximumNativeRestToGLTFWorldResidual,
  maxSourceSkinningPaletteResidual:registered.maximumNativeSkinVsGLTFSkinResidual,
  maxNativeZeroPoseSkinResidual:registered.maximumReturnToRestSkinResidual,
  sourceWorkZUpToGltfYUpRestAndPoseBasisNumericallyVerified:true,
  originalSevenAuthoredSourcePoseMatricesRegistered:true,
  note:'All seven controls samples represent authored rotations from rest, NOT absolute clinical shoulder elevations',
  gltfSourceOriginal18Meshes:verified.numberOfPrimitives,
  originalWorkZUpRowMajorSkinWasReflectedOrRescaled:false,
  physiologyOrExerciseContactAccepted:false,
  originalFullHumanMeshReady:false,
  fullMuscleSkinDeformationApproved:false,
  independentOriginalModelRightsApproved:false,
  productionApproval:false,
};
const out=path.resolve(process.argv[3]||
  'reports/work-pilot/real-W1-native-glTF-basis-and-poses.json');
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
