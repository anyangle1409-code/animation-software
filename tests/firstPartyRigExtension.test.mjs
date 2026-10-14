import test from 'node:test';
import assert from 'node:assert/strict';
import * as api from '../src/viewer/firstPartyRigExtension.mjs';
const I=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const base=()=>({sourceSha256:'a'.repeat(64),jointNames:Array.from({length:67},(_,i)=>'base_'+i)});
const manifest=()=>({kind:'hgpt-provisional-rig-extension-v2',status:'REVIEW_ONLY',
  baseSourceSha256:'a'.repeat(64),sourceSha256:'b'.repeat(64),
  baseJointNames:base().jointNames,
  extensions:[{name:'deltoid_helper_l',parent:'base_10',role:'shoulder_helper'},
    {name:'toe_01_r',parent:'base_60',role:'individual_toe'}],
  morphNames:['knee_contact_l','elbow_contact_r'],releaseApproved:false});
const frame=c=>({sourceSha256:c.sourceSha256,
  posedWorldByJoint:Object.fromEntries(c.jointNames.map(n=>[n,I()])),
  morphWeights:{knee_contact_l:.5,elbow_contact_r:0}});
test('opt-in v2 appends helpers/toes without changing baseline palette order',()=>{
  const c=api.compileRigExtension(base(),manifest(),{reviewOnly:true});
  assert.equal(c.jointNames.length,69);assert.deepEqual(c.jointNames.slice(0,67),base().jointNames);
  assert.equal(c.releaseApproved,false);assert.equal(c.sourceBytesVerified,false);
  const f=api.packExtendedReviewPose(c,frame(c));
  assert.equal(f.posedWorld.length,69*16);assert.deepEqual([...f.morphWeights],[.5,0]);
});
test('rejects default use, unknown schema, baseline reorder and duplicate names',()=>{
  assert.throws(()=>api.compileRigExtension(base(),manifest()),/opt-in/);
  for(const alter of [m=>m.kind='v3',m=>m.baseJointNames.reverse(),
    m=>m.extensions[0].name='base_0',m=>m.releaseApproved=true,
    m=>m.extra=true,m=>m.extensions[0].role='anatomical_replacement',
    m=>m.extensions[0].parent='missing']){
    const m=manifest();alter(m);assert.throws(()=>api.compileRigExtension(base(),m,{reviewOnly:true}));
  }
});
test('requires complete authored helper world transforms and exact morph weights',()=>{
  const c=api.compileRigExtension(base(),manifest(),{reviewOnly:true});
  for(const alter of [f=>delete f.posedWorldByJoint.deltoid_helper_l,
    f=>f.posedWorldByJoint.extra=I(),f=>f.sourceSha256='c'.repeat(64),
    f=>f.posedWorldByJoint.base_0[0]=2,f=>f.posedWorldByJoint.base_0[12]=11,
    f=>f.morphWeights.knee_contact_l=NaN,f=>f.morphWeights.knee_contact_l=1.1,
    f=>delete f.morphWeights.elbow_contact_r]){
    const f=frame(c);alter(f);assert.throws(()=>api.packExtendedReviewPose(c,f));
  }
  assert.throws(()=>api.packExtendedReviewPose({...c},frame(c)),/compiled/);
});
test('snapshots contract input and rejects forward/cyclic parents and resource excess',()=>{
  const m=manifest(),c=api.compileRigExtension(base(),m,{reviewOnly:true});
  m.extensions[0].name='mutated';m.morphNames[0]='mutated';
  assert.equal(c.jointNames[67],'deltoid_helper_l');assert.equal(c.morphNames[0],'knee_contact_l');
  const bad=manifest();bad.extensions[0].parent=bad.extensions[1].name;
  assert.throws(()=>api.compileRigExtension(base(),bad,{reviewOnly:true}),/parent/);
  bad.extensions=Array.from({length:62},(_,i)=>({name:'helper_'+i,parent:'base_0',role:'shoulder_helper'}));
  assert.throws(()=>api.compileRigExtension(base(),bad,{reviewOnly:true}),/128/);
});
