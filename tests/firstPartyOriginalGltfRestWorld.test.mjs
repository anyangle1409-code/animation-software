import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSyntheticBatchedGlb}
  from './support/buildSyntheticBatchedGlb.mjs';
import {parseRestrictedBatchedSkinnedGlb as parse}
  from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
import {deriveOriginalSourceGLTFRestWorld as derive,
  HGPT_GLTF_REST_WORLD_KIND}
  from '../src/viewer/firstPartyOriginalGltfRestWorld.mjs';

function source(mutate){
  return buildSyntheticBatchedGlb({
    meshCount:18,allowProvisionalPilot:true,
    mutate
  });
}
const accept=source=>parse(source,{allowProvisionalPilot:true});
test('18-mesh synthetic source glTF world rest exactly inverts copied source inverse bind',()=>{
  const glb=source(),before=new Uint8Array(glb).slice();
  const scene=accept(glb);
  const out=derive(glb,scene);
  assert.equal(out.kind,HGPT_GLTF_REST_WORLD_KIND);
  assert.equal(out.sourceJointCount,2);
  assert.deepEqual(out.orderedSourceJointNames,scene.jointNodeNames);
  assert.ok(out.maximumWorldInverseBindResidual<1e-5);
  for(const name of out.orderedSourceJointNames){
    const world=out.sourceWorldRestByName[name];
    assert.equal(world.length,16);
    assert.ok(Object.isFrozen(world));
  }
  assert.equal(out.nativeWorkZUpRowMajorPoseFramesIndependentlyRegistered,false);
  assert.equal(out.arbitraryHumanExerciseMotionApproved,false);
  assert.equal(out.productionReady,false);
  assert.deepEqual(new Uint8Array(glb),before);
});
test('source GLB joints cannot drift from their inverse binds unnoticed',()=>{
  const glb=source(root=>{
    const i=root.skins[0].joints[0];
    root.nodes[i].translation=[.1,0,0];
  });
  const scene=accept(glb);
  assert.throws(()=>derive(glb,scene),
    /original glTF joint world rest does not numerically invert/);
});
test('source GLB invalid quaternion magnitude cannot make a fake original human rest',()=>{
  const glb=source(root=>{
    const i=root.skins[0].joints[0];
    root.nodes[i].rotation=[0,0,0,.4];
  });
  const scene=accept(glb);
  assert.throws(()=>derive(glb,scene),/source quaternion not unit length/);
});
test('source rig matrix shears and reflections are rejected before reference inference',()=>{
  const glb=source(root=>{
    const i=root.skins[0].joints[0];
    root.nodes[i].scale=[-1,1,1];
  });
  const scene=accept(glb);
  assert.throws(()=>derive(glb,scene),/reflected\/inverted source joint basis/);
});
test('forged unvalidated model scene fails closed',()=>{
  const glb=source();
  const real=accept(glb);
  assert.throws(()=>derive(glb,{
    ...real,audit:{...real.audit,sourceGeometryDecoded:false},
  }),/strict verified first-party/);
  assert.throws(()=>derive(glb,{
    ...real,batches:[{parsed:{mesh:{inverseBindMatrices:'fake'}}}],
  }),/strict verified first-party/);
});
