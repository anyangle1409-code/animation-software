import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSyntheticExerciseHandoff} from './support/buildSyntheticExerciseHandoff.mjs';
import {bindFirstPartyExerciseToDiagnosticPose} from '../src/exercise/firstPartyExercisePoseBinding.mjs';
import {createDiagnosticExercisePlayback} from '../src/viewer/firstPartyDiagnosticPlayback.mjs';
async function fixture(){
  const x=await buildSyntheticExerciseHandoff();
  const binding=bindFirstPartyExerciseToDiagnosticPose(x.command,x.model,x.clip,x.declaration);
  const draws=[],pending=new Map(),history=new Map();let next=0;
  const requestFrame=fn=>{pending.set(++next,fn);history.set(next,fn);return next;};
  const cancelFrame=id=>pending.delete(id);
  const p=createDiagnosticExercisePlayback(binding,{draw:(frame,index)=>draws.push({frame,index}),requestFrame,cancelFrame});
  const tick=t=>{const e=pending.entries().next().value;assert.ok(e,'one scheduled frame');pending.delete(e[0]);e[1](t);};
  return {p,draws,pending,history,tick,binding};
}
test('plays only exact authored samples, holds between them and completes without a live loop',async()=>{
  const {p,draws,pending,tick}=await fixture();p.play();
  tick(1000);tick(1100);tick(1500);tick(1750);tick(2000);
  assert.deepEqual(draws.map(d=>d.index),[0,1,2]);assert.equal(p.state().status,'completed');
  assert.equal(pending.size,0);assert.equal(p.state().interpolationPerformed,false);
});
test('pause/resume, seek and dispose cancel stale callbacks and bound copied frames',async()=>{
  const {p,draws,pending,history,tick}=await fixture();p.play();tick(0);tick(250);
  const stale=[...history.values()].at(-1);p.pause();assert.equal(pending.size,0);
  stale(700);assert.equal(draws.length,1);
  p.seek(.75);assert.equal(draws.at(-1).index,1);draws.at(-1).frame.sourceJointOrderedPalette[12]=99;
  p.seek(.75);assert.ok(draws.at(-1).frame.sourceJointOrderedPalette[12]<1);
  p.play();tick(1000);tick(1250);assert.equal(draws.at(-1).index,2);
  p.dispose();assert.equal(pending.size,0);assert.throws(()=>p.play(),/disposed/);
});
test('cannot consume forged binding or invalid time and clock inputs',async()=>{
  const {p,binding,tick}=await fixture();
  assert.throws(()=>createDiagnosticExercisePlayback({...binding},{draw:()=>{}}),/validated/);
  for(const t of [-1,NaN,Infinity,1.1])assert.throws(()=>p.seek(t),/time/);
  p.play();assert.throws(()=>tick(NaN),/clock/);assert.equal(p.state().status,'paused');
});
test('draw failure stops scheduling and disposal inside draw prevents rescheduling',async()=>{
  const {binding}=await fixture();let callback,p;
  p=createDiagnosticExercisePlayback(binding,{draw:()=>p.dispose(),requestFrame:f=>{callback=f;return 1;},cancelFrame:()=>{}});
  p.play();assert.equal(p.state().status,'disposed');assert.equal(callback,undefined);
  const bad=createDiagnosticExercisePlayback(binding,{draw:()=>{throw Error('draw failed');},requestFrame:()=>{throw Error('must not schedule');},cancelFrame:()=>{}});
  assert.throws(()=>bad.play(),/draw failed/);assert.equal(bad.state().status,'paused');
});
test('scheduler resource failure leaves playback stopped',async()=>{
  const {binding}=await fixture();
  const p=createDiagnosticExercisePlayback(binding,{draw:()=>{},requestFrame:()=>{throw Error('scheduler unavailable');},cancelFrame:()=>{}});
  assert.throws(()=>p.play(),/scheduler unavailable/);assert.equal(p.state().status,'paused');
});
