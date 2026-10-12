import test from 'node:test';
import assert from 'node:assert/strict';
import {createOriginalWorkOrbitCamera,HGPT_W1_SOURCE_SHA256}
  from '../src/viewer/firstPartyOriginalWorkOrbitCamera.mjs';
function fixture(){
  const events=new Map(),draws=[];
  const canvas={width:960,height:540,clientHeight:540,style:{touchAction:'auto'},
    addEventListener(name,fn){events.set(name,fn)},
    removeEventListener(name){events.delete(name)},
    emit(name,e){events.get(name)?.(e)},
    setPointerCapture(){},hasPointerCapture(){return false}};
  const model={kind:'hgpt-provisional-original-model-handoff-v1',
    sourceSha256:HGPT_W1_SOURCE_SHA256,numberOfPrimitives:18,
    sourceJointNames:Array(6).fill('source'),
    audit:{allGLBPrimitivesDecodedAndBound:true,
      provisionalLargeSceneDiagnosticOnly:true,
      independentlyVerifiedSourceRights:false,modelProductionReady:false}};
  const registered={modelSha256:HGPT_W1_SOURCE_SHA256,
    status:'REGISTERED_SOURCE_POSES_DIAGNOSTIC_ONLY',
    originalFrameCount:7,motionIsRelativeFromRestNotAbsoluteElevation:true,
    interpolationInvented:false,modelProductionReady:false};
  const renderPose=(i,camera)=>{draws.push({i,camera});return{
    drewAllOriginalPilotParts:true,originalPrimitiveCount:18,productionReady:false}};
  return {canvas,model,registered,renderPose,events,draws};
}
test('fail closed without explicit opt-in or exact source SHA',()=>{
  const f=fixture();
  assert.throws(()=>createOriginalWorkOrbitCamera(f),/opt-in/);
  assert.equal(f.events.size,0);
  f.model.sourceSha256='0'.repeat(64);
  assert.throws(()=>createOriginalWorkOrbitCamera({...f,diagnosticOptIn:true}),/SHA-bound/);
});
test('reject false rights or production claims and unregistered poses',()=>{
  for(const [field,value] of [['independentlyVerifiedSourceRights',true],
    ['modelProductionReady',true]]){
    const f=fixture();f.model.audit[field]=value;
    assert.throws(()=>createOriginalWorkOrbitCamera({...f,diagnosticOptIn:true}),/W1 model/);
  }
  for(const [field,value] of [['interpolationInvented',true],
    ['modelProductionReady',true],['originalFrameCount',8]]){
    const f=fixture();f.registered[field]=value;
    assert.throws(()=>createOriginalWorkOrbitCamera({...f,diagnosticOptIn:true}),/registered/);
  }
});
test('orbit pointer, zoom, seven authored poses, return to neutral',()=>{
  const f=fixture(),c=createOriginalWorkOrbitCamera({...f,diagnosticOptIn:true});
  assert.equal(f.canvas.style.touchAction,'none');
  const first=c.draw();assert.equal(first.poseIndex,0);
  f.canvas.emit('pointerdown',{pointerType:'mouse',button:0,pointerId:1,clientX:100,clientY:100});
  f.canvas.emit('pointermove',{pointerId:1,clientX:240,clientY:140});
  f.canvas.emit('pointerup',{pointerId:1});
  assert.notDeepEqual(c.snapshot().eye,first.eye);
  const oldDistance=c.snapshot().distance;
  let prevented=false;
  f.canvas.emit('wheel',{deltaY:-120,preventDefault(){prevented=true}});
  assert.ok(prevented);assert.ok(c.snapshot().distance<oldDistance);
  assert.equal(c.setPoseIndex(4).poseIndex,4);
  assert.equal(c.setPoseIndex(6).poseIndex,6);
  assert.throws(()=>c.setPoseIndex(7),/0\.\.6/);
  assert.ok(f.draws.length>=5);
  assert.ok(f.draws.every(x=>x.camera.eye.every(Number.isFinite)));
  c.dispose();assert.equal(f.events.size,0);
  assert.equal(f.canvas.style.touchAction,'auto');
  assert.throws(()=>c.draw(),/disposed/);
});
test('two pointer pinch bounded and malformed input ignored',()=>{
  const f=fixture(),c=createOriginalWorkOrbitCamera({...f,diagnosticOptIn:true});
  f.canvas.emit('pointerdown',{pointerType:'touch',pointerId:1,clientX:10,clientY:10});
  f.canvas.emit('pointerdown',{pointerType:'touch',pointerId:2,clientX:30,clientY:10});
  f.canvas.emit('pointermove',{pointerId:2,clientX:100,clientY:10});
  assert.ok(c.snapshot().distance<3.4);
  f.canvas.emit('pointermove',{pointerId:2,clientX:NaN,clientY:10});
  assert.ok(Number.isFinite(c.snapshot().distance));
  f.canvas.emit('pointerup',{pointerId:1});
  f.canvas.emit('pointerup',{pointerId:2});
  c.dispose();
});
test('GPU renderer must report complete 18-part diagnostic draw',()=>{
  const f=fixture();f.renderPose=()=>({drewAllOriginalPilotParts:false,originalPrimitiveCount:18,productionReady:false});
  const c=createOriginalWorkOrbitCamera({...f,diagnosticOptIn:true});
  assert.throws(()=>c.draw(),/draw incomplete/);c.dispose();
});
test('hostile finite pointer coordinates cannot corrupt original camera matrices',()=>{
  const f=fixture(),c=createOriginalWorkOrbitCamera({...f,diagnosticOptIn:true});
  const initial=c.draw();
  f.canvas.emit('pointerdown',{pointerType:'touch',pointerId:1,clientX:1e308,clientY:0});
  f.canvas.emit('pointerdown',{pointerType:'touch',pointerId:2,clientX:-1e308,clientY:0});
  f.canvas.emit('pointermove',{pointerId:2,clientX:-1e308,clientY:0});
  assert.deepEqual(c.snapshot().eye,initial.eye);
  assert.equal(c.snapshot().distance,3.4);
  f.canvas.emit('pointerdown',{pointerType:'mouse',button:0,pointerId:3,clientX:100,clientY:100});
  for(let i=0;i<30;i++)f.canvas.emit('pointermove',{
    pointerId:3,clientX:i%2?1000000:-1000000,clientY:100});
  assert.ok(c.snapshot().eye.every(Number.isFinite));
  assert.ok(Math.abs(c.snapshot().yaw)<=2*Math.PI);
  c.dispose();
});
test('rejected GPU pose draw rolls back selected authored pose',()=>{
  const f=fixture();let allowed=true;
  f.renderPose=(i)=>({drewAllOriginalPilotParts:allowed||i===0,
    originalPrimitiveCount:18,productionReady:false});
  const c=createOriginalWorkOrbitCamera({...f,diagnosticOptIn:true});
  c.draw();allowed=false;
  assert.throws(()=>c.setPoseIndex(4),/draw incomplete/);
  assert.equal(c.snapshot().poseIndex,0);
  c.dispose();
});
