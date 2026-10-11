#!/usr/bin/env node
/** Browser G1f: original embedded PNGs → actual WebGL2 texture sampling and GPU pixel readback. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {deflateSync} from 'node:zlib';
import {chromium} from 'playwright';
import {buildSyntheticBatchedGlb} from '../tests/support/buildSyntheticBatchedGlb.mjs';
const port=5192,base='http://127.0.0.1:'+port+'/';
const out=path.resolve('reports/browser-smoke/first-party-g1f-embedded-png');
fs.mkdirSync(out,{recursive:true});
const align=n=>(n+3)&~3;
function extract(glb){
  const v=new DataView(glb),j=v.getUint32(12,true),p=20+j;
  return {root:JSON.parse(new TextDecoder().decode(new Uint8Array(glb,20,j)).trim()),
    bin:new Uint8Array(glb,p+8,v.getUint32(p,true))};
}
function pack(root,bin){
  const enc=new TextEncoder().encode(JSON.stringify(root));
  const jlen=align(enc.length),total=12+8+jlen+8+bin.length;
  const b=new ArrayBuffer(total),v=new DataView(b);
  v.setUint32(0,0x46546c67,true);v.setUint32(4,2,true);v.setUint32(8,total,true);
  v.setUint32(12,jlen,true);v.setUint32(16,0x4e4f534a,true);
  new Uint8Array(b,20,jlen).fill(32);new Uint8Array(b,20,enc.length).set(enc);
  const p=20+jlen;
  v.setUint32(p,bin.length,true);v.setUint32(p+4,0x004e4942,true);
  new Uint8Array(b,p+8,bin.length).set(bin);
  return b;
}
function crc(arr){
  let v=0xffffffff;
  for(const b of arr){v^=b;for(let i=0;i<8;i++)v=(v>>>1)^((v&1)?0xedb88320:0)}
  return(v^0xffffffff)>>>0;
}
function chunk(name,payload){
  const n=new Uint8Array(12+payload.length),v=new DataView(n.buffer);
  n.set(new TextEncoder().encode(name),4);n.set(payload,8);
  v.setUint32(0,payload.length,false);
  v.setUint32(n.length-4,crc(n.subarray(4,n.length-4)),false);
  return n;
}
function png2x2(r,g,b){
  const ihdr=new Uint8Array(13);
  new DataView(ihdr.buffer).setUint32(0,2,false);
  new DataView(ihdr.buffer).setUint32(4,2,false);
  ihdr[8]=8;ihdr[9]=6;
  const raw=new Uint8Array([
    0,r,g,b,255,r,g,b,255,
    0,r,g,b,255,r,g,b,255
  ]);
  const bytes=[new Uint8Array([137,80,78,71,13,10,26,10]),
    chunk('IHDR',ihdr),chunk('IDAT',new Uint8Array(deflateSync(raw))),
    chunk('IEND',new Uint8Array())];
  const result=new Uint8Array(bytes.reduce((n,b)=>n+b.length,0));
  let pos=0;for(const b of bytes){result.set(b,pos);pos+=b.length}
  return result;
}
function source(){
  const {root,bin:input}=extract(buildSyntheticBatchedGlb());
  const chunks=[];let offset=input.length;
  const add=bytes=>{
    const at=offset;chunks.push({at,bytes});offset+=align(bytes.length);
    root.bufferViews.push({buffer:0,byteOffset:at,byteLength:bytes.length});
    return root.bufferViews.length-1;
  };
  for(let m=0;m<2;m++){
    const uv=add(new Uint8Array(new Float32Array([0,0,1,0,0,1]).buffer));
    root.accessors.push({bufferView:uv,componentType:5126,count:3,type:'VEC2'});
    root.meshes[m].primitives[0].attributes.TEXCOORD_0=root.accessors.length-1;
    root.meshes[m].primitives[0].material=m;
  }
  const imageViews=[add(png2x2(247,20,23)),add(png2x2(15,244,32))];
  root.images=imageViews.map((n,i)=>({name:'original_png_'+i,bufferView:n,mimeType:'image/png'}));
  root.samplers=[{magFilter:9729,minFilter:9729,wrapS:33071,wrapT:33071}];
  root.textures=[{source:0,sampler:0},{source:1,sampler:0}];
  root.materials=[0,1].map(i=>({name:'project_original_mat_'+i,
    pbrMetallicRoughness:{baseColorFactor:[1,1,1,1],
      metallicFactor:0,roughnessFactor:1,baseColorTexture:{index:i,texCoord:0}}}));
  const combined=new Uint8Array(offset);combined.set(input,0);
  for(const {at,bytes}of chunks)combined.set(bytes,at);
  root.buffers[0].byteLength=combined.length;
  return pack(root,combined);
}
const raw=source(),sourceCopy=new Uint8Array(raw).slice();
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','--host','127.0.0.1',
  '--port',String(port),'--strictPort'],{stdio:'ignore'});
let browser;
async function ready(){
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw new Error('Vite texture test server exited');
    try{if((await fetch(base)).ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  throw new Error('Native image WebGL2 smoke server unavailable');
}
try{
  await ready();
  browser=await chromium.launch({headless:true,
    args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
  const page=await browser.newPage({viewport:{width:1200,height:800}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);
  const report=await page.evaluate(async bytes=>{
    const {parseRestrictedBatchedSkinnedGlb:parse}=await import(
      '/src/viewer/firstPartyGlbSkinnedBatches.mjs');
    const {createNativeEmbeddedPngWebGL2:renderer}=await import(
      '/src/viewer/firstPartyEmbeddedPngWebGL2.mjs');
    const source=parse(new Uint8Array(bytes).buffer,{
      allowSourceFlatColors:true,allowSourceUV0:true,
      allowEmbeddedPngBaseColor:true,
    });
    const canvas=document.createElement('canvas');document.body.appendChild(canvas);
    const native=renderer(canvas);
    native.setSize(960,540);
    const accepted=await native.setSourceBatches(source.batches);
    for(let i=0;i<12;i++)native.render({eye:[1.1,.45,4.5],target:[1.1,.45,0]});
    const gl=canvas.getContext('webgl2');
    const arr=new Uint8Array(canvas.width*canvas.height*4);
    gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,arr);
    let red=0,green=0,both=0;
    for(let i=0;i<arr.length;i+=4){
      const r=arr[i],g=arr[i+1],b=arr[i+2];
      if(r>150&&r>g*2.5&&r>b*2.5)red++;
      if(g>150&&g>r*2.5&&g>b*2.5)green++;
      if(r>150&&g>150)both++;
    }
    const result={sourceGLBBytes:bytes.length,sourceMeshes:source.audit.numberOfMeshes,
      sourcePrimitives:source.audit.numberOfPrimitives,
      pngSourcesValidated:source.audit.embeddedPngBaseColorSourceValidated,
      sourceTextures:accepted.textures,sourcePixels:accepted.pixels,
      kind:native.kind,frames:native.frames,draws:native.draws,
      red,green,both,glError:gl.getError(),originalHumanApproved:source.audit.actualOriginalHumanMeshUsed,
      textureSamplingPreviouslyImplemented:source.audit.textureSamplingImplemented};
    native.dispose();
    return result;
  },Array.from(new Uint8Array(raw)));
  assert.deepEqual(new Uint8Array(raw),sourceCopy);
  assert.equal(report.pngSourcesValidated,true);
  assert.equal(report.sourceTextures,2);
  assert.equal(report.sourcePixels,8);
  assert.equal(report.kind,'hgpt-webgl2-source-embedded-png-preview-v1');
  assert.equal(report.frames,12);
  assert.equal(report.draws,24);
  assert.ok(report.red>200,'source PNG A red GPU fragments not visible');
  assert.ok(report.green>200,'source PNG B green GPU fragments not visible');
  assert.ok(report.both<100,'cross-colour source texture bleeding');
  assert.equal(report.glError,0);
  assert.equal(report.originalHumanApproved,false);
  assert.equal(report.textureSamplingPreviouslyImplemented,false);
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'actual-source-png-gpu-pixels.json'),
    JSON.stringify({passed:true,...report,syntheticSourceOnly:true,
      fullHumanDeformationApproved:false,realPBRImplemented:false},null,2)+'\n');
  console.log(JSON.stringify(report));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
