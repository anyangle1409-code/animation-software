import test from 'node:test';
import assert from 'node:assert/strict';
import {probeOriginalPaletteFloatUpload} from '../src/viewer/firstPartyOriginalPaletteFloatUpload.mjs';
const glFor=(error=0,alloc=true)=>{
 const calls={made:0,deleted:0,released:0,uploaded:0};
 const gl={
 MAX_TEXTURE_SIZE:3379,MAX_VERTEX_ATTRIBS:34921,
 MAX_VERTEX_TEXTURE_IMAGE_UNITS:35660,
 TEXTURE_2D:3553,TEXTURE_MIN_FILTER:10241,TEXTURE_MAG_FILTER:10240,
 TEXTURE_WRAP_S:10242,TEXTURE_WRAP_T:10243,CLAMP_TO_EDGE:33071,
 NEAREST:9728,RGBA32F:34836,RGBA:6408,FLOAT:5126,NO_ERROR:0,
 getParameter(p){return p===3379?4096:16},
 createTexture(){calls.made++;return alloc?{}:null},
 bindTexture(){},texParameteri(){},
 texImage2D(...args){
  calls.uploaded++;
  assert.equal(args[2],gl.RGBA32F);assert.equal(args[3],268);
  assert.equal(args[4],1);assert.equal(args[8].length,268*4);
 },
 getError(){return error},
 deleteTexture(){calls.deleted++},
 getExtension(){return {loseContext(){calls.released++}}}
 };
 return {gl,calls};
};
test('fresh local context required',()=>assert.throws(
 ()=>probeOriginalPaletteFloatUpload(),/caller-owned fresh canvas/));
test('actual 268x1 RGBA32F zero palette uploads and releases safely',()=>{
 const x=glFor();
 const result=probeOriginalPaletteFloatUpload({makeCanvas:()=>({
 getContext:()=>x.gl})});
 assert.equal(result.ready,true);
 assert.equal(result.originalHumanDrawProved,false);
 assert.equal(result.modelRead,false);
 assert.equal(x.calls.uploaded,1);
 assert.equal(x.calls.deleted,1);
 assert.equal(x.calls.released,2);
});
test('GPU upload error fails closed and deletes temporary texture',()=>{
 const x=glFor(1282);
 const result=probeOriginalPaletteFloatUpload({makeCanvas:()=>({
 getContext:()=>x.gl})});
 assert.equal(result.reason,'RGBA32F_PALETTE_UPLOAD_FAILED');
 assert.equal(result.ready,false);
 assert.equal(x.calls.deleted,1);
});
test('texture allocation failure does not claim GPU proof',()=>{
 const x=glFor(0,false);
 const result=probeOriginalPaletteFloatUpload({makeCanvas:()=>({
 getContext:()=>x.gl})});
 assert.equal(result.reason,'PALETTE_UPLOAD_PROBE_FAILED');
 assert.equal(result.gpuUploadProved,false);
 assert.equal(x.calls.deleted,0);
});
test('lack of basic WebGL2 returns prior capability blocker without upload',()=>{
 const x=glFor();
 x.gl.getParameter=(p)=>p===3379?128:16;
 const result=probeOriginalPaletteFloatUpload({makeCanvas:()=>({
 getContext:()=>x.gl})});
 assert.equal(result.reason,'JOINT_PALETTE_TEXTURE_TOO_SMALL');
 assert.equal(x.calls.uploaded,0);
});
