import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSyntheticFirstPartyGlb} from './support/buildSyntheticFirstPartyGlb.mjs';
import {HGPT_PROTOTYPE_HANDOFF_KIND as MODEL_KIND,
  digestOriginalGlbSha256,validateProvisionalModelHandoff}
  from '../src/viewer/firstPartyPrototypeModelHandoff.mjs';
import {HGPT_PROTOTYPE_CLIP_KIND as CLIP_KIND}
  from '../src/viewer/firstPartyPrototypePoseSequence.mjs';
import {HGPT_INTENT_CLIP_DECLARATION_KIND as DECL_KIND,
  HGPT_BOUND_EXERCISE_KIND as BOUND_KIND,
  bindFirstPartyExerciseToDiagnosticPose as bind,
  getBoundDiagnosticExerciseFrame as frame}
  from '../src/exercise/firstPartyExercisePoseBinding.mjs';
const I=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const T=x=>[1,0,0,0,0,1,0,0,0,0,1,0,x,0,0,1];
async function fixture(command='left arm standing dumbbell shoulder press neutral grip'){
  const glb=buildSyntheticFirstPartyGlb();
  const sha=await digestOriginalGlbSha256(glb);
  const model=await validateProvisionalModelHandoff(glb,{
    kind:MODEL_KIND,candidateId:'OriginalFunctionalPrototype',
    status:'PROTOTYPE_ONLY',
    glb:{sha256:sha,layout:'single',
      sourceFeatures:{flatColors:false,uv0:false,normals:false}},
    frame:{unit:'metre',up:'Y',handedness:'right',
      basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
    rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
      thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
    rig:{sourceToRuntimeBone:{
      test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
      runtimeBoneNames:['upperarm_l','forearm_l'],
      restWorldByRuntimeBone:{upperarm_l:I(),forearm_l:I()},
      lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED'},
    releaseApproved:false
  });
  const clip={
    kind:CLIP_KIND,candidateId:model.candidateId,sourceSha256:model.sourceSha256,
    exerciseId:'overhead_press',approvalStatus:'DIAGNOSTIC_ONLY',
    durationSeconds:1,
    frames:[
      {timeSeconds:0,posedWorldByRuntimeBone:{upperarm_l:I(),forearm_l:I()}},
      {timeSeconds:.5,posedWorldByRuntimeBone:{
        upperarm_l:T(.25),forearm_l:T(.35)}},
      {timeSeconds:1,posedWorldByRuntimeBone:{
        upperarm_l:T(.5),forearm_l:T(.7)}},
    ]
  };
  const declaration={
    kind:DECL_KIND,sourcePoseSetId:'OriginalOverheadDiagnosticA01',
    candidateId:model.candidateId,
    sourceSha256:model.sourceSha256,exerciseId:'overhead_press',
    parameters:{equipment:'dumbbell',laterality:'left',posture:'standing',grip:'neutral'},
    statedOrigin:'WORK_AUTHORED_SOURCE_CLAIM',
    biomechanicsReview:'UNVERIFIED_DIAGNOSTIC',
  };
  return {command,model,clip,declaration,glb};
}
const fails=async(modify,pattern=/Exercise-to-pose binding rejected|G4b pose clip rejected|Provisional model handoff rejected|Exercise intent rejected/)=>{
  const x=await fixture();
  modify(x);
  assert.throws(()=>bind(x.command,x.model,x.clip,x.declaration),pattern);
};
test('actual G4 SHA verified GLB, full G4b poses and strict G4c text join as a diagnostics-only whole clip',async()=>{
  const x=await fixture();
  const b=bind(x.command,x.model,x.clip,x.declaration);
  assert.equal(b.kind,BOUND_KIND);
  assert.equal(b.status,'BOUND_DIAGNOSTIC_ONLY');
  assert.equal(b.exerciseId,'overhead_press');
  assert.equal(b.candidateId,x.model.candidateId);
  assert.equal(b.sourceSha256,x.model.sourceSha256);
  assert.equal(b.sourcePoseSetId,x.declaration.sourcePoseSetId);
  assert.deepEqual(b.requestedParameters,{
    equipment:'dumbbell',laterality:'left',posture:'standing',grip:'neutral'
  });
  assert.deepEqual(b.runtimeJointNames,['upperarm_l','forearm_l']);
  assert.equal(b.frameCount,3);
  assert.deepEqual([frame(b,0).timeSeconds,frame(b,1).timeSeconds,
    frame(b,2).timeSeconds],[0,.5,1]);
  assert.ok(Math.abs(frame(b,1).sourceJointOrderedPalette[12]-.25)<1e-6);
  assert.ok(Math.abs(frame(b,2).sourceJointOrderedPalette[28]-.7)<1e-6);
  assert.ok(b.requiredBiomechanicsVerification.includes('scapulohumeral-coordination'));
  assert.ok(b.requiredBiomechanicsVerification.includes('equipment-contact'));
});
test('source SHA, pose rig and exercise identity reject a foreign candidate',async()=>{
  await fails(x=>{x.declaration.sourceSha256='f'.repeat(64)},/source pose identity/);
  await fails(x=>{x.declaration.candidateId='other'},/source pose identity/);
  await fails(x=>{x.declaration.exerciseId='row'},/source pose identity/);
  await fails(x=>{x.clip.exerciseId='bench_press'},/source pose identity/);
  await fails(x=>{x.clip.sourceSha256='f'.repeat(64)},/SHA\/candidate mismatch/);
  await fails(x=>{x.clip.candidateId='other'},/SHA\/candidate mismatch/);
  await fails(x=>{x.model={...x.model}},/validated prototype/);
});
test('all explicitly described equipment/side/posture/grip must exactly match authored source metadata',async()=>{
  await fails(x=>{x.declaration.parameters.equipment='barbell'},/explicit equipment/);
  await fails(x=>{x.declaration.parameters.laterality='right'},/explicit laterality/);
  await fails(x=>{x.declaration.parameters.laterality=null},/explicit laterality/);
  await fails(x=>{x.declaration.parameters.posture='seated'},/explicit posture/);
  await fails(x=>{x.declaration.parameters.grip=null},/explicit grip/);
  await fails(x=>{x.declaration.parameters.grip='supinated'},/explicit grip/);
  await fails(x=>{x.declaration.parameters.unknown='value'},/exact explicit fields/);
  await fails(x=>{delete x.declaration.parameters.grip},/exact explicit fields/);
});
test('no accidental implicit equivalence between a generic command and a specific clip',async()=>{
  const x=await fixture();
  x.command='dumbbell shoulder press';
  assert.throws(()=>bind(x.command,x.model,x.clip,x.declaration),
    /explicit laterality/);
  x.declaration.parameters.laterality=null;
  assert.throws(()=>bind(x.command,x.model,x.clip,x.declaration),
    /explicit posture/);
  x.declaration.parameters.posture=null;
  assert.throws(()=>bind(x.command,x.model,x.clip,x.declaration),
    /explicit grip/);
  x.declaration.parameters.grip=null;
  const b=bind(x.command,x.model,x.clip,x.declaration);
  assert.equal(b.requestedParameters.laterality,null);
  assert.equal(b.requestedParameters.posture,null);
  assert.equal(b.requestedParameters.grip,null);
});
test('metadata is explicitly unverified, not certified by a submitted declaration',async()=>{
  const x=await fixture();
  const result=bind(x.command,x.model,x.clip,x.declaration);
  assert.equal(result.audit.sourceGLBExactSHAAndBindValidated,true);
  assert.equal(result.audit.everyPoseFrameOriginalRigNumericallyScreened,true);
  assert.equal(result.audit.textAndClipExerciseIdMatch,true);
  for(const key of ['sourcePoseAuthorshipIndependentlyVerified',
    'realHumanMotionIndependentlyVerified','physiologicalRangeOfMotionAccepted',
    'realEquipmentContactOrDynamicsVerified','movementWasGeneratedByText',
    'productionReady'])assert.equal(result.audit[key],false);
  x.declaration.biomechanicsReview='CLINICALLY_ACCEPTED';
  assert.throws(()=>bind(x.command,x.model,x.clip,x.declaration),
    /source authorship is a declaration/);
  x.declaration.biomechanicsReview='UNVERIFIED_DIAGNOSTIC';
  x.declaration.statedOrigin='CERTIFIED_WORK_EVIDENCE';
  assert.throws(()=>bind(x.command,x.model,x.clip,x.declaration),
    /declaration/);
});
test('G4b rigid transforms and timestamps still strictly validated',async()=>{
  await fails(x=>{x.clip.frames[1].timeSeconds=0},/strictly increasing/);
  await fails(x=>{x.clip.frames[1].posedWorldByRuntimeBone.forearm_l=T(NaN)},/nonfinite/);
  await fails(x=>{delete x.clip.frames[1].posedWorldByRuntimeBone.forearm_l},/exact runtime/);
  await fails(x=>{x.clip.approvalStatus='APPROVED_RELEASE'},/cannot approve/);
  await fails(x=>{x.clip.frames=[x.clip.frames[0]]},/2..600/);
});
test('bound palettes are snapshots and callers cannot edit source animation by mutation',async()=>{
  const x=await fixture();
  const result=bind(x.command,x.model,x.clip,x.declaration);
  const original=frame(result,1).sourceJointOrderedPalette[12];
  x.clip.frames[1].posedWorldByRuntimeBone.upperarm_l[12]=9;
  x.declaration.parameters.equipment='barbell';
  const first=frame(result,1);
  first.sourceJointOrderedPalette[12]=-99;
  const fresh=frame(result,1);
  assert.ok(Math.abs(fresh.sourceJointOrderedPalette[12]-original)<1e-8);
  assert.equal(result.requestedParameters.equipment,'dumbbell');
  assert.ok(Object.isFrozen(result));
  assert.ok(Object.isFrozen(result.audit));
  assert.ok(Object.isFrozen(result.requestedParameters));
});
test('cannot read frame from forged binding or invent intermediate frames',async()=>{
  const x=await fixture();
  const result=bind(x.command,x.model,x.clip,x.declaration);
  assert.throws(()=>frame({...result},0),/validated G4d/);
  assert.throws(()=>frame(result,-1),/whole-number authored/);
  assert.throws(()=>frame(result,.5),/whole-number authored/);
  assert.throws(()=>frame(result,3),/whole-number authored/);
  assert.equal(frame(result,0).interpolationPerformed,false);
  assert.equal(frame(result,0).realHumanKinematicsApproved,false);
});
test('safely refuse structurally fake declarations and unregistered inputs',async()=>{
  await fails(x=>{x.declaration.kind='other'},/unsupported/);
  await fails(x=>{x.declaration.sourcePoseSetId='../bad'},/source pose set identifier/);
  await fails(x=>{x.declaration.releaseApproved=true},/exact explicit fields/);
  await fails(x=>{delete x.declaration.sourcePoseSetId},/exact explicit fields/);
  await fails(x=>{x.command='unknown shoulder exercise'},/Exercise intent rejected/);
  await fails(x=>{x.command='shoulder press 30kg'},/Exercise intent rejected/);
  await fails(x=>{x.command='barbell shoulder press'},/explicit equipment/);
});
