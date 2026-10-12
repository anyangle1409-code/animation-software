import test from 'node:test';
import assert from 'node:assert/strict';
import {probeOriginalFullBodyWebGL2,
 HGPT_ORIGINAL_WEBGL2_PROBE_KIND} from '../src/viewer/firstPartyOriginalWebGL2Capability.mjs';

const context=(max=4096,attribs=16)=>{
 let releases=0,reads=0;
 const gl={MAX_TEXTURE_SIZE:3379,MAX_VERTEX_ATTRIBS:34921,
 getParameter(p){reads++;return p===3379?max:attribs;},
 getExtension(n){assert.equal(n,'WEBGL_lose_context');
 return {loseContext(){releases++}};}};
 return {gl,get releases(){return releases},get reads(){return reads}};
};
test('never auto-probes a remote/browser global canvas',()=>{
 assert.throws(()=>probeOriginalFullBodyWebGL2(),/Explicit local canvas factory/);
});
test('reports context-unavailable without trying fallback GL/WebGL1',()=>{
 const calls=[];
 const p=probeOriginalFullBodyWebGL2({makeCanvas:()=>({
 getContext:(name,settings)=>{calls.push([name,settings]);return null}
 })});
 assert.deepEqual(calls,[['webgl2',{alpha:false,depth:true,antialias:true}]]);
 assert.equal(p.reason,'WEBGL2_CONTEXT_UNAVAILABLE');
 assert.equal(p.supported,false);
 assert.equal(p.modelDrawn,false);
});
test('67-joint RGBA32F palette must fit a 268-texel native texture',()=>{
 const contextSmall=context(267,16);
 const p=probeOriginalFullBodyWebGL2({
 makeCanvas:()=>({getContext:()=>contextSmall.gl})});
 assert.equal(p.reason,'JOINT_PALETTE_TEXTURE_TOO_SMALL');
 assert.equal(contextSmall.releases,1);
});
test('must have five available source attribute locations',()=>{
 const c=context(4096,4);
 const p=probeOriginalFullBodyWebGL2({makeCanvas:()=>({getContext:()=>c.gl})});
 assert.equal(p.reason,'NATIVE_VERTEX_ATTRIBUTES_INSUFFICIENT');
 assert.equal(c.releases,1);
});
test('successful capability probe never asserts original source/GPU proof',()=>{
 const c=context();
 const p=probeOriginalFullBodyWebGL2({makeCanvas:()=>({getContext:()=>c.gl})});
 assert.equal(p.kind,HGPT_ORIGINAL_WEBGL2_PROBE_KIND);
 assert.equal(p.supported,true);
 assert.equal(p.paletteTexelsRequired,268);
 assert.equal(p.sourceModelSHA256Verified,false);
 assert.equal(p.originalGpuDrawVerified,false);
 assert.equal(p.productionReady,false);
 assert.equal(p.modelDrawn,false);
 assert.equal(c.releases,1);
 assert.ok(Object.isFrozen(p));
});
test('exceptions are an explicit unsupported state without leaking diagnostics',()=>{
 const p=probeOriginalFullBodyWebGL2({makeCanvas:()=>({getContext(){
 throw new Error('private device details should not surface')
 }})});
 assert.deepEqual([p.reason,p.supported,p.modelDrawn],
 ['WEBGL2_PROBE_FAILED',false,false]);
});
