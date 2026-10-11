#!/usr/bin/env node
/** G2d real Chromium GPU moving PNG pixels + same-shader CPU/GPU parity. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';
import {buildSyntheticMovingTexturedGlb} from '../tests/support/buildSyntheticMovingTexturedGlb.mjs';
const port=5194,base='http://127.0.0.1:'+port+'/';
const output=path.resolve('reports/browser-smoke/first-party-g2d-moving-png');
fs.mkdirSync(output,{recursive:true});
const raw=buildSyntheticMovingTexturedGlb();
const unchanged=new Uint8Array(raw).slice();
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','--host',
  '127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});
let browser;
try{
  let up=false;
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw Error('G2d Vite server exited');
    try{if((await fetch(base)).ok){up=true;break;}}catch{}
    await new Promise(r=>setTimeout(r,200));
  }
  assert.ok(up,'G2d local test server unavailable');
  browser=await chromium.launch({headless:true,
    args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
  const page=await browser.newPage({viewport:{width:1200,height:800}});
  const errors=[],remote=[],vendor=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{
    const url=r.url();
    if(!url.startsWith(base)&&!url.startsWith('data:'))remote.push(url);
    if(/threeRuntimeBoundary|threeSceneBoundary|node_modules\/\.vite\/deps\/three|react-dom|@react-three/.test(url))
      vendor.push(url);
  });
  await page.goto(base+'native-webgl2-skinning-preview.html');
  const result=await page.evaluate(async bytes=>{
    const {parseRestrictedBatchedSkinnedGlb:parse}=await import(
      '/src/viewer/firstPartyGlbSkinnedBatches.mjs');
    const {createNativeMovingTexturedSkinWebGL2:create}=await import(
      '/src/viewer/firstPartyMovingTexturedSkinWebGL2.mjs');
    const {deformIndexedSkin}=await import(
      '/src/viewer/firstPartyIndexedSkinnedMesh.mjs');
    const {referenceSkinOriginalUnitNormals}=await import(
      '/src/viewer/firstPartySkinnedNormalReference.mjs');
    const source=parse(new Uint8Array(bytes).buffer,{
      allowSourceFlatColors:true,allowSourceUV0:true,
      allowSourceNormals:true,allowEmbeddedPngBaseColor:true
    });
    const canvas=document.createElement('canvas');document.body.append(canvas);
    const renderer=create(canvas);renderer.setSize(960,540);
    const loaded=await renderer.setSourceBatches(source.batches);
    const ident=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
    const rot=a=>{const c=Math.cos(a),s=Math.sin(a);
      return new Float32Array([c,s,0,0,-s,c,0,0,0,0,1,0,0,0,0,1]);};
    const gl=canvas.getContext('webgl2');
    const pixels=()=>{const a=new Uint8Array(canvas.width*canvas.height*4);
      gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,a);
      return a;};
    const tally=a=>{
      let red=0,green=0,rx=0,gx=0;
      for(let i=0;i<a.length;i+=4){
        const r=a[i],g=a[i+1],b=a[i+2],x=(i/4)%canvas.width;
        if(r>120&&r>g*2.5&&r>b*2.5){red++;rx+=x;}
        if(g>120&&g>r*2.5&&g>b*2.5){green++;gx+=x;}
      }
      return {red,green,redX:rx/Math.max(1,red),greenX:gx/Math.max(1,green)};
    };
    let first,last,maxPositionError=0,maxNormalError=0,normalLengths=[Infinity,0];
    for(let frame=0;frame<12;frame++){
      const angle=frame/11*.85;
      const pose=new Float32Array([...ident(),...rot(angle)]);
      const worlds=source.batches.map(()=>pose);
      renderer.renderBatches(worlds);
      if(frame===0)first=pixels();
      if(frame===11)last=pixels();
      for(let i=0;i<source.batches.length;i++){
        const {mesh}=source.batches[i].parsed;
        const actual=renderer.captureIndexedGpuStreams(i,pose);
        const cpu=deformIndexedSkin(mesh,pose).positions;
        const normal=referenceSkinOriginalUnitNormals(
          mesh,source.batches[i].sourceNormals,pose);
        for(let j=0;j<mesh.indices.length;j++){
          const index=mesh.indices[j];
          for(let k=0;k<3;k++){
            maxPositionError=Math.max(maxPositionError,
              Math.abs(actual.positions[j*3+k]-cpu[index*3+k]));
            maxNormalError=Math.max(maxNormalError,
              Math.abs(actual.normals[j*3+k]-normal[index*3+k]));
          }
          const n=Math.hypot(...actual.normals.slice(j*3,j*3+3));
          normalLengths[0]=Math.min(normalLengths[0],n);
          normalLengths[1]=Math.max(normalLengths[1],n);
        }
      }
    }
    let changed=0;
    for(let i=0;i<first.length;i+=4)
      if(Math.abs(first[i]-last[i])+Math.abs(first[i+1]-last[i+1])+
        Math.abs(first[i+2]-last[i+2])>70)changed++;
    const proof=canvas.toDataURL('image/png');
    const report={kind:renderer.kind,frames:renderer.frames,draws:renderer.draws,
      captures:renderer.captures,loaded,first:tally(first),last:tally(last),
      changedPixels:changed,maxPositionError,maxNormalError,
      normalLengths,glError:gl.getError(),sourceAudit:source.audit,
      humanApproved:false,sourceBytes:bytes.length};
    renderer.dispose();
    return {report,proof};
  },Array.from(new Uint8Array(raw)));
  assert.deepEqual(new Uint8Array(raw),unchanged);
  const r=result.report;
  assert.equal(r.frames,12);assert.equal(r.draws,24);
  assert.equal(r.captures,24);assert.equal(r.loaded.textures,2);
  assert.ok(r.first.red>200&&r.first.green>200,'original PNG colours absent');
  assert.ok(r.last.red>200&&r.last.green>200,'moving textured pixels absent');
  assert.ok(r.changedPixels>200,'moving indexed texture did not change framebuffer');
  assert.ok(Math.abs(r.first.greenX-r.last.greenX)>2,
    'GPU-skinned source mesh pixel centroid did not move');
  assert.ok(r.maxPositionError<1e-5&&r.maxNormalError<1e-5,
    'same shader GPU output differs from independent CPU reference');
  assert.ok(r.normalLengths[0]>.999&&r.normalLengths[1]<1.001);
  assert.equal(r.glError,0);assert.deepEqual(errors,[]);
  assert.deepEqual(remote,[]);assert.deepEqual(vendor,[]);
  assert.equal(r.humanApproved,false);
  assert.match(result.proof,/^data:image\/png;base64,/);
  fs.writeFileSync(path.join(output,'moving-original-synthetic-png.png'),
    Buffer.from(result.proof.split(',')[1],'base64'));
  fs.writeFileSync(path.join(output,'gpu-cpu-motion-pixels.json'),
    JSON.stringify({passed:true,...r,remote,vendor,errors},null,2)+'\n');
  console.log(JSON.stringify(r));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
