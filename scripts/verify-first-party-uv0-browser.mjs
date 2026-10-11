#!/usr/bin/env node
/** G1c actual browser/GL2 source TEXCOORD_0 → fragment UV interpolation proof.
 * Synthetic project-authored triangle geometry only. No real skin or texture.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';
const port=5184,base='http://127.0.0.1:'+port+'/';
const dir=path.resolve('reports/browser-smoke/first-party-g1c-uv0');
fs.mkdirSync(dir,{recursive:true});
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js',
  '--host','127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});
let browser;
async function ready(){
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw new Error('Vite source UV0 diagnostic server stopped');
    try{if((await fetch(base)).ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  throw new Error('UV0 diagnostic browser server did not start');
}
try{
  await ready();
  browser=await chromium.launch({headless:true,
    args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
  const page=await browser.newPage({viewport:{width:1280,height:900}});
  const pageErrors=[],vendorRequests=[],gpuConsoleErrors=[];
  page.on('pageerror',error=>pageErrors.push(error.message));
  page.on('console',msg=>{
    if(msg.type()==='error')gpuConsoleErrors.push(msg.text());
  });
  page.on('request',req=>{
    if(/(?:threeRuntimeBoundary|threeSceneBoundary|node_modules\/\.vite\/deps\/three(?:\.js)?(?:\?|$)|react-dom|@react-three)/i.test(req.url()))
      vendorRequests.push(req.url());
  });
  await page.goto(base+'native-webgl2-skinning-preview.html',
    {waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>{
    const c=document.querySelector('#hgpt-native-skin-canvas');
    return c&&Number(c.dataset.hgptNativeSkinnedFrame)>=5;
  },null,{timeout:35000});
  const result=await page.evaluate(async()=>{
    const {buildSyntheticUV0Glb}=
      await import('/tests/support/buildSyntheticUV0Glb.mjs');
    const {parseRestrictedBatchedSkinnedGlb}=
      await import('/src/viewer/firstPartyGlbSkinnedBatches.mjs');
    const {deformIndexedSkin}=
      await import('/src/viewer/firstPartyIndexedSkinnedMesh.mjs');
    const {validateNativeGLBToRigBinding,packMappedWorldPalette}=
      await import('/src/viewer/firstPartyGlbRigBindingContract.mjs');
    const {createNativeUV0WebGL2}=
      await import('/src/viewer/firstPartyUV0WebGL2.mjs');
    const input=buildSyntheticUV0Glb({meshCount:2,primitivesPerMesh:1});
    const source=parseRestrictedBatchedSkinnedGlb(input,{allowSourceUV0:true});
    const canvas=document.createElement('canvas');
    canvas.id='hgpt-firstparty-uv0-shader';
    canvas.style.position='absolute';
    canvas.style.left='8px';canvas.style.top='120px';
    canvas.style.width='960px';canvas.style.height='540px';
    canvas.style.border='2px solid white';
    document.body.append(canvas);
    const gpu=createNativeUV0WebGL2(canvas);
    gpu.setSize(960,540,1);
    const ident=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
    const trans=y=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,y,0,1]);
    const bindings=source.batches.map(({parsed})=>
      validateNativeGLBToRigBinding(parsed,{
        sourceToCanonical:{test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
        allowedCanonicalNames:['upperarm_l','forearm_l'],
        canonicalRestWorldByBone:{upperarm_l:ident(),forearm_l:ident()},
      }));
    const initialUV0=source.batches[0].sourceUV0.slice();
    let firstVertex=null,maxSkinMotion=0;
    for(let f=0;f<20;f++){
      const frac=f/19;
      const parts=source.batches.map(({parsed,sourceUV0},i)=>{
        const palette=packMappedWorldPalette(bindings[i],{
          upperarm_l:ident(),forearm_l:trans(frac*.5)
        });
        const posed=deformIndexedSkin(parsed.mesh,palette);
        if(i===0){
          if(firstVertex===null)firstVertex=posed.positions[1];
          maxSkinMotion=Math.max(maxSkinMotion,
            Math.abs(posed.positions[1]-firstVertex));
        }
        return {positions:posed.positions,indices:posed.indices,uv0:sourceUV0};
      });
      gpu.renderBatches(parts,{eye:[1,0.5,6.2],target:[1.25,.5,0]});
    }
    const gl=canvas.getContext('webgl2');
    const bytes=new Uint8Array(canvas.width*canvas.height*4);
    gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,bytes);
    let redUVPixels=0,greenUVPixels=0;
    for(let i=0;i<bytes.length;i+=4){
      const red=bytes[i],green=bytes[i+1];
      if(red>80&&red>green*2.5)redUVPixels++;
      if(green>80&&green>red*2.5)greenUVPixels++;
    }
    return {
      sourceGLBBytes:input.byteLength,
      decodedMeshes:source.audit.numberOfMeshes,
      decodedPrimitives:source.audit.numberOfPrimitives,
      uv0SourceValidated:source.audit.sourceUV0CoordinatesValidated,
      sourceTextureSamplingImplemented:source.audit.textureSamplingImplemented,
      sourceUV0Pair:[
        [...source.batches[0].sourceUV0.slice(0,2)],
        [...source.batches[1].sourceUV0.slice(0,2)]
      ],
      uv0RemainedUnmodified:firstVertex!==null &&
        initialUV0.every((v,i)=>v===source.batches[0].sourceUV0[i]),
      GPUKind:gpu.kind,
      frames:gpu.frameCount,
      actualIndexedDrawCalls:gpu.drawCallCount,
      sourceSkinMotion:maxSkinMotion,
      redUVPixels,greenUVPixels,
      framebuffer:[canvas.width,canvas.height],
      originalHumanModelAccepted:source.audit.actualOriginalHumanMeshUsed,
      actualTextureSampling:false
    };
  });
  assert.equal(result.decodedMeshes,2);
  assert.equal(result.decodedPrimitives,2);
  assert.equal(result.uv0SourceValidated,true);
  assert.equal(result.sourceTextureSamplingImplemented,false);
  assert.equal(result.uv0RemainedUnmodified,true);
  assert.equal(result.GPUKind,'hgpt-native-webgl2-uv0-diagnostic-v1');
  assert.equal(result.frames,20);
  assert.equal(result.actualIndexedDrawCalls,40);
  assert.ok(result.sourceSkinMotion>.12);
  assert.ok(result.redUVPixels>500,'Actual GPU source TEXCOORD_0 red-fragment region invisible');
  assert.ok(result.greenUVPixels>500,'Actual GPU source TEXCOORD_0 green-fragment region invisible');
  assert.deepEqual(result.framebuffer,[960,540]);
  assert.equal(result.originalHumanModelAccepted,false);
  assert.deepEqual(pageErrors,[]);
  assert.deepEqual(gpuConsoleErrors,[]);
  assert.deepEqual(vendorRequests,[]);
  await page.screenshot({path:path.join(dir,'original-uv0-native-gpu-synthetic-proof.png')});
  const output={
    passed:true,...result,browserErrors:pageErrors,
    gpuConsoleErrors,vendorRequests,
    syntheticTriangleUV0Only:true,
    noImageTextureAssetsUsed:true,
    approvedHumanModelRendered:false,
    normalStudioThreeDependencyRemoved:false
  };
  fs.writeFileSync(path.join(dir,'native-uv0-synthetic-proof.json'),
    JSON.stringify(output,null,2)+'\n');
  console.log(JSON.stringify(output,null,2));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
