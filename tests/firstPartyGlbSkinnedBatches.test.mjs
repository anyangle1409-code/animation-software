import assert from 'node:assert/strict';
import test from 'node:test';
import { buildSyntheticBatchedGlb as fixture }
  from './support/buildSyntheticBatchedGlb.mjs';
import { parseRestrictedBatchedSkinnedGlb as parse,
  FIRST_PARTY_SCENE_BATCH_KIND } from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
import { deformIndexedSkin } from '../src/viewer/firstPartyIndexedSkinnedMesh.mjs';
import { validateNativeGLBToRigBinding,packMappedWorldPalette }
  from '../src/viewer/firstPartyGlbRigBindingContract.mjs';
const id=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
const pose=(x,y)=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,x,y,0,1]);
const check=(change,re=/GLB batch rejection|GLB rejection/)=>
  assert.throws(()=>parse(fixture({mutate:change})),re);

test('decodes two distinct source-owned skinned meshes with shared bound joints',()=>{
  const result=parse(fixture());
  assert.equal(result.kind,FIRST_PARTY_SCENE_BATCH_KIND);
  assert.equal(result.batches.length,2);
  assert.equal(result.audit.numberOfMeshes,2);
  assert.equal(result.audit.numberOfPrimitives,2);
  assert.equal(result.audit.decodedVertices,6);
  assert.equal(result.audit.indexedTriangles,2);
  assert.deepEqual(result.batches.map(p=>[p.meshIndex,p.primitiveIndex]),[[0,0],[1,0]]);
  assert.deepEqual(result.batches.map(p=>p.sourceMeshNodeIndex),[0,3]);
  assert.deepEqual([...result.batches[0].parsed.mesh.positions.slice(0,3)],[0,0,0]);
  assert.deepEqual([...result.batches[1].parsed.mesh.positions.slice(0,3)],[1.5,.25,0]);
  assert.deepEqual(result.jointNodeNames,['test_upperarm_l','test_forearm_l']);
  for(const key of [
    'actualOriginalHumanMeshUsed','clinicalAnatomyApproved',
    'rightsAndProvenanceApproved','productionRuntimeReady'
  ])assert.equal(result.audit[key],false);
});
test('decodes one mesh with multiple primitives, without silently dropping any',()=>{
  const r=parse(fixture({meshCount:1,primitivesPerMesh:3}));
  assert.deepEqual(r.batches.map(x=>x.meshIndex),[0,0,0]);
  assert.deepEqual(r.batches.map(x=>x.primitiveIndex),[0,1,2]);
  assert.equal(r.audit.decodedVertices,9);
  assert.equal(r.audit.indexedTriangles,3);
  assert.ok(r.batches[2].parsed.mesh.positions[0]>.8);
});
test('decodes combined two meshes and two primitives, preserving independent order',()=>{
  const r=parse(fixture({meshCount:2,primitivesPerMesh:2}));
  assert.deepEqual(r.batches.map(x=>[x.meshIndex,x.primitiveIndex]),
    [[0,0],[0,1],[1,0],[1,1]]);
  assert.equal(r.audit.decodedVertices,12);
  assert.equal(r.audit.indexedTriangles,4);
  assert.equal(r.batches.length,4);
  assert.notEqual(r.batches[0].parsed.mesh.positions[0],r.batches[3].parsed.mesh.positions[0]);
});
test('both parts consume exact validated source→nominal-rig mapping with real skin deformation',()=>{
  const r=parse(fixture());
  let meshes=0;
  for(const {parsed} of r.batches){
    const plan=validateNativeGLBToRigBinding(parsed,{
      sourceToCanonical:{test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
      allowedCanonicalNames:['upperarm_l','forearm_l'],
      canonicalRestWorldByBone:{upperarm_l:id(),forearm_l:id()}
    });
    assert.equal(plan.maximumMatrixResidual,0);
    const packed=packMappedWorldPalette(plan,{
      forearm_l:pose(0,.5),upperarm_l:pose(0,0)
    });
    const d=deformIndexedSkin(parsed.mesh,packed);
    assert.equal(d.triangleCount,1);
    assert.ok(Math.abs(d.positions[1]-parsed.mesh.positions[1]-.125)<1e-6);
    meshes++;
  }
  assert.equal(meshes,2);
});
test('rejects missing, duplicate or nonexplicit mesh roots',()=>{
  check(g=>{g.scenes=[]},/single explicit/);
  check(g=>{delete g.scene},/single explicit/);
  check(g=>{g.scene=1},/single explicit/);
  check(g=>{g.scenes[0].nodes.push(g.scenes[0].nodes[0])},/duplicated/);
  check(g=>{g.scenes[0].nodes=[0,1,2]},/direct root/);
  check(g=>{g.nodes[3].mesh=0},/duplicated mesh/);
  check(g=>{delete g.nodes[3].skin},/same explicit skin/);
  check(g=>{g.nodes[3].mesh=99},/unknown mesh/);
  check(g=>{delete g.nodes[3].mesh; delete g.nodes[3].skin},/every mesh/);
});
test('rejects unknown mesh hierarchy and inconsistent mesh skin',()=>{
  check(g=>{g.nodes[1].children=[3]},/hierarchy parent/);
  check(g=>{g.nodes[3].skin=1},/same explicit skin/);
  check(g=>{g.nodes[1].skin=0},/non-mesh/);
  check(g=>{g.nodes[3].scale=[2,1,1]},/nonidentity/);
  check(g=>{g.nodes[3].translation=[.5,0,0]},/nonidentity/);
  check(g=>{g.nodes[3].rotation=[0,0,1,0]},/nonidentity/);
});
test('refuses unsupported materials, textures, animation and joint/weight attributes',()=>{
  check(g=>{g.meshes[1].primitives[0].material=0},/material/);
  check(g=>{g.meshes[1].primitives[0].targets=[{}]},/morph/);
  check(g=>{g.meshes[1].primitives[0].attributes.JOINTS_1=1},/secondary/);
  check(g=>{g.meshes[1].primitives[0].mode=1},/TRIANGLES/);
  check(g=>{g.meshes[1].primitives[0].attributes.TEXCOORD_0=0},/secondary|UV/);
  check(g=>{g.images=[{uri:'https://example.invalid/image.png'}]},/texture/);
  check(g=>{g.animations=[{}]},/texture|animation/);
  check(g=>{g.extensionsUsed=['KHR_draco_mesh_compression']},/extensions/);
});
test('cannot hide invalid position accessor or skin weights in a secondary primitive',()=>{
  check(g=>{g.accessors[g.meshes[1].primitives[0].attributes.POSITION].type='VEC2'},/VEC3/);
  check(g=>{g.accessors[g.meshes[1].primitives[0].attributes.POSITION].byteOffset=10000},/escapes/);
  check(g=>{g.meshes[1].primitives[0].attributes.WEIGHTS_0=0},/VEC4/);
  check(g=>{g.meshes[1].primitives[0].attributes.JOINTS_0=0},/VEC4/);
  check(g=>{g.meshes[1].primitives[0].indices=0},/SCALAR/);
});
test('rejects too many mesh/primitive entries, not truncate and pretend valid',()=>{
  assert.throws(()=>parse(fixture({meshCount:4,primitivesPerMesh:3})),/fixture budget/);
  check(g=>g.meshes.push(...Array.from({length:3},()=>structuredClone(g.meshes[0]))),/1..4/);
  check(g=>{g.meshes[0].primitives=[]},/bounded primitives/);
  check(g=>{g.meshes[0].primitives.push(
    ...Array.from({length:8},()=>structuredClone(g.meshes[0].primitives[0]))
  )},/bounded primitives/);
  check(g=>{g.meshes[1].primitives.push(
    ...Array.from({length:7},()=>structuredClone(g.meshes[1].primitives[0]))
  )},/2..8/);
});
test('rejects malformed GLB header, extra raw bytes and untrusted source types',()=>{
  assert.throws(()=>parse(new Uint8Array(fixture())),/bounded raw/);
  const malformed=fixture();new DataView(malformed).setUint32(8,999,true);
  assert.throws(()=>parse(malformed),/header/);
  const truncated=fixture().slice(0,-4);
  assert.throws(()=>parse(truncated),/header|BIN chunk/);
});
test('source GLB remains byte-for-byte untouched by adapter and deterministic',()=>{
  const source=fixture({meshCount:2,primitivesPerMesh:2});
  const before=new Uint8Array(source).slice();
  const r1=parse(source),r2=parse(source);
  assert.deepEqual(new Uint8Array(source),before);
  assert.deepEqual(r1.batches.map(x=>x.parsed.mesh.positions),
    r2.batches.map(x=>x.parsed.mesh.positions));
});
test('reject a candidate original character on purpose: no implicit production approval',()=>{
  const r=parse(fixture());
  assert.equal(r.audit.clinicalAnatomyApproved,false);
  assert.equal(r.audit.actualOriginalHumanMeshUsed,false);
  assert.equal(r.audit.rightsAndProvenanceApproved,false);
  assert.equal(r.audit.productionRuntimeReady,false);
  assert.ok(r.batches.every(x=>x.parsed.audit.productionReady===false));
});

function fakeGpu(){
  const calls=[];
  const gl={
    VERTEX_SHADER:1,FRAGMENT_SHADER:2,COMPILE_STATUS:3,LINK_STATUS:4,
    ARRAY_BUFFER:5,ELEMENT_ARRAY_BUFFER:6,FLOAT:7,DEPTH_TEST:8,
    DYNAMIC_DRAW:9,COLOR_BUFFER_BIT:10,DEPTH_BUFFER_BIT:20,
    TRIANGLES:4,UNSIGNED_SHORT:5123,UNSIGNED_INT:5125,
    createShader:()=>({}),shaderSource:()=>{},compileShader:()=>{},
    getShaderParameter:()=>true,getShaderInfoLog:()=>'',deleteShader:()=>{},
    createProgram:()=>({}),attachShader:()=>{},linkProgram:()=>{},
    getProgramParameter:()=>true,getProgramInfoLog:()=>'',deleteProgram:()=>{},
    createVertexArray:()=>({}),createBuffer:()=>({}),bindVertexArray:()=>{},
    bindBuffer:()=>{},getUniformLocation:(_,name)=>({name}),enableVertexAttribArray:()=>{},
    vertexAttribPointer:()=>{},enable:()=>{},viewport:()=>{},
    clearColor:()=>{},clear:()=>calls.push('clear'),useProgram:()=>{},
    uniformMatrix4fv:()=>{},uniform3fv:()=>{},
    bufferData:()=>{},
    drawElements:(_,count)=>calls.push(['draw',count]),
    deleteBuffer:()=>{},deleteVertexArray:()=>{},
  };
  const listeners=new Map();
  const canvas={
    width:0,height:0,
    getContext:kind=>{assert.equal(kind,'webgl2');return gl;},
    addEventListener:(key,fn)=>listeners.set(key,fn),
    removeEventListener:key=>listeners.delete(key),
  };
  return {canvas,calls,listeners};
}
test('multi-mesh native GPU validates ALL parts before one clear and multiple indexed draws',async()=>{
  const {createNativeIndexedMeshWebGL2,deformIndexedSkin}=
    await import('../src/viewer/firstPartyIndexedSkinnedMesh.mjs');
  const gpu=fakeGpu(),renderer=createNativeIndexedMeshWebGL2(gpu.canvas);
  const source=parse(fixture());
  const posed=new Float32Array([...id(),...id()]);
  const decoded=source.batches.map(x=>deformIndexedSkin(x.parsed.mesh,posed));
  assert.equal(renderer.renderBatches(decoded,{colors:[[1,0,0],[0,1,0]]}),true);
  assert.equal(renderer.frameCount,1);
  assert.equal(renderer.drawCallCount,2);
  assert.deepEqual(gpu.calls,['clear',['draw',3],['draw',3]]);
  const draws=gpu.calls.length;
  assert.throws(()=>renderer.renderBatches([decoded[0],{...decoded[1],indices:new Uint16Array([0,1,19])}]),
    /Invalid triangle index/);
  assert.equal(gpu.calls.length,draws,'Bad second primitive must not partially draw the first');
  assert.throws(()=>renderer.renderBatches(decoded,{colors:[[1,0,0]]}),/one color/);
  assert.throws(()=>renderer.renderBatches([]),/1..8/);
  renderer.render(decoded[0]);
  assert.equal(renderer.frameCount,2);
  assert.equal(renderer.drawCallCount,3);
  renderer.dispose();
});
test('batched native GPU honors loss/recovery without third-party fallback',async()=>{
  const {createNativeIndexedMeshWebGL2,deformIndexedSkin}=
    await import('../src/viewer/firstPartyIndexedSkinnedMesh.mjs');
  const gpu=fakeGpu(),renderer=createNativeIndexedMeshWebGL2(gpu.canvas);
  const source=parse(fixture());
  const parts=source.batches.map(x=>deformIndexedSkin(x.parsed.mesh,new Float32Array([...id(),...id()])));
  renderer.setSize(400,300,1);
  let prevented=false;
  gpu.listeners.get('webglcontextlost')({preventDefault:()=>{prevented=true;}});
  assert.equal(prevented,true);
  assert.equal(renderer.renderBatches(parts),false);
  assert.equal(renderer.frameCount,0);
  gpu.listeners.get('webglcontextrestored')();
  assert.equal(renderer.renderBatches(parts),true);
  assert.equal(renderer.frameCount,1);
  renderer.dispose();
});
