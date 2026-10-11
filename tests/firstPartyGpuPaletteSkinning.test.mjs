import assert from 'node:assert/strict';
import test from 'node:test';
import {buildNativeJointSkinPalette,createNativePaletteSkinnedWebGL2,
  HGPT_NATIVE_GPU_SKIN_KIND} from '../src/viewer/firstPartyGpuPaletteSkinning.mjs';
import {buildSyntheticUV0Glb} from './support/buildSyntheticUV0Glb.mjs';
import {parseRestrictedBatchedSkinnedGlb} from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
import {deformIndexedSkin} from '../src/viewer/firstPartyIndexedSkinnedMesh.mjs';
const id=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
const translation=(x,y,z)=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1]);
const approx=(a,b)=>assert.ok(Math.abs(a-b)<1e-5,a+' expected '+b);
const mesh=()=>parseRestrictedBatchedSkinnedGlb(
  buildSyntheticUV0Glb(),{allowSourceUV0:true}).batches[0];
test('correct four-texel column-major GPU skin palette is identity at source bind rest',()=>{
  const first=mesh().parsed.mesh;
  const p=buildNativeJointSkinPalette(first,new Float32Array([...id(),...id()]));
  assert.deepEqual([...p],[...id(),...id()]);
  assert.equal(p.length,32);
});
test('GPU bone palette is source-ordered worldPose times source inverse bind matrix',()=>{
  const first=mesh().parsed.mesh;
  const p=buildNativeJointSkinPalette(first,new Float32Array([
    ...translation(1,2,3),...translation(4,5,6)]));
  assert.deepEqual([...p.slice(12,15)],[1,2,3]);
  assert.deepEqual([...p.slice(28,31)],[4,5,6]);
});
test('rest inverse bind cancels authored source rest translation',()=>{
  const first=mesh().parsed.mesh;
  first.inverseBindMatrices.set(translation(-1,-2,-3),0);
  first.inverseBindMatrices.set(translation(-4,-5,-6),16);
  const p=buildNativeJointSkinPalette(first,new Float32Array([
    ...translation(1,2,3),...translation(4,5,6)]));
  for(let i=0;i<p.length;i++)approx(p[i],new Float32Array([...id(),...id()])[i]);
});
test('reject incomplete joint palette and nonfinite transforms',()=>{
  const first=mesh().parsed.mesh;
  assert.throws(()=>buildNativeJointSkinPalette(first,id()),/complete/);
  assert.throws(()=>buildNativeJointSkinPalette(first,new Float64Array([...id(),...id()])),/Float32Array/);
  const bad=new Float32Array([...id(),...id()]);bad[12]=NaN;
  assert.throws(()=>buildNativeJointSkinPalette(first,bad),/nonfinite/);
  bad[12]=0;bad[3]=1;
  assert.throws(()=>buildNativeJointSkinPalette(first,bad),/affine/);
});
test('reject pose scale, shear and improper mirrored source frame',()=>{
  const first=mesh().parsed.mesh;
  let poses=new Float32Array([...id(),...id()]);
  poses[0]=2;
  assert.throws(()=>buildNativeJointSkinPalette(first,poses),/scaling/);
  poses=new Float32Array([...id(),...id()]);
  poses[4]=.25;poses[5]=Math.sqrt(1-.25*.25);
  assert.throws(()=>buildNativeJointSkinPalette(first,poses),/shear/);
  poses=new Float32Array([...id(),...id()]);
  poses[0]=-1;
  assert.throws(()=>buildNativeJointSkinPalette(first,poses),/reflection/);
});
test('typed GPU palette refuses malformed mesh/weights/indices',()=>{
  const first=mesh().parsed.mesh;
  first.weights[0]=2;
  assert.throws(()=>buildNativeJointSkinPalette(first,new Float32Array([...id(),...id()])),
    /Bad skin index\/weight/);
});
test('GPU palette shares actual original CPU LBS rest pose, not human model approval',()=>{
  const source=mesh().parsed.mesh;
  const poses=new Float32Array([...translation(0,0,0),...translation(0,.5,0)]);
  const palette=buildNativeJointSkinPalette(source,poses);
  const cpu=deformIndexedSkin(source,poses);
  approx(cpu.positions[1],palette[13]*source.weights[0]+
    palette[29]*source.weights[1]);
  assert.equal(cpu.triangleCount,1);
});
function fakeGPU(shaderCompiles=true){
  const calls=[],listeners=new Map();
  const gl={
    VERTEX_SHADER:1,FRAGMENT_SHADER:2,COMPILE_STATUS:3,LINK_STATUS:4,
    ARRAY_BUFFER:5,ELEMENT_ARRAY_BUFFER:6,FLOAT:7,UNSIGNED_SHORT:5123,
    UNSIGNED_INT:5125,DEPTH_TEST:8,DYNAMIC_DRAW:9,
    COLOR_BUFFER_BIT:10,DEPTH_BUFFER_BIT:20,TRIANGLES:4,
    SEPARATE_ATTRIBS:51,TEXTURE0:52,TEXTURE_2D:53,
    TEXTURE_MIN_FILTER:54,TEXTURE_MAG_FILTER:55,NEAREST:56,
    TEXTURE_WRAP_S:57,TEXTURE_WRAP_T:58,CLAMP_TO_EDGE:59,
    RGBA32F:60,RGBA:61,MAX_TEXTURE_SIZE:62,
    TRANSFORM_FEEDBACK_BUFFER:63,STREAM_READ:64,RASTERIZER_DISCARD:65,
    createShader:()=>({}),shaderSource:()=>{},compileShader:()=>{},
    getShaderParameter:()=>shaderCompiles,getShaderInfoLog:()=>'bad compilation',
    deleteShader:()=>{},createProgram:()=>({}),attachShader:()=>{},
    transformFeedbackVaryings:(_,values)=>assert.deepEqual(values,['vSkinnedWorld']),
    linkProgram:()=>{},getProgramParameter:()=>true,getProgramInfoLog:()=>'',
    deleteProgram:()=>calls.push('freeProgram'),
    createVertexArray:()=>({}),createBuffer:()=>({}),createTexture:()=>({}),
    bindVertexArray:()=>{},bindBuffer:()=>{},bindBufferBase:()=>{},
    getUniformLocation:()=>({}),enableVertexAttribArray:()=>{},vertexAttribIPointer:()=>{},
    vertexAttribPointer:()=>{},activeTexture:()=>{},bindTexture:()=>{},
    texParameteri:()=>{},enable:()=>{},disable:()=>{},viewport:()=>{},
    clearColor:()=>{},clear:()=>calls.push('clear'),useProgram:()=>{},
    uniformMatrix4fv:()=>{},uniform1i:()=>{},
    texImage2D:(target,level,internal,w,h,border,format,type,pal)=>{
      calls.push(['paletteTex',w,h,pal.length]);
    },
    getParameter:k=>k===62?4096:0,
    bufferData:()=>{},drawElements:(_,n)=>calls.push(['draw',n]),
    beginTransformFeedback:()=>{},endTransformFeedback:()=>{},
    getBufferSubData:(_,off,a)=>a.fill(0),
    deleteBuffer:()=>calls.push('freeBuffer'),
    deleteVertexArray:()=>calls.push('freeVAO'),deleteTexture:()=>calls.push('freeTexture'),
  };
  const canvas={
    getContext:k=>{assert.equal(k,'webgl2');return gl;},
    addEventListener:(k,f)=>listeners.set(k,f),
    removeEventListener:k=>listeners.delete(k),
  };
  return {canvas,calls,listeners};
}
test('GPU draws two independently mapped source GLB mesh parts in a single depth pass',()=>{
  const f=fakeGPU(),gpu=createNativePaletteSkinnedWebGL2(f.canvas);
  gpu.setSize(640,480,1);
  const r=parseRestrictedBatchedSkinnedGlb(buildSyntheticUV0Glb(),{allowSourceUV0:true});
  const parts=r.batches.map(b=>({
    mesh:b.parsed.mesh,uv0:b.sourceUV0,
    posedWorld:new Float32Array([...id(),...translation(0,.5,0)]),
  }));
  assert.equal(gpu.kind,HGPT_NATIVE_GPU_SKIN_KIND);
  assert.equal(gpu.renderBatches(parts),true);
  assert.equal(gpu.frameCount,1);assert.equal(gpu.drawCallCount,2);
  assert.equal(f.calls.filter(x=>x==='clear').length,1);
  assert.equal(f.calls.filter(x=>Array.isArray(x)&&x[0]==='draw').length,2);
  assert.deepEqual(f.calls.filter(x=>Array.isArray(x)&&x[0]==='paletteTex'),
    [['paletteTex',8,1,32],['paletteTex',8,1,32]]);
  const old=f.calls.length;
  assert.throws(()=>gpu.renderBatches([parts[0],{...parts[1],uv0:new Float32Array(2)}]),
    /UV0 vertex count/);
  assert.equal(f.calls.length,old,'A bad final part must not partially draw valid earlier geometry');
  gpu.dispose();assert.ok(f.calls.includes('freeTexture'));
  assert.equal(f.listeners.size,0);
});
test('GPU palette context loss/restore never falls back to third-party renderer',()=>{
  const f=fakeGPU(),gpu=createNativePaletteSkinnedWebGL2(f.canvas);
  let prevented=false;
  f.listeners.get('webglcontextlost')({preventDefault:()=>{prevented=true;}});
  assert.ok(prevented);
  assert.equal(gpu.renderBatches([]),false);
  f.listeners.get('webglcontextrestored')();
  assert.throws(()=>gpu.renderBatches([]),/1..8/);
  gpu.dispose();
});
test('GPU palette rejects invalid batch size and shader/GPU capability',()=>{
  assert.throws(()=>createNativePaletteSkinnedWebGL2({getContext:()=>null}),/WebGL2/);
  assert.throws(()=>createNativePaletteSkinnedWebGL2(fakeGPU(false).canvas),/shader compile/);
  const f=fakeGPU(),g=createNativePaletteSkinnedWebGL2(f.canvas);
  assert.throws(()=>g.renderBatches([]),/1..8/);
  g.dispose();
});
test('four-contributor native GPU palette remains 4-joint unlike two-joint tube special casing',()=>{
  const mesh4={
    positions:new Float32Array([0,0,0,1,0,0,0,1,0]),
    indices:new Uint16Array([0,1,2]),
    jointIndices:new Uint16Array([...Array(3)].flatMap(()=>[0,1,2,3])),
    weights:new Float32Array([...Array(3)].flatMap(()=>[.1,.2,.3,.4])),
    inverseBindMatrices:new Float32Array([...id(),...id(),...id(),...id()])
  };
  const poses=new Float32Array([
    ...translation(1,0,0),...translation(0,2,0),
    ...translation(0,0,3),...translation(-4,0,0)
  ]);
  const gpu=buildNativeJointSkinPalette(mesh4,poses);
  assert.equal(gpu.length,64);
  const cpu=deformIndexedSkin(mesh4,poses);
  approx(cpu.positions[0],.1-1.6);
  approx(cpu.positions[1],.4);
  approx(cpu.positions[2],.9);
});
