import assert from 'node:assert/strict';
import test from 'node:test';
import {buildSyntheticBatchedGlb as fixture} from './support/buildSyntheticBatchedGlb.mjs';
import {parseRestrictedBatchedSkinnedGlb as parse}
  from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
const red={name:'project_firstparty_red',pbrMetallicRoughness:{
  baseColorFactor:[.94,.28,.21,1],metallicFactor:0,roughnessFactor:1}};
const green={name:'project_firstparty_green',pbrMetallicRoughness:{
  baseColorFactor:[.16,.86,.30,1],metallicFactor:0,roughnessFactor:1}};
function colored(mutate=()=>{}){
  return fixture({mutate:(g,bin)=>{
    g.materials=[structuredClone(red),structuredClone(green)];
    g.meshes[0].primitives[0].material=0;
    g.meshes[1].primitives[0].material=1;
    mutate(g,bin);
  }});
}
const decode=buffer=>parse(buffer,{allowSourceFlatColors:true});
const bad=(fn,re)=>assert.throws(()=>decode(colored(fn)),re);

test('default G1a strict GLB loader still refuses material-bearing source',()=>{
  assert.throws(()=>parse(colored()),/materials refused/);
});
test('opt-in G1b reads two separate source-material RGB triplets in source primitive order',()=>{
  const r=decode(colored());
  assert.deepEqual(r.batches.map(x=>x.materialColor),
    [[.94,.28,.21],[.16,.86,.3]]);
  assert.deepEqual(r.batches.map(x=>x.sourceMaterialIndex),[0,1]);
  assert.equal(r.audit.flatOpaqueSourceColorsValidated,true);
  assert.equal(r.audit.textureSamplingImplemented,false);
  assert.equal(r.audit.metallicRoughnessPBRImplemented,false);
  assert.equal(r.audit.clinicalAnatomyApproved,false);
  assert.equal(r.audit.productionRuntimeReady,false);
  assert.equal(Object.isFrozen(r.batches[0].materialColor),true);
});
test('strict existing zero-material glTF geometry remains supported in opt-in mode',()=>{
  const r=decode(fixture());
  assert.equal(r.batches.length,2);
  assert.deepEqual(r.batches.map(x=>x.materialColor),
    [[.74,.8,.92],[.74,.8,.92]]);
});
test('strict material index bounds and material count refusal',()=>{
  bad(g=>{g.meshes[1].primitives[0].material=99},/invalid material index/);
  bad(g=>{g.meshes[1].primitives[0].material=-1},/invalid material index/);
  bad(g=>{g.meshes[1].primitives[0].material=1.2},/invalid material index/);
  bad(g=>{g.materials=Array(9).fill(red)},/material count/);
});
test('reject texture PBR extensions, unknown fields and source material execution metadata',()=>{
  bad(g=>{g.materials[0].pbrMetallicRoughness.baseColorTexture={index:0}},
    /texture\/unsupported/);
  bad(g=>{g.materials[0].normalTexture={index:0}},/unsupported glTF material/);
  bad(g=>{g.materials[0].extensions={KHR_materials_clearcoat:{}}},/unsupported glTF material/);
  bad(g=>{g.materials[1].extras={externalURL:'https://example.invalid/code'}},/unsupported glTF material/);
  bad(g=>{g.images=[{uri:'https://example.invalid/a.png'}]},/texture/);
});
test('reject invalid physical shading assumptions and transparency',()=>{
  bad(g=>{g.materials[0].pbrMetallicRoughness.metallicFactor=1},/only matte/);
  bad(g=>{g.materials[0].pbrMetallicRoughness.roughnessFactor=.5},/only matte/);
  bad(g=>{g.materials[0].alphaMode='BLEND'},/OPAQUE/);
  bad(g=>{g.materials[0].alphaMode='MASK'},/OPAQUE/);
  bad(g=>{g.materials[1].doubleSided=true},/two-sided/);
});
test('reject nonfinite, oversized or translucent RGBA source values',()=>{
  bad(g=>{g.materials[0].pbrMetallicRoughness.baseColorFactor=[NaN,.2,.3,1]},/opaque finite/);
  bad(g=>{g.materials[0].pbrMetallicRoughness.baseColorFactor=[2,.2,.3,1]},/opaque finite/);
  bad(g=>{g.materials[0].pbrMetallicRoughness.baseColorFactor=[.2,.2,.3,.8]},/opaque finite/);
  bad(g=>{g.materials[0].pbrMetallicRoughness.baseColorFactor=[.2,.3,1]},/opaque finite/);
  bad(g=>{delete g.materials[0].pbrMetallicRoughness.baseColorFactor},/opaque finite/);
});
test('every source material must be used and validated, not silently discarded',()=>{
  bad(g=>{g.materials.push({name:'unused_bad',alphaMode:'BLEND'})},/unused/);
  bad(g=>{delete g.meshes[1].primitives[0].material},/unused/);
});
test('malformed second material fails even if first source mesh is valid',()=>{
  bad(g=>{g.materials[1].pbrMetallicRoughness.baseColorFactor=[.2,.3,.4,.5]},/opaque finite/);
  bad(g=>{delete g.materials[1].pbrMetallicRoughness},/explicit flat/);
});
test('top-level required extension still rejected even when material index sanitised for strict parser',()=>{
  bad(g=>{g.extensionsRequired=['KHR_materials_unlit']},/extensions/);
  bad(g=>{g.extensionsUsed=['KHR_texture_transform']},/extensions/);
});
test('source GLB binary remains identical and original vertex weights preserved',()=>{
  const asset=colored();
  const copy=new Uint8Array(asset).slice();
  const r=decode(asset);
  assert.deepEqual(new Uint8Array(asset),copy);
  assert.equal(r.audit.decodedVertices,6);
  for(const part of r.batches)assert.deepEqual(
    [...part.parsed.mesh.weights.slice(0,4)],[.75,.25,0,0]);
});
test('source material colors cannot magically authorize original-human provenance or a production renderer',()=>{
  const r=decode(colored());
  for(const k of ['clinicalAnatomyApproved','rightsAndProvenanceApproved',
    'productionRuntimeReady','actualOriginalHumanMeshUsed'])
    assert.equal(r.audit[k],false,k+' falsely promoted');
});
