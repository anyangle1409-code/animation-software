import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSyntheticExerciseHandoff} from './support/buildSyntheticExerciseHandoff.mjs';
import {compileProvisionalPoseSequence,getProvisionalPoseFrame} from '../src/viewer/firstPartyPrototypePoseSequence.mjs';
async function fixture(){
  const x=await buildSyntheticExerciseHandoff();
  const seq=compileProvisionalPoseSequence(x.model,x.clip);
  return {seq,expected:x.clip.frames[1].posedWorldByRuntimeBone.upperarm_l[12]};
}
test('public typed pose buffers cannot change a validated frame or bypass translation screening',async()=>{
  const {seq,expected}=await fixture();
  seq.frames[1].sourceOrderedWorldMatrices[12]=1000;
  assert.equal(getProvisionalPoseFrame(seq,1).sourceOrderedWorldMatrices[12],expected);
  assert.equal(seq.audit.allFramesOriginalSkinOrderNumericallyScreened,true);
});
test('frame API returns isolated copies rather than writable validated state',async()=>{
  const {seq,expected}=await fixture();
  const first=getProvisionalPoseFrame(seq,1);
  first.sourceOrderedWorldMatrices[12]=NaN;
  const next=getProvisionalPoseFrame(seq,1);
  assert.notEqual(first.sourceOrderedWorldMatrices,next.sourceOrderedWorldMatrices);
  assert.equal(next.sourceOrderedWorldMatrices[12],expected);
  assert.equal(next.timeSeconds,.5);
});
test('legacy frame inspection yields fresh snapshots with immutable headers and unchanged safety gates',async()=>{
  const {seq}=await fixture();
  const one=seq.frames,two=seq.frames;
  assert.notEqual(one,two);
  one[0].sourceOrderedWorldMatrices.fill(NaN);
  assert.equal(two[0].sourceOrderedWorldMatrices[0],1);
  assert.equal(getProvisionalPoseFrame(seq,0).sourceOrderedWorldMatrices[0],1);
  assert.ok(Object.isFrozen(one));assert.ok(Object.isFrozen(one[0]));
  assert.equal(seq.audit.productionClipApproved,false);
  assert.equal(seq.audit.wholeBodyExerciseAccuracyAccepted,false);
});
