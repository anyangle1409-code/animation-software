import assert from 'node:assert/strict';
import test from 'node:test';
import {
  validateNativeSkinnedMesh,deformIndexedSkin,invertRigidBind,
  makeTwoBoneSkinProbe,createNativeIndexedMeshWebGL2,NATIVE_SKINNED_KIND
} from '../src/viewer/firstPartyIndexedSkinnedMesh.mjs';

const id=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
const shift=(x,y,z)=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1]);
const near=(a,b,e=1e-5)=>assert.ok(Math.abs(a-b)<=e,'expected '+a+' ~ '+b);
function triangle(overrides={}){
  return {
    positions:new Float32Array([0,0,0,1,0,0,0,1,0]),
    indices:new Uint16Array([0,1,2]),
    jointIndices:new Uint16Array([0,0,0,0,0,0,0,0,0,0,0,0]),
    weights:new Float32Array([1,0,0,0,1,0,0,0,1,0,0,0]),
    inverseBindMatrices:id(),...overrides
  };
}
test('identity LBS exactly preserves source surface and normal',()=>{
  const m=triangle(),deformed=deformIndexedSkin(m,id());
  assert.deepEqual([...deformed.positions],[...m.positions]);
  assert.deepEqual([...deformed.indices],[...m.indices]);
  assert.equal(deformed.triangleCount,1);
  for(let i=0;i<3;i++){
    near(deformed.normals[i*3],0);near(deformed.normals[i*3+1],0);near(deformed.normals[i*3+2],1);
  }
});
test('one rigid bone moves ALL vertices and does not change triangle count',()=>{
  const posed=shift(4,5,-7),d=deformIndexedSkin(triangle(),posed);
  assert.deepEqual([...d.positions],[4,5,-7,5,5,-7,4,6,-7]);
  assert.equal(d.triangleCount,1);
});
test('inverse bind exactly cancels authored rest transform',()=>{
  const bind=shift(1,2,3);
  const mesh=triangle({inverseBindMatrices:invertRigidBind(bind)});
  const d=deformIndexedSkin(mesh,bind);
  for(let i=0;i<mesh.positions.length;i++)near(d.positions[i],mesh.positions[i]);
});
test('native LBS blends two joint translations by four explicit weights',()=>{
  const mesh=triangle({
    inverseBindMatrices:new Float32Array([...id(),...id()]),
    jointIndices:new Uint16Array([0,1,0,0,0,1,0,0,0,1,0,0]),
    weights:new Float32Array([.25,.75,0,0,.25,.75,0,0,.25,.75,0,0]),
  });
  const posed=new Float32Array([...shift(1,0,0),...shift(0,2,0)]);
  const x=deformIndexedSkin(mesh,posed).positions;
  near(x[0],.25);near(x[1],1.5);
  near(x[3],1.25);near(x[4],1.5);
  near(x[6],.25);near(x[7],2.5);
});
test('normals recomputed after actual rotated/slanted deformed triangle',()=>{
  const m=triangle();
  // Rotate 90 degrees about X: source XY plane becomes XZ
  const rot=new Float32Array([1,0,0,0,0,0,1,0,0,-1,0,0,0,0,0,1]);
  const d=deformIndexedSkin(m,rot);
  near(Math.abs(d.normals[1]),1);
  near(d.normals[0],0);near(d.normals[2],0);
});
test('triangle winding gives opposite normal orientation when flipped',()=>{
  const a=deformIndexedSkin(triangle(),id());
  const b=deformIndexedSkin(triangle({indices:new Uint16Array([0,2,1])}),id());
  near(a.normals[2],1);near(b.normals[2],-1);
});
test('invalid palette and mesh arrays fail closed',()=>{
  assert.throws(()=>validateNativeSkinnedMesh({}),/typed/);
  assert.throws(()=>validateNativeSkinnedMesh(triangle({positions:new Float32Array([1,2])})),/3D/);
  assert.throws(()=>validateNativeSkinnedMesh(triangle({indices:new Uint16Array([0,1,5])})),/Out-of-range/);
  assert.throws(()=>validateNativeSkinnedMesh(triangle({weights:new Float32Array(12)})),/sum/);
  assert.throws(()=>validateNativeSkinnedMesh(triangle({jointIndices:new Uint16Array(11)})),/four/);
  assert.throws(()=>validateNativeSkinnedMesh(triangle({jointIndices:new Uint16Array([1,...new Array(11).fill(0)])})),/Bad skin/);
  assert.throws(()=>validateNativeSkinnedMesh(triangle({positions:new Float32Array([NaN,0,0,1,0,0,0,1,0])})),/Nonfinite/);
  assert.throws(()=>deformIndexedSkin(triangle(),new Float32Array(16)),/affine/);
  assert.throws(()=>deformIndexedSkin(triangle(),new Float32Array([...id(),...id()])),/match/);
  assert.throws(()=>deformIndexedSkin(triangle({indices:new Uint16Array([0,0,0])}),id()),/degenerate/);
});
test('bad homogeneous and nonfinite rotations are rejected',()=>{
  assert.throws(()=>invertRigidBind(new Float32Array(16)),/affine/);
  assert.throws(()=>invertRigidBind(new Float32Array([2,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])),/orthonormal/);
  assert.throws(()=>invertRigidBind(new Float32Array([Infinity,...id().slice(1)])),/Nonfinite/);
  // Each row has unit length but two are nonorthogonal: an invalid rigid bind.
  const shear=new Float32Array([
    1,0.5,0,0,
    0,Math.sqrt(0.75),0,0,
    0,0,1,0,
    0,0,0,1
  ]);
  assert.throws(()=>invertRigidBind(shear),/shear|nonorthogonal/);
  const reflected=new Float32Array([-1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
  assert.throws(()=>invertRigidBind(reflected),/right-handed/);
});
test('rigid inverse correct for 90-degree joint rotation about Z',()=>{
  const r=new Float32Array([0,1,0,0,-1,0,0,0,0,0,1,0,2,3,4,1]);
  const mesh=triangle({inverseBindMatrices:invertRigidBind(r)});
  const d=deformIndexedSkin(mesh,r);
  mesh.positions.forEach((value,i)=>near(d.positions[i],value));
});
test('continuous synthetic two-bone reference proxy is indexed, skin-validated',()=>{
  const m=makeTwoBoneSkinProbe([0,1.5,0],[0,1.0,0],[0,.55,.4]);
  const info=validateNativeSkinnedMesh({...m,inverseBindMatrices:new Float32Array([...id(),...id()])});
  assert.equal(info.bones,2);
  assert.equal(info.vertices,70);
  assert.equal(info.triangles,120+16);
  assert.ok(m.weights.some(x=>x>.3 && x<.7),'The elbow MUST have smoothly blended weights');
  assert.ok(m.weights.some(x=>x===1));
  const d=deformIndexedSkin({...m,inverseBindMatrices:new Float32Array([...id(),...id()])},
    new Float32Array([...id(),...shift(.14,-.10,.12)]));
  assert.ok(d.positions.some((value,i)=>Math.abs(value-m.positions[i])>.01));
  assert.ok(d.triangleCount>0);
});
test('synthetic source joints and degenerate polyline fail closed',()=>{
  assert.throws(()=>makeTwoBoneSkinProbe([0,0,0],[0,0,0],[1,0,0]),/Degenerate/);
  assert.throws(()=>makeTwoBoneSkinProbe([0,0,0],[1,0,0],[1,0,0]),/Degenerate/);
  assert.throws(()=>makeTwoBoneSkinProbe([0,0,0],[1,0,0],[2,0,0],{radius:-1}),/Invalid/);
});

function fakeGL(shaderOk=true) {
  const calls=[];
  const gl={
    VERTEX_SHADER:1,FRAGMENT_SHADER:2,COMPILE_STATUS:3,LINK_STATUS:4,
    ARRAY_BUFFER:5,ELEMENT_ARRAY_BUFFER:6,FLOAT:7,DEPTH_TEST:8,
    DYNAMIC_DRAW:9,COLOR_BUFFER_BIT:10,DEPTH_BUFFER_BIT:20,
    TRIANGLES:4,UNSIGNED_SHORT:5123,UNSIGNED_INT:5125,
    createShader:()=>({}),shaderSource:()=>{},compileShader:()=>{},
    getShaderParameter:()=>shaderOk,getShaderInfoLog:()=>'bad shader',
    deleteShader:()=>{},createProgram:()=>({}),attachShader:()=>{},linkProgram:()=>{},
    getProgramParameter:()=>true,getProgramInfoLog:()=>'',deleteProgram:()=>calls.push('program'),
    createVertexArray:()=>({}),createBuffer:()=>({}),bindVertexArray:()=>{},bindBuffer:()=>{},
    getUniformLocation:(_,name)=>({name}),enableVertexAttribArray:()=>{},
    vertexAttribPointer:()=>{},enable:()=>{},viewport:()=>{},
    clearColor:()=>{},clear:()=>{},useProgram:()=>{},
    uniformMatrix4fv:(_,transpose,p)=>{assert.equal(transpose,false);assert.equal(p.length,16);},
    uniform3fv:()=>{},bufferData:(_,source)=>{assert.ok(source.length>=3);},
    drawElements:(mode,count,type,offset)=>calls.push(['draw',mode,count,type,offset]),
    deleteBuffer:()=>calls.push('buffer'),deleteVertexArray:()=>calls.push('vao')
  };
  const events=new Map();
  const canvas={
    width:0,height:0,
    getContext:kind=>{assert.equal(kind,'webgl2');return gl;},
    addEventListener:(name,cb)=>events.set(name,cb),
    removeEventListener:name=>events.delete(name)
  };
  return {gl,canvas,events,calls};
}
test('actual indexed-triangle GPU uses drawElements, not old skeleton lines',()=>{
  const {canvas,events,calls}=fakeGL();
  const renderer=createNativeIndexedMeshWebGL2(canvas);
  renderer.setSize(640,480,2);
  assert.equal(renderer.kind,NATIVE_SKINNED_KIND);
  assert.equal(canvas.width,1280);assert.equal(canvas.height,960);
  const m=deformIndexedSkin(triangle(),id());
  assert.equal(renderer.render(m),true);
  assert.deepEqual(calls.find(c=>Array.isArray(c)),['draw',4,3,5123,0]);
  assert.equal(renderer.frameCount,1);
  renderer.dispose();renderer.dispose();
  assert.equal(events.size,0);
  assert.ok(calls.filter(c=>c==='buffer').length===3);
  assert.ok(calls.includes('vao')&&calls.includes('program'));
});
test('32-bit triangle vertex indices supported for future large body meshes',()=>{
  const {canvas,calls}=fakeGL();
  const r=createNativeIndexedMeshWebGL2(canvas);
  const m=deformIndexedSkin(triangle(),id());
  r.render({...m,indices:new Uint32Array([0,1,2])});
  assert.deepEqual(calls.find(c=>Array.isArray(c)),['draw',4,3,5125,0]);
  r.dispose();
});
test('invalid first-party triangle inputs fail before draw',()=>{
  const {canvas,calls}=fakeGL();const r=createNativeIndexedMeshWebGL2(canvas);
  assert.throws(()=>r.render({positions:new Float32Array(3)}),/Malformed/);
  assert.throws(()=>r.render({positions:new Float32Array(9),normals:new Float32Array(9),
    indices:new Uint16Array([0,1,8])}),/Invalid triangle/);
  assert.throws(()=>r.render({...deformIndexedSkin(triangle(),id()),normals:new Float32Array([NaN,...new Array(8).fill(0)])}),/Nonfinite/);
  assert.equal(r.frameCount,0);assert.equal(calls.filter(c=>Array.isArray(c)).length,0);r.dispose();
});
test('native triangle GPU survives simulated WebGL context loss/restore',()=>{
  const {canvas,events}=fakeGL();const r=createNativeIndexedMeshWebGL2(canvas);
  r.setSize(60,40,1);
  let prevented=false;
  events.get('webglcontextlost')({preventDefault:()=>prevented=true});
  assert.ok(prevented);assert.ok(r.contextLost);
  assert.equal(r.render(deformIndexedSkin(triangle(),id())),false);
  events.get('webglcontextrestored')();
  assert.equal(r.render(deformIndexedSkin(triangle(),id())),true);
  r.dispose();
});
test('missing WebGL2 or shader failure does not fall back to third-party engine',()=>{
  assert.throws(()=>createNativeIndexedMeshWebGL2({getContext:()=>null}),/WebGL2 unavailable/);
  assert.throws(()=>createNativeIndexedMeshWebGL2(fakeGL(false).canvas),/shader compile/);
});
