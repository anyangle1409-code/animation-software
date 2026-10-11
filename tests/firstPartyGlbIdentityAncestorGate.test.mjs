import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSyntheticBatchedGlb}
  from './support/buildSyntheticBatchedGlb.mjs';
import {parseRestrictedBatchedSkinnedGlb as parse}
  from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
import {checkOriginalPilotIdentityMeshAncestry as ancestry,
  exposeVerifiedPilotMeshAsValidationRoot as promote}
  from '../src/viewer/firstPartyGlbIdentityAncestorGate.mjs';
const fixture=()=>{
  const root={nodes:[
    {name:'WorkExportRoot',children:[1,2]},
    {name:'partA',mesh:0,skin:0},
    {name:'partB',mesh:1,skin:0}
  ],scene:0,scenes:[{nodes:[0]}]};
  return root;
};
const map=()=>new Map([[0,1],[1,2]]);
test('accepts exactly identity source scene wrapper without source joint or object rewrite',()=>{
  const source=fixture(),backup=structuredClone(source);
  const check=ancestry(source,[0],map());
  assert.equal(check.sourceMeshAncestors.length,2);
  assert.equal(check.anyIdentityGroupPromotion,true);
  assert.equal(check.sourceBoneHierarchyChanged,false);
  assert.deepEqual(source,backup);
  const validationCopy=structuredClone(source);
  const didPromote=promote(validationCopy,1,check);
  assert.equal(didPromote,true);
  assert.deepEqual(validationCopy.scenes[0].nodes,[0,1]);
  assert.deepEqual(validationCopy.nodes[0].children,[2]);
  assert.deepEqual(source,backup);
});
test('old direct scene root mesh still valid in pilot with no needless relocation',()=>{
  const source={nodes:[{mesh:0,skin:0,name:'source_part'}],
    scene:0,scenes:[{nodes:[0]}]};
  const check=ancestry(source,[0],new Map([[0,0]]));
  assert.equal(check.anyIdentityGroupPromotion,false);
  assert.equal(promote(structuredClone(source),0,check),false);
});
test('multiple strictly identity grouping levels preserve original skeleton structure',()=>{
  const source=fixture();
  source.nodes.unshift({name:'gltfWrapper',children:[1]});
  source.nodes[1].children=[2,3];
  source.scenes[0].nodes=[0];
  const c=ancestry(source,[0],new Map([[0,2],[1,3]]));
  assert.deepEqual(c.sourceMeshAncestors[0].ancestorIndices,[1,0]);
  assert.equal(c.anyIdentityGroupPromotion,true);
});
test('refuse nonidentity translation, rotation, scale and matrix for a source mesh ancestor',()=>{
  const mutations=[
    n=>n.translation=[.001,0,0],
    n=>n.rotation=[0,0,.02,.9998],
    n=>n.scale=[1,1.05,1],
    n=>n.matrix=[1,0,0,0,0,1,0,0,0,0,1,0,.25,0,0,1],
    n=>n.mesh=17,
    n=>n.skin=0,
    n=>n.extensions={unsafe:true},
  ];
  for(const mutate of mutations){
    const root=fixture();mutate(root.nodes[0]);
    assert.throws(()=>ancestry(root,[0],map()),
      /nonidentity or unsupported source ancestor/,String(mutate));
  }
});
test('rejects root child self-parent, repeated node, double parent and hidden cycles',()=>{
  {
    const r=fixture();r.nodes[0].children=[0,1,2];
    assert.throws(()=>ancestry(r,[0],map()),/self-parenting/);
  }
  {
    const r=fixture();r.nodes[0].children=[1,1,2];
    assert.throws(()=>ancestry(r,[0],map()),/duplicate child/);
  }
  {
    const r=fixture();r.nodes.push({name:'extra',children:[1]});
    assert.throws(()=>ancestry(r,[0],map()),/multiple parents/);
  }
  {
    const r=fixture();r.nodes.push({name:'isolatedCycleA',children:[4]});
    r.nodes.push({name:'isolatedCycleB',children:[3]});
    assert.throws(()=>ancestry(r,[0],map()),/cyclic source node/);
  }
});
test('rejects unrooted mesh and mesh ancestor even with identity transform',()=>{
  {
    const r=fixture();r.nodes[0].children=[1];
    assert.throws(()=>ancestry(r,[0],map()),/reachable from active scene roots/);
  }
  {
    const r=fixture();r.nodes[1].children=[2];
    r.nodes[0].children=[1];
    assert.throws(()=>ancestry(r,[0],map()),/skinned mesh cannot have a mesh ancestor/);
  }
});
const wrapped18=()=>buildSyntheticBatchedGlb({
  meshCount:18,allowProvisionalPilot:true,
  mutate:root=>{
    const priorRoots=[...root.scenes[0].nodes];
    const group=root.nodes.length;
    root.nodes.push({name:'WorkIdentityExportRoot',children:priorRoots});
    root.scenes[0].nodes=[group];
  },
});
test('real G4f source adapter accepts 18 nested source meshes behind identity-only root',()=>{
  const glb=wrapped18(),bytes=new Uint8Array(glb).slice();
  const parsed=parse(glb,{allowProvisionalPilot:true});
  assert.equal(parsed.audit.numberOfMeshes,18);
  assert.equal(parsed.audit.numberOfPrimitives,18);
  assert.equal(parsed.audit.verifiedIdentityGroupSourceMeshAncestry,true);
  assert.equal(parsed.audit.sourceBoneHierarchyChanged,false);
  assert.equal(parsed.audit.clinicalAnatomyApproved,false);
  assert.equal(parsed.audit.productionRuntimeReady,false);
  assert.equal(parsed.batches.length,18);
  assert.deepEqual(new Uint8Array(glb),bytes);
});
test('historic non-pilot GLB rules still reject nested meshes even when identity-rooted',()=>{
  const glb=wrapped18();
  assert.throws(()=>parse(glb),/bounded original skinned meshes/);
});
test('adapter rejects nested Work GLB when parent has nonidentity source transform',()=>{
  const glb=buildSyntheticBatchedGlb({
    meshCount:18,allowProvisionalPilot:true,
    mutate:root=>{
      const prev=[...root.scenes[0].nodes];
      const parent=root.nodes.length;
      root.nodes.push({name:'UnsafeMovedMeshes',
        children:prev,translation:[1,0,0]});
      root.scenes[0].nodes=[parent];
    }
  });
  assert.throws(()=>parse(glb,{allowProvisionalPilot:true}),
    /nonidentity or unsupported source ancestor/);
});
test('an attacker cannot request source-mesh promotion using a forged graph',()=>{
  const s=fixture();
  assert.throws(()=>promote(structuredClone(s),1,{
    kind:'forged',sourceMeshAncestors:[{nodeIndex:1}]
  }),/only a strictly validated source pilot/);
});
