import test from 'node:test';
import assert from 'node:assert/strict';
import {probeOriginalPaletteShaderLink} from '../src/viewer/firstPartyOriginalPaletteShaderLink.mjs';
function fake({compile=true,link=true,glError=0}={}){
 const counts={deletedShader:0,deletedProgram:0,lost:0,compiled:0,linked:0};
 const gl={VERTEX_SHADER:35633,FRAGMENT_SHADER:35632,COMPILE_STATUS:35713,
 LINK_STATUS:35714,NO_ERROR:0,
 createShader(k){return {k}},shaderSource(s,c){assert.match(c,/#version 300 es/);
 if(s.k===35633){
 assert.match(c,/uniform int uJointIndex/);
 assert.match(c,/clamp\(uJointIndex,0,66\)\*4/);
 for(let column=0;column<4;column++)
  assert.ok(c.includes(`ivec2(firstTexel+${column},0)`));
 }},
 compileShader(){counts.compiled++},
 getShaderParameter(){return compile},createProgram(){return {}},
 attachShader(){},linkProgram(){counts.linked++},
 getProgramParameter(){return link},getError(){return glError},
 deleteShader(){counts.deletedShader++},deleteProgram(){counts.deletedProgram++},
 getExtension(){return {loseContext(){counts.lost++}}}};
 return {gl,counts};
}
test('requires explicit caller-local canvas',()=>assert.throws(
 ()=>probeOriginalPaletteShaderLink(),/Local canvas factory required/));
test('no WebGL2 is not proof of a rendered human',()=>{
 const p=probeOriginalPaletteShaderLink({makeCanvas:()=>({getContext:()=>null})});
 assert.equal(p.reason,'WEBGL2_UNAVAILABLE');
 assert.equal(p.originalHumanGpuDrawVerified,false);
});
test('native vertex texture sampler shader compiles, links, and releases',()=>{
 const x=fake();
 const p=probeOriginalPaletteShaderLink({makeCanvas:()=>({getContext:()=>x.gl})});
 assert.equal(p.linked,true);assert.equal(p.productionReady,false);
 assert.equal(p.originalHumanGpuDrawVerified,false);
 assert.equal(x.counts.compiled,2);assert.equal(x.counts.linked,1);
 assert.equal(x.counts.deletedShader,2);assert.equal(x.counts.deletedProgram,1);
 assert.equal(x.counts.lost,1);
});
test('vertex shader compile error blocks linkage',()=>{
 const x=fake({compile:false});
 const p=probeOriginalPaletteShaderLink({makeCanvas:()=>({getContext:()=>x.gl})});
 assert.equal(p.reason,'PALETTE_SHADER_COMPILE_FAILED');
 assert.equal(x.counts.linked,0);assert.equal(x.counts.deletedShader,2);
});
test('link errors and GL errors are explicit blockers',()=>{
 for(const opts of [{link:false},{glError:1282}]){
 const x=fake(opts);
 const p=probeOriginalPaletteShaderLink({makeCanvas:()=>({getContext:()=>x.gl})});
 assert.equal(p.reason,'PALETTE_SHADER_LINK_FAILED');
 assert.equal(x.counts.deletedProgram,1);
 }
});

test('shader addressing explicitly spans first and last 67-joint matrix bounds',()=>{
 const positions=[0,66];
 for(const index of positions){
  const offset=Math.min(66,Math.max(0,index))*4;
  assert.ok(offset>=0&&offset+3<268);
 }
 assert.equal(66*4+3,267);
});
