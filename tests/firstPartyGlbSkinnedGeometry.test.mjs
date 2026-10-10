import test from 'node:test';
import assert from 'node:assert/strict';
import { buildSyntheticFirstPartyGlb as sample } from './support/buildSyntheticFirstPartyGlb.mjs';
import { parseRestrictedSkinnedGlb as parse, FIRST_PARTY_GLB_GATE } from '../src/viewer/firstPartyGlbSkinnedGeometry.mjs';
import { deformIndexedSkin } from '../src/viewer/firstPartyIndexedSkinnedMesh.mjs';

const shift=(x,y,z)=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1]);
const epsilon=(a,b)=>assert.ok(Math.abs(a-b)<=1e-6,a+' != '+b);
const rejects=(change,message)=>
  assert.throws(()=>parse(sample(change)),new RegExp(message,'i'));
test('original synthetic GLB2 embedded buffer parses into real first-party four-weight geometry',()=>{
  const result=parse(sample());
  assert.equal(result.kind,FIRST_PARTY_GLB_GATE);
  assert.equal(result.audit.vertices,3);
  assert.equal(result.audit.indexedTriangles,1);
  assert.equal(result.audit.bonePaletteCount,2);
  assert.deepEqual(result.jointNodeNames,['test_upperarm_l','test_forearm_l']);
  assert.deepEqual([...result.mesh.positions],[0,0,0,1,0,0,0,1,0]);
  assert.deepEqual([...result.mesh.indices],[0,1,2]);
  assert.deepEqual([...result.mesh.weights.slice(0,4)],[.75,.25,0,0]);
  assert.ok(result.audit.strictUnsupportedContentRejected);
  assert.equal(result.audit.originalFullBodyCharacterLoaded,false);
  assert.equal(result.audit.sourceProvenanceOrRedistributionApproved,false);
});
test('actual GLB decoded vertex weights deform correctly through existing native CPU skinning',()=>{
  const glb=parse(sample());
  const posed=new Float32Array([...shift(1,0,0),...shift(0,2,0)]);
  const result=deformIndexedSkin(glb.mesh,posed);
  epsilon(result.positions[0],.75);epsilon(result.positions[1],.5);
  epsilon(result.positions[3],1.75);epsilon(result.positions[4],.5);
  assert.equal(result.triangleCount,1);
});
test('fixture builder is byte-for-byte deterministic',()=>{
  assert.deepEqual(new Uint8Array(sample()),new Uint8Array(sample()));
});
test('reject malformed magic, length, version and arbitrary trailing chunk',()=>{
  for(const [offset,value,description] of [
    [0,0,'GLB magic'],[4,3,'GLB 2.0'],[8,1024,'file size mismatch'],
    [12,1,'chunk length']
  ]){
    const b=sample();
    new DataView(b).setUint32(offset,value,true);
    assert.throws(()=>parse(b),new RegExp(description,'i'));
  }
  assert.throws(()=>parse(new ArrayBuffer(8)),/length/);
  assert.throws(()=>parse(new Uint8Array(sample())),/ArrayBuffer/);
});
test('reject external buffer, extension, texture and executable animation content',()=>{
  rejects(g=>{g.buffers[0].uri='https://example.com/thirdparty.bin'},/URI/);
  rejects(g=>{g.extensionsRequired=['KHR_draco_mesh_compression']},/extensions/);
  rejects(g=>{g.extensionsUsed=['EXT_meshopt_compression']},/extensions/);
  rejects(g=>{g.images=[{uri:'not-allowed.png'}]},/texture/);
  rejects(g=>{g.textures=[{source:0}]},/texture/);
  rejects(g=>{g.animations=[{}]},/texture|animation/);
  rejects(g=>{g.cameras=[{}]},/camera/);
});
test('reject materials, morphs, second primitives, extra influence sets and alternate topologies',()=>{
  rejects(g=>{g.meshes[0].primitives[0].material=0},/material/);
  rejects(g=>{g.meshes[0].primitives[0].targets=[{}]},/morph/);
  rejects(g=>{g.meshes[0].primitives.push({...g.meshes[0].primitives[0]})},/single/);
  rejects(g=>{g.meshes[0].primitives[0].attributes.JOINTS_1=1},/secondary/);
  rejects(g=>{g.meshes[0].primitives[0].mode=1},/TRIANGLES/);
  rejects(g=>{delete g.meshes[0].primitives[0].indices},/unindexed/);
});
test('reject missing extra skins, bones, joint mapping, and duplicated joint identity',()=>{
  rejects(g=>{g.skins=[]},/one skin/);
  rejects(g=>{g.skins[0].joints=[1,1]},/duplicate/);
  rejects(g=>{g.skins[0].joints=[1,987]},/bad bone node/);
  rejects(g=>{delete g.nodes[1].name},/names/);
  rejects(g=>{g.nodes[2].name=g.nodes[1].name},/duplicate joint names/);
  rejects(g=>{g.skins[0].inverseBindMatrices=undefined},/inverse bind/);
  rejects(g=>{g.nodes[0].skin=undefined},/one explicit/);
});
test('do not silently ignore nonidentity mesh/world node transforms',()=>{
  rejects(g=>{g.nodes[0].translation=[2,0,0]},/nonidentity/);
  rejects(g=>{g.nodes[0].scale=[1,2,1]},/nonidentity/);
  rejects(g=>{g.nodes[1].children=[0]},/nested/);
});
test('reject sparse buffer data, undeclared stride, or buffer view overflow',()=>{
  rejects(g=>{g.accessors[0].sparse={count:1,indices:{},values:{}}},/sparse/);
  rejects(g=>{g.bufferViews[0].byteStride=4},/stride/);
  rejects(g=>{g.bufferViews[0].byteLength=9999},/buffer/);
  rejects(g=>{g.accessors[0].byteOffset=9999},/escapes/);
  rejects(g=>{g.bufferViews[0].buffer=3},/embedded/);
  rejects(g=>{g.buffers[0].byteLength=4},/buffer/);
});
test('reject malformed typed accessors or counts',()=>{
  rejects(g=>{g.accessors[0].type='VEC2'},/VEC3/);
  rejects(g=>{g.accessors[1].componentType=5126},/component/);
  rejects(g=>{g.accessors[2].count=2},/count mismatch/);
  rejects(g=>{g.accessors[4].count=1},/inverse bind count/);
  rejects(g=>{g.accessors[3].count=2},/indexed triangles/);
  rejects(g=>{g.accessors[1].normalized=true},/normalized joint/);
});
test('reject malformed bound index, zero weights and nonfinite coordinates in actual BIN',()=>{
  rejects((g,bin)=>{
    const offset=g.bufferViews[3].byteOffset;
    new DataView(bin.buffer).setUint16(offset,44,true);
  },/triangle vertex/);
  rejects((g,bin)=>{
    new DataView(bin.buffer).setFloat32(g.bufferViews[0].byteOffset,NaN,true);
  },/nonfinite/);
  rejects((g,bin)=>{
    const off=g.bufferViews[2].byteOffset;
    for(let i=0;i<3;i++){
      new DataView(bin.buffer).setFloat32(off+i*16,0,true);
      new DataView(bin.buffer).setFloat32(off+i*16+4,0,true);
    }
  },/weight/);
});
test('honest raw source gates forbid auto-upgrading geometry to original character',()=>{
  const x=parse(sample());
  for(const key of [
    'canonicalBoneMappingVerified','glTF_jointNodePoseToOriginalRigVerified',
    'physicalSkeletonToHumanStatureRegistered',
    'sourceProvenanceOrRedistributionApproved','sourceSkinningAppearanceValidated',
    'originalFullBodyCharacterLoaded','allOriginalRuntimeDependenciesRemoved',
    'productionReady'
  ])assert.equal(x.audit[key],false,key+' was falsely accepted');
});
