import assert from 'node:assert/strict';
import test from 'node:test';
import {buildSyntheticSourceNormalGLB as fixture} from './support/buildSyntheticSourceNormalGlb.mjs';
import {parseRestrictedBatchedSkinnedGlb as parse}
  from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
import {readRestrictedGlbNormals,HGPT_SOURCE_NORMAL_KIND}
  from '../src/viewer/firstPartyGlbSourceNormals.mjs';
const read=buf=>parse(buf,{allowSourceNormals:true,allowSourceUV0:true});
const fail=(mutate,regex=/GLB NORMAL rejection|GLB rejection/)=>
  assert.throws(()=>read(fixture({mutate})),regex);
const acc=(doc,m=1,p=0)=>doc.accessors[
  doc.meshes[m].primitives[p].attributes.NORMAL];
const view=(doc,m=1,p=0)=>doc.bufferViews[acc(doc,m,p).bufferView];
test('original source-normal decoder declares non-anatomical v1 source subset',()=>{
  assert.equal(HGPT_SOURCE_NORMAL_KIND,'hgpt-g1d-strict-glb-source-normal-v1');
});
test('2 GLB meshes preserve opposite unit source NORMAL directions and UV0 together',()=>{
  const source=fixture();
  const result=read(source);
  assert.equal(result.audit.originalUnitLengthSourceNormalsValidated,true);
  assert.equal(result.audit.sourceNormalsGPUSkinned,false);
  assert.equal(result.audit.actualOriginalHumanMeshUsed,false);
  assert.equal(result.batches.length,2);
  assert.deepEqual([...result.batches[0].sourceNormals],[0,0,1,0,0,1,0,0,1]);
  assert.deepEqual([...result.batches[1].sourceNormals],[0,1,0,0,1,0,0,1,0]);
  assert.equal(result.batches[0].sourceUV0.length,6);
});
test('all 4 parts have matching independent source normals and valid shared skin',()=>{
  const r=read(fixture({meshCount:2,primitivesPerMesh:2}));
  assert.equal(r.batches.length,4);
  assert.deepEqual(r.batches.map(b=>b.sourceNormals[1]),[0,1,1,0]);
  assert.deepEqual(r.batches.map(b=>b.parsed.audit.bonePaletteCount),[2,2,2,2]);
  assert.ok(r.batches.every(b=>b.sourceNormals.every(Number.isFinite)));
});
test('old batch remains source-normal-ignored until explicitly opted into strict unit decoder',()=>{
  const r=parse(fixture(),{allowSourceUV0:true});
  assert.equal(r.batches[0].sourceNormals,null);
  assert.equal(r.audit.originalUnitLengthSourceNormalsValidated,false);
  assert.equal(r.batches[0].parsed.audit.ignoredSourceNormalsAndRecomputeOnDeformation,true);
  assert.throws(()=>read(fixture({mutate:d=>{delete d.meshes[1].primitives[0].attributes.NORMAL;}})),
    /NORMAL accessor must be explicitly present/);
});
test('reject missing NORMAL in second part, count mismatch, wrong accessor component and type',()=>{
  fail(d=>{delete d.meshes[1].primitives[0].attributes.NORMAL},/explicitly present/);
  fail(d=>{acc(d).count=2},/FLOAT VEC3 matching/);
  fail(d=>{acc(d).type='VEC2'},/FLOAT VEC3 matching/);
  fail(d=>{acc(d).componentType=5123},/FLOAT VEC3 matching/);
  fail(d=>{acc(d).normalized=true},/FLOAT VEC3 matching/);
});
test('reject sparse/unknown accessor metadata and untrusted source types',()=>{
  fail(d=>{acc(d).sparse={count:1}},/sparse/);
  fail(d=>{acc(d).extras={web:'https://invalid.local'}},/unknown or sparse/);
  fail(d=>{acc(d).bufferView=999},/embedded BIN/);
  assert.throws(()=>readRestrictedGlbNormals(null,new Uint8Array(0),0,3),/embedded GLB/);
  assert.throws(()=>readRestrictedGlbNormals({},new Uint8Array(0),-1,3),/explicitly present|bounded/);
});
test('refuse malformed float bufferView offsets, stride, declaration and pointers',()=>{
  fail(d=>{view(d).byteOffset=3},/alignment/);
  fail(d=>{acc(d).byteOffset=2},/alignment/);
  fail(d=>{view(d).byteStride=8},/stride/);
  fail(d=>{view(d).byteStride=14},/stride/);
  fail(d=>{view(d).byteStride=256},/stride/);
  fail(d=>{view(d).byteLength=100000},/exceeds bounded BIN/);
  fail(d=>{acc(d).byteOffset=100000},/escapes bufferView/);
  fail(d=>{view(d).buffer=1},/embedded BIN/);
});
test('explicit source normals must be unit length finite, never silently normalized',()=>{
  fail((d,bin)=>{
    new DataView(bin.buffer).setFloat32(view(d).byteOffset,NaN,true);
  },/nonfinite/);
  fail((d,bin)=>{
    new DataView(bin.buffer).setFloat32(view(d).byteOffset,Infinity,true);
  },/nonfinite/);
  fail((d,bin)=>{
    const offset=view(d).byteOffset;
    new DataView(bin.buffer).setFloat32(offset,0,true);
    new DataView(bin.buffer).setFloat32(offset+4,0,true);
    new DataView(bin.buffer).setFloat32(offset+8,0,true);
  },/unit length/);
  fail((d,bin)=>{
    new DataView(bin.buffer).setFloat32(view(d).byteOffset,1.2,true);
  },/unit length/);
});
test('reject source GLB attempting to smuggle image, texture, morph or later UV set',()=>{
  fail(d=>{d.images=[{uri:'https://example.invalid/skin.png'}]},/texture/);
  fail(d=>{d.textures=[{source:0}]},/texture/);
  fail(d=>{d.meshes[1].primitives[0].targets=[{}]},/morph/);
  fail(d=>{d.meshes[1].primitives[0].attributes.TEXCOORD_1=0},/secondary influences|UV/);
  fail(d=>{d.extensionsUsed=['KHR_draco_mesh_compression']},/extensions/);
});
test('original GLB source bytes remain untouched across NORMAL parse and GLB→LBS',()=>{
  const buffer=fixture();
  const untouched=new Uint8Array(buffer).slice();
  const r=read(buffer);
  assert.deepEqual(new Uint8Array(buffer),untouched);
  assert.equal(r.batches[1].sourceNormals.length,9);
  assert.equal(r.audit.productionRuntimeReady,false);
  assert.equal(r.audit.clinicalAnatomyApproved,false);
  assert.equal(r.audit.rightsAndProvenanceApproved,false);
});
test('source normal opt-in is a strict boolean, no accidental enabling by arbitrary input',()=>{
  assert.throws(()=>parse(fixture(),{allowSourceNormals:'true'}),/boolean/);
  assert.throws(()=>parse(fixture(),{allowSourceNormals:1}),/boolean/);
});
