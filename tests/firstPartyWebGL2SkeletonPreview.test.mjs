import assert from 'node:assert/strict';
import test from 'node:test';
import {
  NATIVE_RENDERER_KIND, nativeLookAt, nativePerspective, multiplyNativeMat4,
  clipPoint, packBoneSegments, createFirstPartyWebGL2BoneRenderer,
} from '../src/viewer/firstPartyWebGL2SkeletonPreview.mjs';

const close=(actual,expected,epsilon=1e-5)=>{
  assert.ok(Math.abs(actual-expected)<=epsilon,'expected '+actual+' ~ '+expected);
};

test('native 4x4 left-multiplication has column-major identity semantics',()=>{
  const id=new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
  const view=nativeLookAt([0,0,4],[0,0,0]);
  multiplyNativeMat4(id,view).forEach((value,i)=>close(value,view[i]));
  multiplyNativeMat4(view,id).forEach((value,i)=>close(value,view[i]));
  clipPoint(view,[0,0,0]).forEach((value,i)=>close(value,[0,0,-4,1][i]));
});
test('native perspective maps near/far planes to WebGL negative/positive clip depth',()=>{
  const p=nativePerspective(Math.PI/2,1,1,11);
  const near=clipPoint(p,[0,0,-1]),far=clipPoint(p,[0,0,-11]);
  close(near[2]/near[3],-1);
  close(far[2]/far[3],1);
  close(clipPoint(p,[1,0,-1])[0]/near[3],1);
});
test('view transform handles oblique camera and target-center invariance',()=>{
  const camera=[2.3,1.35,2.7],target=[0,0.9,0];
  const view=nativeLookAt(camera,target);
  const eye=clipPoint(view,camera);
  for(const value of eye.slice(0,3))close(value,0);
  const t=clipPoint(view,target);
  close(t[0],0);close(t[1],0);
  assert.ok(t[2]<0);
});
test('invalid camera/frustum/clip values fail closed',()=>{
  assert.throws(()=>nativeLookAt([0,0,0],[0,0,0]),/Degenerate/);
  assert.throws(()=>nativeLookAt([0,2,0],[0,0,0]),/Degenerate/);
  assert.throws(()=>nativePerspective(0,1,.1,10),/Invalid/);
  assert.throws(()=>nativePerspective(1,0,.1,10),/Invalid/);
  assert.throws(()=>nativePerspective(1,1,10,1),/Invalid/);
  assert.throws(()=>nativePerspective(Number.NaN,1,.1,10),/Nonfinite/);
  assert.throws(()=>multiplyNativeMat4([0],[0]),/4x4/);
  assert.throws(()=>clipPoint(new Float32Array(16),[1]),/Malformed/);
});
test('view-projection gives finite centered pose and mirrored horizontal sign',()=>{
  const vp=multiplyNativeMat4(nativePerspective(.9,1,0.1,10),nativeLookAt([0,1,5],[0,1,0]));
  const middle=clipPoint(vp,[0,1,0]);
  const left=clipPoint(vp,[-1,1,0]),right=clipPoint(vp,[1,1,0]);
  close(middle[0]/middle[3],0);
  close(middle[1]/middle[3],0);
  close(left[0]/left[3],-right[0]/right[3]);
  assert.ok(left[0]/left[3]<0);
});
test('bone endpoint line packing uses real posed head/tail values and preserves named order',()=>{
  const rig={names:['left','right'],has:name=>name==='left'||name==='right'};
  const evalPort={
    head:name=>name==='left'?{x:-1,y:1,z:0}:{x:1,y:1,z:0},
    tail:name=>name==='left'?{x:-1,y:2,z:0}:{x:1,y:2,z:0}
  };
  assert.deepEqual([...packBoneSegments(rig,evalPort)],[-1,1,0,-1,2,0,1,1,0,1,2,0]);
  assert.deepEqual([...packBoneSegments(rig,evalPort,['right'])],[1,1,0,1,2,0]);
});
test('degenerate, spoofed, nonfinite, empty skeleton poses are rejected',()=>{
  const rig={names:['x'],has:name=>name==='x'};
  assert.throws(()=>packBoneSegments(rig,{head:()=>({x:0,y:0,z:0}),tail:()=>({x:0,y:0,z:0})}),/Degenerate/);
  assert.throws(()=>packBoneSegments(rig,{head:()=>({x:0,y:0,z:0}),tail:()=>({x:0,y:1,z:0})},['fake']),/Unknown bone/);
  assert.throws(()=>packBoneSegments(rig,{head:()=>({x:0,y:0,z:0}),tail:()=>({x:NaN,y:1,z:0})}),/Nonfinite/);
  assert.throws(()=>packBoneSegments(rig,{},[]),/No bones/);
});

function gpuStub({shaderOk=true,linkOk=true}={}){
  const calls=[];
  const gl={
    VERTEX_SHADER:0x8B31,FRAGMENT_SHADER:0x8B30,COMPILE_STATUS:0x8B81,LINK_STATUS:0x8B82,
    ARRAY_BUFFER:0x8892,FLOAT:0x1406,DEPTH_TEST:0x0B71,
    COLOR_BUFFER_BIT:0x4000,DEPTH_BUFFER_BIT:0x0100,DYNAMIC_DRAW:0x88E8,
    LINES:1,
    createShader:()=>({}),shaderSource:()=>{},compileShader:()=>{},
    getShaderParameter:()=>shaderOk,getShaderInfoLog:()=>'(mock compile error)',
    deleteShader:()=>{},createProgram:()=>({}),attachShader:()=>{},linkProgram:()=>{},
    getProgramParameter:()=>linkOk,getProgramInfoLog:()=>'(mock link error)',
    deleteProgram:()=>calls.push('deleteProgram'),
    createBuffer:()=>({}),createVertexArray:()=>({}),
    getUniformLocation:(_,name)=>({name}),bindVertexArray:()=>{},bindBuffer:()=>{},
    enableVertexAttribArray:()=>{},vertexAttribPointer:()=>{},enable:()=>{},
    viewport:()=>{},clearColor:()=>{},clear:()=>{},useProgram:()=>{},
    uniformMatrix4fv:(_,transpose,m)=>{assert.equal(transpose,false);assert.equal(m.length,16);},
    uniform4fv:()=>{},bufferData:(_,points)=>{assert.equal(points.length%6,0);},
    drawArrays:(_,start,count)=>{calls.push(['draw',start,count]);},
    deleteBuffer:()=>calls.push('deleteBuffer'),deleteVertexArray:()=>calls.push('deleteVAO'),
  };
  const events=new Map();
  const canvas={
    width:0,height:0,
    getContext:(name)=>{assert.equal(name,'webgl2');return gl;},
    addEventListener:(name,cb)=>events.set(name,cb),
    removeEventListener:(name)=>events.delete(name)
  };
  return {gl,canvas,calls,events};
}
test('first-party WebGL2 draws exact line count and releases original resources',()=>{
  const {canvas,calls,events}=gpuStub();
  const renderer=createFirstPartyWebGL2BoneRenderer(canvas);
  assert.equal(renderer.kind,NATIVE_RENDERER_KIND);
  renderer.setSize(200,100,2);
  assert.equal(canvas.width,400);assert.equal(canvas.height,200);
  const points=new Float32Array([0,0,0,0,1,0,-1,0,0,-1,1,0]);
  assert.equal(renderer.render(points),true);
  assert.equal(renderer.frameCount,1);
  assert.ok(calls.some(x=>Array.isArray(x)&&x[2]===4));
  assert.equal(events.size,2);
  renderer.dispose();renderer.dispose();
  assert.ok(calls.includes('deleteBuffer')&&calls.includes('deleteVAO')&&calls.includes('deleteProgram'));
  assert.equal(events.size,0);
  assert.throws(()=>renderer.render(points),/Disposed/);
});
test('renderer stops on context loss and reconstructs first-party resources on restore',()=>{
  const {canvas,events,calls}=gpuStub();
  const renderer=createFirstPartyWebGL2BoneRenderer(canvas);
  renderer.setSize(100,100);
  let prevented=false;
  events.get('webglcontextlost')({preventDefault:()=>{prevented=true;}});
  assert.equal(prevented,true);
  assert.equal(renderer.render(new Float32Array([0,0,0,0,1,0])),false);
  assert.equal(renderer.contextLost,true);
  events.get('webglcontextrestored')();
  assert.equal(renderer.contextLost,false);
  assert.equal(renderer.render(new Float32Array([0,0,0,0,1,0])),true);
  renderer.dispose();
});
test('renderer rejects invalid geometry/color rather than displaying falsely successful frame',()=>{
  const {canvas}=gpuStub();
  const r=createFirstPartyWebGL2BoneRenderer(canvas);
  assert.throws(()=>r.setSize(0,10),/viewport/);
  assert.throws(()=>r.render(new Float32Array([0,0,0])),/segments/);
  assert.throws(()=>r.render(new Float32Array([0,0,0,0,1,NaN])),/Nonfinite/);
  assert.throws(()=>r.render(new Float32Array([0,0,0,0,1,0]),{color:[1,1,2,1]}),/color/);
  assert.equal(r.frameCount,0);r.dispose();
});
test('native GPU program errors fail closed rather than shipping a blank display',()=>{
  for(const setting of [{shaderOk:false},{linkOk:false}]){
    const {canvas}=gpuStub(setting);
    assert.throws(()=>createFirstPartyWebGL2BoneRenderer(canvas),/compilation|link/);
  }
});
test('missing WebGL2 does not load an alternative third-party renderer',()=>{
  const canvas={getContext:()=>null};
  assert.throws(()=>createFirstPartyWebGL2BoneRenderer(canvas),/WebGL2 unavailable/);
});
