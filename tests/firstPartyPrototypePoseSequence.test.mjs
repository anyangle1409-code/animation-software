import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSyntheticFirstPartyGlb} from './support/buildSyntheticFirstPartyGlb.mjs';
import {
  HGPT_PROTOTYPE_HANDOFF_KIND as MODEL_KIND,
  digestOriginalGlbSha256,
  validateProvisionalModelHandoff,
} from '../src/viewer/firstPartyPrototypeModelHandoff.mjs';
import {compileProvisionalPoseSequence as compile,
  getProvisionalPoseFrame as getFrame,
  HGPT_PROTOTYPE_CLIP_KIND as CLIP_KIND,
} from '../src/viewer/firstPartyPrototypePoseSequence.mjs';

const id=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const t=(x=0,y=0,z=0)=>[1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1];
const rz90=()=>[0,1,0,0,-1,0,0,0,0,0,1,0,0,0,0,1];

async function fixture(){
  const bytes=buildSyntheticFirstPartyGlb();
  const sha=await digestOriginalGlbSha256(bytes);
  const manifest={
    kind:MODEL_KIND,candidateId:'FunctionalOriginalPrototype',
    status:'PROTOTYPE_ONLY',
    glb:{sha256:sha,layout:'single',
      sourceFeatures:{flatColors:false,uv0:false,normals:false}},
    frame:{unit:'metre',up:'Y',handedness:'right',
      basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
    rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
      thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
    rig:{
      sourceToRuntimeBone:{test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
      runtimeBoneNames:['upperarm_l','forearm_l'],
      restWorldByRuntimeBone:{upperarm_l:id(),forearm_l:id()},
      lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED',
    },
    releaseApproved:false,
  };
  const model=await validateProvisionalModelHandoff(bytes,manifest);
  const clip={
    kind:CLIP_KIND,candidateId:model.candidateId,
    sourceSha256:model.sourceSha256,
    exerciseId:'original-test-shoulder-reach',
    approvalStatus:'DIAGNOSTIC_ONLY',durationSeconds:1,
    frames:[
      {timeSeconds:0,posedWorldByRuntimeBone:{
        upperarm_l:t(),forearm_l:t()}},
      {timeSeconds:.5,posedWorldByRuntimeBone:{
        upperarm_l:t(.1,0,0),forearm_l:t(.2,0,0)}},
      {timeSeconds:1,posedWorldByRuntimeBone:{
        upperarm_l:t(.2,0,0),forearm_l:t(.3,0,0)}},
    ],
  };
  return {model,clip};
}
test('actual source-SHA-bound rig compiles full ordered 3-frame pose sequence',async()=>{
  const {model,clip}=await fixture();
  const seq=compile(model,clip);
  assert.equal(seq.kind,CLIP_KIND);
  assert.equal(seq.sourceSha256,model.sourceSha256);
  assert.equal(seq.frames.length,3);
  assert.deepEqual(seq.frames.map(f=>f.timeSeconds),[0,.5,1]);
  assert.deepEqual(seq.runtimeBoneNames,['upperarm_l','forearm_l']);
  assert.ok(Math.abs(getFrame(seq,2).sourceOrderedWorldMatrices[12]-.2)<1e-6);
  assert.ok(Math.abs(getFrame(seq,2).sourceOrderedWorldMatrices[28]-.3)<1e-6);
  assert.equal(seq.audit.frameMatricesInterpolated,false);
  assert.equal(seq.audit.wholeBodyExerciseAccuracyAccepted,false);
  assert.equal(seq.audit.loadDependentPhysicsVerified,false);
  assert.equal(seq.audit.productionClipApproved,false);
});
test('material source image or clinical approval cannot be inferred from motion fixtures',async()=>{
  const {model,clip}=await fixture();
  const c=compile(model,clip);
  assert.equal(model.audit.medicallyApprovedHumanSkeleton,false);
  for(const name of ['physiologicalRangeOfMotionApproved','loadDependentPhysicsVerified',
    'realHumanVideoComparisonPassed','wholeBodyExerciseAccuracyAccepted',
    'productionClipApproved'])assert.equal(c.audit[name],false);
  assert.equal(c.audit.sampledFrameCount,3);
  assert.ok(c.audit.maxConsecutiveJointTranslationMetres>.09);
});
test('keeps real relative rotations as matrices rather than shearing interpolation',async()=>{
  const {model,clip}=await fixture();
  clip.frames[1].posedWorldByRuntimeBone.upperarm_l=rz90();
  const r=compile(model,clip);
  assert.ok(Math.abs(r.audit.maxConsecutiveJointRotationRadians-Math.PI/2)<.005);
  assert.equal(r.audit.frameMatricesInterpolated,false);
});
test('refuses clip from another model digest, candidate or exercise identity',async()=>{
  const {model,clip}=await fixture();
  clip.sourceSha256='0'.repeat(64);
  assert.throws(()=>compile(model,clip),/SHA\/candidate mismatch/);
  clip.sourceSha256=model.sourceSha256;
  clip.candidateId='other';
  assert.throws(()=>compile(model,clip),/SHA\/candidate mismatch/);
  clip.candidateId=model.candidateId;
  clip.exerciseId='../unsafe';
  assert.throws(()=>compile(model,clip),/exercise identity/);
  clip.exerciseId='safe';
  clip.approvalStatus='CLINICAL_PASS';
  assert.throws(()=>compile(model,clip),/cannot approve/);
});
test('refuses missing, extra or changed joint data in any frame',async()=>{
  const {model,clip}=await fixture();
  delete clip.frames[1].posedWorldByRuntimeBone.forearm_l;
  assert.throws(()=>compile(model,clip),/exact runtime/);
  clip.frames[1].posedWorldByRuntimeBone.forearm_l=id();
  clip.frames[1].posedWorldByRuntimeBone.extra=id();
  assert.throws(()=>compile(model,clip),/exact runtime/);
  delete clip.frames[1].posedWorldByRuntimeBone.extra;
  clip.frames[1].posedWorldByRuntimeBone.forearm_l=t(NaN,0,0);
  assert.throws(()=>compile(model,clip),/nonfinite/);
});
test('no invalid reflected, scale or nonfinite joint pose transforms are accepted',async()=>{
  const {model,clip}=await fixture();
  clip.frames[0].posedWorldByRuntimeBone.upperarm_l=[
    -1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,
  ];
  assert.throws(()=>compile(model,clip),/reflected/);
  clip.frames[0].posedWorldByRuntimeBone.upperarm_l=[
    2,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,
  ];
  assert.throws(()=>compile(model,clip),/scale/);
  clip.frames[0].posedWorldByRuntimeBone.upperarm_l=t(11,0,0);
  assert.throws(()=>compile(model,clip),/translation exceeds/);
});
test('timestamps are bounded, strictly ordered and span declared full duration',async()=>{
  const {model,clip}=await fixture();
  clip.frames[0].timeSeconds=.1;
  assert.throws(()=>compile(model,clip),/must start at 0/);
  clip.frames[0].timeSeconds=0;
  clip.frames[1].timeSeconds=0;
  assert.throws(()=>compile(model,clip),/strictly increasing/);
  clip.frames[1].timeSeconds=.5;
  clip.frames[2].timeSeconds=.9;
  assert.throws(()=>compile(model,clip),/reach exact exercise duration/);
  clip.frames[2].timeSeconds=1;
  clip.durationSeconds=181;
  assert.throws(()=>compile(model,clip),/duration required/);
});
test('missing frames, unsupported fields and forged handles fail closed',async()=>{
  const {model,clip}=await fixture();
  assert.throws(()=>getFrame({},0),/validated G4b/);
  const result=compile(model,clip);
  assert.throws(()=>getFrame({...result},0),/validated G4b/);
  assert.throws(()=>getFrame(result,-1),/keyframe index/);
  assert.throws(()=>getFrame(result,0.5),/integer keyframe/);
  assert.throws(()=>getFrame(result,3),/keyframe index/);
  clip.frames=[clip.frames[0]];
  assert.throws(()=>compile(model,clip),/2..600/);
  clip.frames=[...result.frames];
  assert.throws(()=>compile(model,clip),/frame 0 must have exact fields/);
});
test('fabricated model handle cannot bypass original G4 SHA and rig binder',async()=>{
  const {model,clip}=await fixture();
  assert.throws(()=>compile({...model},clip),/validated prototype/);
  assert.throws(()=>compile(null,clip),/previous G4 prototype/);
});
