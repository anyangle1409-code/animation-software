import assert from 'node:assert/strict';
import test from 'node:test';
import {buildSyntheticSourceNormalGLB as fixture} from './support/buildSyntheticSourceNormalGlb.mjs';
import {parseRestrictedBatchedSkinnedGlb} from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
import {referenceSkinOriginalUnitNormals,validateNativeSourceNormals}
  from '../src/viewer/firstPartySkinnedNormalReference.mjs';
import {createNativePaletteSkinnedWebGL2}
  from '../src/viewer/firstPartyGpuPaletteSkinning.mjs';
const id=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
const rotX=r=>{
  const c=Math.cos(r),s=Math.sin(r);
  return new Float32Array([1,0,0,0,0,c,s,0,0,-s,c,0,0,0,0,1]);
};
const almost=(x,y,tol=1e-5)=>
  assert.ok(Math.abs(x-y)<tol,'normal parity: '+x+' != '+y);
const source=()=>parseRestrictedBatchedSkinnedGlb(fixture(),{
  allowSourceNormals:true,allowSourceUV0:true}).batches;
test('G2c reference preserves original nonidentical GLB NORMAL at neutral bind',()=>{
  for(const part of source()){
    const {mesh}=part.parsed;
    const n=referenceSkinOriginalUnitNormals(mesh,part.sourceNormals,
      new Float32Array([...id(),...id()]));
    assert.deepEqual([...n],[...part.sourceNormals]);
    assert.equal(validateNativeSourceNormals(mesh,part.sourceNormals).vertices,3);
  }
});
test('G2c exact 90° rotation of all influences moves +Y source normal to +Z',()=>{
  const part=source()[1],m=part.parsed.mesh;
  const n=referenceSkinOriginalUnitNormals(m,part.sourceNormals,
    new Float32Array([...rotX(Math.PI/2),...rotX(Math.PI/2)]));
  for(let i=0;i<n.length;i+=3){
    almost(n[i],0);almost(n[i+1],0);almost(n[i+2],1);
  }
});
test('G2c equal weighted opposing 90° rotations correctly refuse singular normal blend',()=>{
  const part=source()[1];
  // The synthetic source has 75/25 per vertex; use two-bone .5/.5 to
  // produce complete cancellation, which shader normalization cannot
  // meaningfully handle without corrective skin policy.
  const m={...part.parsed.mesh,weights:new Float32Array([...Array(3)].flatMap(
    ()=>[.5,.5,0,0]))};
  assert.throws(()=>referenceSkinOriginalUnitNormals(m,part.sourceNormals,
    new Float32Array([...rotX(Math.PI/2),...rotX(-Math.PI/2)])),
    /Weighted source normal cancels/);
});
test('G2c weighted rigid rotations are combined before normalizing, not after',()=>{
  const part=source()[1];
  const out=referenceSkinOriginalUnitNormals(part.parsed.mesh,part.sourceNormals,
    new Float32Array([...id(),...rotX(Math.PI/2)]));
  const n=.75/Math.hypot(.75,.25),z=.25/Math.hypot(.75,.25);
  for(let i=0;i<out.length;i+=3){
    almost(out[i],0);almost(out[i+1],n);almost(out[i+2],z);
    almost(Math.hypot(...out.slice(i,i+3)),1);
  }
});
test('G2c refuses invalid, NaN, zero, scaled, incomplete or non-typed source normals',()=>{
  const part=source()[0],m=part.parsed.mesh,pose=new Float32Array([...id(),...id()]);
  assert.throws(()=>referenceSkinOriginalUnitNormals(m,new Float32Array(2),pose),/one typed XYZ/);
  assert.throws(()=>referenceSkinOriginalUnitNormals(m,new Float64Array(part.sourceNormals),pose),/one typed XYZ/);
  for(const value of [0,NaN,Infinity,1.6]){
    const n=part.sourceNormals.slice();
    n[0]=value;n[1]=0;n[2]=0;
    assert.throws(()=>referenceSkinOriginalUnitNormals(m,n,pose),/finite and near unit/);
  }
});
test('G2c source 128-bone distant indices directional normal CPU reference supported',()=>{
  const bind=new Float32Array(128*16),world=new Float32Array(128*16);
  for(let i=0;i<128;i++){bind.set(id(),i*16);world.set(id(),i*16);}
  world.set(rotX(Math.PI/2),127*16);
  const m={
    positions:new Float32Array([0,0,0,1,0,0,0,1,0]),
    indices:new Uint16Array([0,1,2]),
    jointIndices:new Uint16Array([...Array(3)].flatMap(()=>[0,31,64,127])),
    weights:new Float32Array([...Array(3)].flatMap(()=>[.1,.2,.3,.4])),
    inverseBindMatrices:bind
  };
  const originals=new Float32Array([0,1,0,0,1,0,0,1,0]);
  const norms=referenceSkinOriginalUnitNormals(m,originals,world);
  for(let i=0;i<norms.length;i+=3){
    almost(norms[i],0);
    almost(norms[i+1],.6/Math.hypot(.6,.4));
    almost(norms[i+2],.4/Math.hypot(.6,.4));
  }
});
function mockGL(){
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
    getShaderParameter:()=>true,getShaderInfoLog:()=>'',
    deleteShader:()=>{},createProgram:()=>({}),attachShader:()=>{},
    transformFeedbackVaryings:(_,v)=>assert.deepEqual(v,['vSkinnedWorld','vSkinnedNormal']),
    linkProgram:()=>{},getProgramParameter:()=>true,getProgramInfoLog:()=>'',
    deleteProgram:()=>{},createVertexArray:()=>({}),
    createBuffer:()=>({}),createTexture:()=>({}),bindVertexArray:()=>{},
    bindBuffer:()=>{},bindBufferBase:()=>{},getUniformLocation:()=>({}),
    enableVertexAttribArray:()=>{},vertexAttribIPointer:()=>{},
    vertexAttribPointer:()=>{},activeTexture:()=>{},bindTexture:()=>{},
    texParameteri:()=>{},enable:()=>{},disable:()=>{},viewport:()=>{},
    clearColor:()=>{},clear:()=>calls.push('clear'),useProgram:()=>{},
    uniformMatrix4fv:()=>{},uniform1i:(_,v)=>calls.push(['mode',v]),
    texImage2D:()=>{},getParameter:k=>k===62?4096:0,
    bufferData:()=>{},drawElements:()=>calls.push('draw'),
    drawArrays:()=>{},beginTransformFeedback:()=>{},endTransformFeedback:()=>{},
    getBufferSubData:(_,a,b)=>b.fill(0),getError:()=>0,NO_ERROR:0,
    deleteBuffer:()=>{},deleteVertexArray:()=>{},deleteTexture:()=>{}
  };
  return {canvas:{
    getContext:k=>k==='webgl2'?gl:null,
    addEventListener:(k,fn)=>listeners.set(k,fn),
    removeEventListener:k=>listeners.delete(k)
  },calls,listeners};
}
test('G2c native GPU normal-preview mode requires valid source NORMAL for every part',()=>{
  const f=mockGL(),gpu=createNativePaletteSkinnedWebGL2(f.canvas);
  const parts=source().map(b=>({mesh:b.parsed.mesh,uv0:b.sourceUV0,
    posedWorld:new Float32Array([...id(),...id()]),sourceNormals:b.sourceNormals}));
  assert.equal(gpu.renderBatches(parts,{normalPreview:true}),true);
  assert.equal(f.calls.filter(x=>x==='clear').length,1);
  assert.equal(f.calls.filter(x=>x==='draw').length,2);
  assert.ok(f.calls.some(x=>Array.isArray(x)&&x[0]==='mode'&&x[1]===1));
  const calls=f.calls.length;
  assert.throws(()=>gpu.renderBatches([parts[0],{...parts[1],sourceNormals:undefined}],
    {normalPreview:true}),/requires explicit original source NORMAL/);
  assert.equal(f.calls.length,calls,'Invalid last source normal must not clear or draw first mesh');
  assert.throws(()=>gpu.renderBatches(parts,{normalPreview:'yes'}),/boolean/);
  const wrong=parts[1].sourceNormals.slice();wrong[1]=4;
  assert.throws(()=>gpu.renderBatches([parts[0],{...parts[1],sourceNormals:wrong}],
    {normalPreview:true}),/finite and near unit/);
  gpu.dispose();
});
