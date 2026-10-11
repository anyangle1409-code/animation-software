import assert from 'node:assert/strict';
import test from 'node:test';
import {buildSyntheticUV0Glb as fixture} from './support/buildSyntheticUV0Glb.mjs';
import {parseRestrictedBatchedSkinnedGlb as parse}
  from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
import {readRestrictedGlbUV0,HGPT_UV0_KIND}
  from '../src/viewer/firstPartyGlbUV0.mjs';
import {createNativeUV0WebGL2,HGPT_UV0_GPU_KIND}
  from '../src/viewer/firstPartyUV0WebGL2.mjs';
import {deformIndexedSkin} from '../src/viewer/firstPartyIndexedSkinnedMesh.mjs';
const opts={allowSourceUV0:true};
const read=bytes=>parse(bytes,opts);
const fail=(mutate,matcher=/UV0 rejection|GLB rejection/)=>
  assert.throws(()=>read(fixture({mutate})),matcher);
const almost=(x,y)=>assert.ok(Math.abs(x-y)<.00001,x+' should be '+y);
const identity=new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);

test('default old strict loader still refuses unapproved TEXCOORD_0 attribute',()=>{
  assert.throws(()=>parse(fixture()),/secondary influences|UV/);
});
test('opt-in UV0 extracts distinct original two-mesh Float32 VEC2 UV arrays in order',()=>{
  const batch=read(fixture());
  assert.equal(batch.audit.sourceUV0CoordinatesValidated,true);
  assert.equal(batch.audit.textureSamplingImplemented,false);
  assert.equal(batch.batches.length,2);
  for(const b of batch.batches){
    assert.ok(b.sourceUV0 instanceof Float32Array);
    assert.equal(b.sourceUV0.length,b.parsed.mesh.positions.length/3*2);
  }
  almost(batch.batches[0].sourceUV0[0],.895);
  almost(batch.batches[0].sourceUV0[1],.055);
  almost(batch.batches[1].sourceUV0[0],.055);
  almost(batch.batches[1].sourceUV0[1],.895);
  assert.equal(batch.audit.actualOriginalHumanMeshUsed,false);
});
test('source UV0 survives four primitives, independent source typed meshes and explicit flat source materials',()=>{
  const r=read(fixture({meshCount:2,primitivesPerMesh:2}));
  assert.equal(r.batches.length,4);
  assert.deepEqual(r.batches.map(b=>[b.meshIndex,b.primitiveIndex]),
    [[0,0],[0,1],[1,0],[1,1]]);
  const colors=parse(fixture({addSourceColors:true}),
    {allowSourceUV0:true,allowSourceFlatColors:true});
  assert.deepEqual(colors.batches.map(b=>b.materialColor),
    [[.94,.25,.2],[.15,.84,.29]]);
  assert.equal(colors.audit.textureSamplingImplemented,false);
});
test('source UV0 accepts glTF normalized UNSIGNED_BYTE and SHORT TEXCOORD_0',()=>{
  for(const c of [5121,5123]){
    const r=read(fixture({componentType:c}));
    assert.equal(r.batches.length,2);
    const precision=c===5121?1/255:1/65535;
    assert.ok(Math.abs(r.batches[0].sourceUV0[0]-.895)<precision);
    assert.ok(Math.abs(r.batches[1].sourceUV0[1]-.895)<precision);
    assert.ok(r.batches.every(b=>b.sourceUV0.every(Number.isFinite)));
  }
});
test('interleaved/tightly-strided aligned bufferView accepted with legal width',()=>{
  const r=read(fixture({mutate:g=>{
    for(const mesh of g.meshes)for(const p of mesh.primitives){
      const a=g.accessors[p.attributes.TEXCOORD_0];
      g.bufferViews[a.bufferView].byteStride=8;
    }
  }}));
  assert.equal(r.audit.sourceUV0CoordinatesValidated,true);
});
test('reject missing UV on just one mesh; no silent non-UV primitive fallback',()=>{
  fail(g=>{delete g.meshes[1].primitives[0].attributes.TEXCOORD_0},/missing valid/);
});
test('refuse mismatched or unexpected texcoord type, component or sparse metadata',()=>{
  fail(g=>{g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].type='VEC3'},/VEC2/);
  fail(g=>{g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].count=2},/count mismatch/);
  fail(g=>{g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].componentType=5125},/FLOAT/);
  fail(g=>{g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].sparse={count:1}},/sparse/);
  fail(g=>{g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].extras={url:'https://x.invalid'}},/metadata/);
});
test('normalized int UV0 must explicitly declare normalized true',()=>{
  fail(g=>{g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].normalized=false;
    g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].componentType=5123;
  },/normalized/);
});
test('float UV0 cannot declare normalized, unsigned 16-bit rejects source corruption',()=>{
  fail(g=>{g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].normalized=true},/must not be normalized/);
  fail(g=>{g.bufferViews[g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].bufferView].byteStride=4},/byteStride/);
});
test('refuse UV0 binary pointer escaping memory, declared size or alignment',()=>{
  fail(g=>{g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].byteOffset=10000},/escapes/);
  fail(g=>{g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].byteOffset=2},/alignment/);
  fail(g=>{g.bufferViews[g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].bufferView].byteLength=200000},/exceeds/);
  fail(g=>{g.bufferViews[g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0].bufferView].buffer=1},/embedded/);
});
test('reject nonfinite/extremely tiled source Float32 UV without clipping into trusted model',()=>{
  fail((g,bin)=>{
    const a=g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0];
    const bv=g.bufferViews[a.bufferView];
    new DataView(bin.buffer).setFloat32(bv.byteOffset,NaN,true);
  },/nonfinite/);
  fail((g,bin)=>{
    const a=g.accessors[g.meshes[1].primitives[0].attributes.TEXCOORD_0];
    const bv=g.bufferViews[a.bufferView];
    new DataView(bin.buffer).setFloat32(bv.byteOffset,1025,true);
  },/extreme tiled/);
});
test('UV0 flag may not smuggle in external textures, extensions or unsupported UV sets',()=>{
  fail(g=>{g.images=[{uri:'https://example.invalid/skin.png'}]},/texture/);
  fail(g=>{g.textures=[{source:0}]},/texture/);
  fail(g=>{g.extensionsUsed=['KHR_texture_transform']},/extensions/);
  fail(g=>{g.meshes[1].primitives[0].attributes.TEXCOORD_1=1},/secondary influences|UV/);
  fail(g=>{g.meshes[1].primitives[0].attributes.JOINTS_1=1},/secondary influences|UV/);
});
test('readRestrictedGlbUV0 fails closed on unauthorized source record types',()=>{
  assert.throws(()=>readRestrictedGlbUV0({},new Uint8Array(0),0,3),/metadata/);
  assert.throws(()=>readRestrictedGlbUV0(null,new Uint8Array(0),0,3),/trusted/);
  assert.equal(HGPT_UV0_KIND,'hgpt-g1c-strict-glb-uv0-v1');
});
test('UV0 source bytes are unchanged, identity LBS does not alter source UV arrays',()=>{
  const file=fixture();const before=new Uint8Array(file).slice();
  const r=read(file);
  const b=r.batches[0];
  const uv=b.sourceUV0.slice();
  const result=deformIndexedSkin(b.parsed.mesh,
    new Float32Array([...identity,...identity]));
  assert.equal(result.triangleCount,1);
  assert.deepEqual(b.sourceUV0,uv);
  assert.deepEqual(new Uint8Array(file),before);
});
function gpu(){
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
    bindBuffer:()=>{},getUniformLocation:()=>({}),enableVertexAttribArray:()=>{},
    vertexAttribPointer:()=>{},enable:()=>{},viewport:()=>{},
    clearColor:()=>{},clear:()=>calls.push('clear'),useProgram:()=>{},
    uniformMatrix4fv:(_,t,m)=>{assert.equal(t,false);assert.equal(m.length,16);},
    bufferData:()=>{},drawElements:(_,n)=>calls.push(['draw',n]),
    deleteBuffer:()=>calls.push('free'),deleteVertexArray:()=>calls.push('vao')
  };
  const listeners=new Map();
  const canvas={getContext:k=>k==='webgl2'?gl:null,
    addEventListener:(k,fn)=>listeners.set(k,fn),
    removeEventListener:k=>listeners.delete(k)};
  return {canvas,gl,calls,listeners};
}
test('native UV0 GPU draws two source UV0 meshes, one depth-frame clear, 2 indexed draw calls',()=>{
  const f=gpu(),r=createNativeUV0WebGL2(f.canvas);
  r.setSize(640,480,1);
  const p=read(fixture()).batches.map(b=>({
    ...deformIndexedSkin(b.parsed.mesh,new Float32Array([...identity,...identity])),
    uv0:b.sourceUV0
  }));
  assert.equal(r.kind,HGPT_UV0_GPU_KIND);
  assert.equal(r.renderBatches(p),true);
  assert.deepEqual(f.calls,['clear',['draw',3],['draw',3]]);
  assert.equal(r.frameCount,1);assert.equal(r.drawCallCount,2);
  assert.throws(()=>r.renderBatches([p[0],{...p[1],uv0:new Float32Array(2)}]),/TEXCOORD_0/);
  assert.deepEqual(f.calls,['clear',['draw',3],['draw',3]],'Bad second part must not draw a first');
  r.dispose();assert.ok(f.calls.includes('vao'));
});
test('native UV0 GPU context loss and recovery rebuilds own shaders without Three fallback',()=>{
  const f=gpu(),r=createNativeUV0WebGL2(f.canvas);
  let prevented=false;
  f.listeners.get('webglcontextlost')({preventDefault:()=>{prevented=true;}});
  assert.ok(prevented);
  assert.equal(r.renderBatches([]),false);
  f.listeners.get('webglcontextrestored')();
  assert.throws(()=>r.renderBatches([]),/1..8/);
  r.dispose();assert.equal(f.listeners.size,0);
});
test('native UV0 GPU must refuse missing WebGL2 rather than loading vendor',()=>{
  assert.throws(()=>createNativeUV0WebGL2({getContext:()=>null}),/WebGL2/);
});
