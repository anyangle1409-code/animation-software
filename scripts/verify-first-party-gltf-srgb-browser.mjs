#!/usr/bin/env node
/** Browser G2e: independently measured glTF sRGB baseColor with linear material-factor tint on moving GPU skin. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {deflateSync} from 'node:zlib';
import {chromium} from 'playwright';
import {buildSyntheticBatchedGlb} from '../tests/support/buildSyntheticBatchedGlb.mjs';
const port=5202,base='http://127.0.0.1:'+port+'/';
const out=path.resolve('reports/browser-smoke/first-party-g2e-srgb-source-tint');
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
    pbrMetallicRoughness:{baseColorFactor:i===0?[.5,.5,.5,1]:[1,1,1,1],
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
  const errors=[],externalRequests=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{
    const u=r.url();
    if(!u.startsWith(base)&&!u.startsWith('data:')&&!u.startsWith('blob:'))
      externalRequests.push(u);
  });
  await page.goto(base);
  const report=await page.evaluate(async bytes=>{
    const {parseRestrictedBatchedSkinnedGlb:parse}=await import(
      '/src/viewer/firstPartyGlbSkinnedBatches.mjs');
    const {createNativePaletteSkinnedWebGL2:renderer}=await import(
      '/src/viewer/firstPartyGpuPaletteSkinning.mjs');
    const source=parse(new Uint8Array(bytes).buffer,{
      allowSourceFlatColors:true,allowSourceUV0:true,
      allowEmbeddedPngBaseColor:true
    });
    const canvas=document.createElement('canvas');document.body.appendChild(canvas);
    const native=renderer(canvas);
    native.setSize(960,540);
    const pose=x=>{
      const tr=new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,x,0,0,1]);
      const world=new Float32Array(32);
      world.set(tr);
      const other=tr.slice();other[12]=x*.35;
      world.set(other,16);
      return world;
    };
    const parts=source.batches.map(p=>({
      mesh:p.parsed.mesh,uv0:p.sourceUV0,posedWorld:pose(0)
    }));
    const camera={eye:[1.1,.45,4.5],target:[1.1,.45,0]};
    const measure=()=>{
      const gl=canvas.getContext('webgl2');
      const bytes=new Uint8Array(canvas.width*canvas.height*4);
      gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,bytes);
      let count=0,redTotal=0,redCenter=0,greenCount=0;
      for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++){
        const k=(y*canvas.width+x)*4,r=bytes[k],g=bytes[k+1],b=bytes[k+2];
        if(r>95&&r>g*2.5&&r>b*2.5){count++;redTotal+=r;redCenter+=x}
        if(g>150&&g>r*2.5&&g>b*2.5)greenCount++;
      }
      return {redCount:count,greenCount,averageRed:count?redTotal/count:0,
        redCentroidX:count?redCenter/count:0,gpuError:gl.getError()};
    };
    await native.setSourcePngBatches(source.batches);
    native.renderBatches(parts,{...camera,texturePreview:true});
    const legacy=measure();
    let modeMismatchRejected=false,invalidSpaceRejected=false;
    try{
      native.renderBatches(parts,{...camera,texturePreview:true,
        colorManagedTexturePreview:true});
    }catch(e){modeMismatchRejected=/must match shader color mode/.test(e.message)}
    try{
      await native.setSourcePngBatches(source.batches,{colorSpace:'unknown'});
    }catch(e){invalidSpaceRejected=/supported mode/.test(e.message)}
    const prepared=await native.setSourcePngBatches(source.batches,
      {colorSpace:'gltf-srgb'});
    let reverseMismatchRejected=false;
    try{native.renderBatches(parts,{...camera,texturePreview:true});}
    catch(e){reverseMismatchRejected=/must match shader color mode/.test(e.message)}
    native.renderBatches(parts,{...camera,texturePreview:true,
      colorManagedTexturePreview:true});
    const linearSrgb=measure();
    for(let i=1;i<=8;i++){
      for(const part of parts)part.posedWorld=pose(.45*i/8);
      native.renderBatches(parts,{...camera,texturePreview:true,
        colorManagedTexturePreview:true});
    }
    const animated=measure();
    const snap=canvas.toDataURL('image/png');
    const result={shaderKind:native.kind,colorSpace:prepared.colorSpace,
      primitives:source.batches.length,legacy,linearSrgb,animated,
      frames:native.frameCount,draws:native.drawCallCount,
      modeMismatchRejected,reverseMismatchRejected,invalidSpaceRejected,
      humanMovementApproved:source.audit.actualOriginalHumanMeshUsed,
      snapshot:snap};
    native.dispose();
    return result;
  },Array.from(new Uint8Array(raw)));
  const encoded=(x)=>x<=.0031308?12.92*x:1.055*x**(1/2.4)-.055;
  const decoded=(x)=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4;
  const expectedLegacy=247*.5;
  const expectedLinear=255*encoded(decoded(247/255)*.5);
  assert.deepEqual(new Uint8Array(raw),sourceCopy);
  assert.equal(report.shaderKind,'hgpt-native-webgl2-rgba32f-4weight-gpu-lbs-v1');
  assert.equal(report.colorSpace,'gltf-srgb');
  assert.equal(report.primitives,2);
  assert.equal(report.frames,10);
  assert.equal(report.draws,20);
  assert.equal(report.modeMismatchRejected,true);
  assert.equal(report.reverseMismatchRejected,true);
  assert.equal(report.invalidSpaceRejected,true);
  for(const key of ['legacy','linearSrgb','animated']){
    assert.ok(report[key].redCount>200,'missing red original source texture in '+key);
    assert.ok(report[key].greenCount>200,'missing green original source texture in '+key);
    assert.equal(report[key].gpuError,0,'GPU error in '+key);
  }
  assert.ok(Math.abs(report.legacy.averageRed-expectedLegacy)<4,
    'Legacy RGBA8 source tint changed unexpectedly');
  assert.ok(Math.abs(report.linearSrgb.averageRed-expectedLinear)<4,
    'Native SRGB8_ALPHA8 decode/linear material tint/sRGB output differs from independent transfer-function oracle');
  assert.ok(report.linearSrgb.averageRed-report.legacy.averageRed>35,
    'sRGB transfer function should visibly differ from nonlinear RGB multiplication');
  assert.ok(Math.abs(report.animated.averageRed-expectedLinear)<4,
    'Moving textured skin should retain source material colour');
  assert.ok(report.animated.redCentroidX-report.linearSrgb.redCentroidX>25,
    'Corrected source-red texture did not move with GPU skeletal skinning');
  assert.equal(report.humanMovementApproved,false);
  assert.deepEqual(errors,[]);
  assert.deepEqual(externalRequests,[]);
  assert.match(report.snapshot,/^data:image\/png;base64,/);
  const image=Buffer.from(report.snapshot.slice('data:image/png;base64,'.length),'base64');
  assert.ok(image.length>1024,'Real moving-colour-managed PNG screenshot missing');
  fs.writeFileSync(path.join(out,'actual-moving-srgb-glb-material.png'),image);
  const {snapshot,...safe}=report;
  const result={...safe,expectedLegacy,expectedLinear,
    pass:true,actualHumanApproved:false,
    firstPartySourceTextureOnly:true,
    noPBRLightingOrToneMapping:true};
  fs.writeFileSync(path.join(out,'gltf-srgb-gpu-colour-oracle.json'),
    JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
