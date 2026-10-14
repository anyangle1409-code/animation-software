import test from 'node:test';
import assert from 'node:assert/strict';
import {compileDiagnosticMorphs,prepareDiagnosticMorphFrame} from '../src/viewer/firstPartyCorrectiveMorphs.mjs';
import {deformIndexedSkin} from '../src/viewer/firstPartyIndexedSkinnedMesh.mjs';
const I=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
function fixture(){
  return {mesh:{positions:new Float32Array([0,0,0,1,0,0,0,1,0]),
    jointIndices:new Uint16Array(12),weights:new Float32Array([1,0,0,0,1,0,0,0,1,0,0,0]),
    indices:new Uint16Array([0,1,2]),inverseBindMatrices:new Float32Array(I)},
    normals:new Float32Array([0,0,1,0,0,1,0,0,1]),
    morphs:[{name:'knee_contact_l',position:{indices:new Uint32Array([0]),deltas:new Float32Array([.1,0,0])},
      normal:{indices:new Uint32Array([0]),deltas:new Float32Array([.2,0,0])}}]};
}
const compile=f=>compileDiagnosticMorphs(f.mesh,f.normals,f.morphs,{reviewOnly:true});
test('sparse POSITION/NORMAL correctives apply before existing first-party LBS',()=>{
  const f=fixture(),h=compile(f),p=prepareDiagnosticMorphFrame(h,{knee_contact_l:1});
  const world=new Float32Array(I);world[12]=.2;
  const deformed=deformIndexedSkin(p.mesh,world);
  assert.ok(Math.abs(deformed.positions[0]-.3)<1e-6);
  assert.ok(Math.abs(Math.hypot(...p.sourceNormals.slice(0,3))-1)<1e-6);
  assert.ok(p.sourceNormals[0]>.19);assert.equal(p.productionApproved,false);
  assert.equal(f.mesh.positions[0],0);assert.equal(f.normals[0],0);
});
test('zero rest weights and snapshots protect original arrays and future frames',()=>{
  const f=fixture(),h=compile(f);f.mesh.positions[0]=9;f.morphs[0].position.deltas[0]=9;
  const zero=prepareDiagnosticMorphFrame(h,{knee_contact_l:0});assert.equal(zero.mesh.positions[0],0);
  zero.mesh.positions[0]=8;
  assert.ok(Math.abs(prepareDiagnosticMorphFrame(h,{knee_contact_l:1}).mesh.positions[0]-.1)<1e-6);
  assert.throws(()=>prepareDiagnosticMorphFrame({...h},{knee_contact_l:0}),/compiled/);
});
test('rejects absent opt-in, invalid sparse indices, nonfinite/unbounded deltas and unknown weights',()=>{
  let f=fixture();assert.throws(()=>compileDiagnosticMorphs(f.mesh,f.normals,f.morphs),/opt-in/);
  for(const alter of [f=>f.morphs[0].position.indices[0]=3,
    f=>f.morphs[0].position.deltas[0]=NaN,f=>f.morphs[0].position.deltas[0]=.3,
    f=>f.morphs.push(f.morphs[0]),f=>f.morphs[0].normal.indices=new Uint32Array([0,0])]){
    f=fixture();alter(f);assert.throws(()=>compile(f));
  }
  const h=compile(fixture());
  for(const weights of [{},{knee_contact_l:NaN},{knee_contact_l:2},{knee_contact_l:0,other:0}])
    assert.throws(()=>prepareDiagnosticMorphFrame(h,weights));
});
test('refuses a corrective combination that cancels a source normal',()=>{
  const f=fixture();f.morphs[0].normal.deltas=new Float32Array([0,0,-1]);
  const h=compile(f);assert.throws(()=>prepareDiagnosticMorphFrame(h,{knee_contact_l:1}),/normal/);
});
