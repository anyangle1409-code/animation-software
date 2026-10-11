#!/usr/bin/env node
/**
 * G4e REAL BROWSER INTEGRATION: verified source GLB SHA + rig/rest mapping +
 * original PNG/material/UV + GPU moving 4-weight indexed triangle shader.
 * Synthetic 2-joint source GLB test fixture, NOT human anatomy/real model.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';
import {buildSyntheticTexturedBatchedGlb}
  from '../tests/support/buildSyntheticTexturedBatchedGlb.mjs';

const port=5209,base='http://127.0.0.1:'+port+'/';
const output=path.resolve('reports/browser-smoke/first-party-g4e-real-glb-handoff');
fs.mkdirSync(output,{recursive:true});
const source=buildSyntheticTexturedBatchedGlb();
const originalBytes=Array.from(new Uint8Array(source));
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js',
  '--host','127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});
let browser;
async function ready(){
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw new Error('Original shader test Vite server exited');
    try{if((await fetch(base)).ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  throw new Error('First-party browser GLB test server not ready');
}
try{
  await ready();
  browser=await chromium.launch({headless:true,
    args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
  const page=await browser.newPage({viewport:{width:1100,height:700}});
  const exceptions=[],otherRequests=[];
  page.on('pageerror',e=>exceptions.push(e.message));
  page.on('request',r=>{
    const url=r.url();
    if(!url.startsWith(base)&&!url.startsWith('data:')&&!url.startsWith('blob:'))
      otherRequests.push(url);
  });
  await page.goto(base);
  const result=await page.evaluate(async raw=>{
    const {HGPT_PROTOTYPE_HANDOFF_KIND,digestOriginalGlbSha256,
      validateProvisionalModelHandoff,packProvisionalModelPose}
      =await import('/src/viewer/firstPartyPrototypeModelHandoff.mjs');
    const {createNativePaletteSkinnedWebGL2}
      =await import('/src/viewer/firstPartyGpuPaletteSkinning.mjs');
    const GLB=new Uint8Array(raw).buffer;
    const SHA=await digestOriginalGlbSha256(GLB);
    const identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
    const manifest={
      kind:HGPT_PROTOTYPE_HANDOFF_KIND,
      candidateId:'G4EOriginalSyntheticTestModel',
      status:'PROTOTYPE_ONLY',
      glb:{sha256:SHA,layout:'batched',sourceFeatures:{
        flatColors:true,uv0:true,normals:false,
        embeddedPngBaseColor:true,
      }},
      frame:{unit:'metre',up:'Y',handedness:'right',
        basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
      rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
        thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
      rig:{sourceToRuntimeBone:{
        test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
        runtimeBoneNames:['upperarm_l','forearm_l'],
        restWorldByRuntimeBone:{upperarm_l:identity,forearm_l:identity},
        lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED'},
      releaseApproved:false,
    };
    const verified=await validateProvisionalModelHandoff(GLB,manifest);
    const canvas=document.createElement('canvas');
    document.body.appendChild(canvas);
    const engine=createNativePaletteSkinnedWebGL2(canvas);
    engine.setSize(960,540);
    const sourceBatches=verified.scene.batches;
    const images=await engine.setSourcePngBatches(sourceBatches,
      {colorSpace:'gltf-srgb'});
    const pose=(x)=>{
      const upper=identity.slice(),fore=identity.slice();
      upper[12]=x;fore[12]=x*.35;
      return packProvisionalModelPose(verified,{
        upperarm_l:upper,forearm_l:fore
      });
    };
    const parts=sourceBatches.map(b=>({
      mesh:b.parsed.mesh,uv0:b.sourceUV0,posedWorld:pose(0)
    }));
    const camera={eye:[1.1,.45,4.5],target:[1.1,.45,0],
      texturePreview:true,colorManagedTexturePreview:true};
    const gl=canvas.getContext('webgl2');
    function measure(){
      const pixels=new Uint8Array(canvas.width*canvas.height*4);
      gl.readPixels(0,0,canvas.width,canvas.height,
        gl.RGBA,gl.UNSIGNED_BYTE,pixels);
      let red=0,green=0,redSum=0,greenSum=0;
      for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++){
        const p=(y*canvas.width+x)*4;
        const R=pixels[p],G=pixels[p+1],B=pixels[p+2];
        if(R>140&&R>G*2.5&&R>B*2.5){red++;redSum+=x}
        if(G>140&&G>R*2.5&&G>B*2.5){green++;greenSum+=x}
      }
      return {red,green,
        redX:red?redSum/red:0,
        greenX:green?greenSum/green:0};
    }
    engine.renderBatches(parts,camera);
    const initial=measure();
    for(let k=1;k<=12;k++){
      for(const part of parts)part.posedWorld=pose(.4*k/12);
      engine.renderBatches(parts,camera);
    }
    const moved=measure();
    const pixels=canvas.toDataURL('image/png');
    const report={
      sourceGLBSha256:verified.sourceSha256,
      sourcePngValidated:verified.audit.sourceEmbeddedPngBaseColorValidated,
      sourceBindingValidated:verified.audit.allGLBPrimitivesDecodedAndBound,
      imageCount:images.textures,
      partCount:sourceBatches.length,
      frames:engine.frameCount,
      draws:engine.drawCallCount,
      initial,moved,
      shiftedRedX:moved.redX-initial.redX,
      shiftedGreenX:moved.greenX-initial.greenX,
      error:gl.getError(),
      anatomicalApproval:verified.audit.medicallyApprovedHumanSkeleton,
      sourceRightsApproval:verified.audit.independentlyVerifiedSourceRights,
      productionReady:verified.audit.modelProductionReady,
      previewHumanRealismApproved:false,
    };
    engine.dispose();
    return {...report,screenshot:pixels};
  },originalBytes);
  assert.equal(result.sourcePngValidated,true);
  assert.equal(result.sourceBindingValidated,true);
  assert.equal(result.imageCount,2);
  assert.equal(result.partCount,2);
  assert.equal(result.frames,13);
  assert.equal(result.draws,26);
  assert.ok(result.initial.red>300&&result.initial.green>300,
    'Original model image data not visible at rest');
  assert.ok(result.moved.red>300&&result.moved.green>300,
    'Original source PNG colours missing after bone motion');
  assert.ok(result.shiftedRedX>20&&result.shiftedGreenX>20,
    'Original GLB materials did not move with skinned joint palette');
  assert.equal(result.error,0);
  assert.equal(result.anatomicalApproval,false);
  assert.equal(result.sourceRightsApproval,false);
  assert.equal(result.productionReady,false);
  assert.deepEqual(exceptions,[]);
  assert.deepEqual(otherRequests,[]);
  assert.match(result.screenshot,/^data:image\/png;base64,/);
  const image=Buffer.from(result.screenshot.slice('data:image/png;base64,'.length),
    'base64');
  assert.ok(image.length>1024);
  fs.writeFileSync(path.join(output,'g4e-source-rig-srgb-gpu-frame.png'),image);
  const {screenshot,...safe}=result;
  fs.writeFileSync(path.join(output,'source-textured-model-import-gpu-proof.json'),
    JSON.stringify({success:true,syntheticOnly:true,
      actualWorkHumanNotAvailable:true,...safe},null,2)+'\n');
  console.log(JSON.stringify(safe));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
