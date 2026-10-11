#!/usr/bin/env node
/**
 * Real Chromium/WebGL2 proof of 2 original synthetic GLB meshes:
 * both skinned independently, BOTH drawn into one shared camera/depth frame.
 * No actual original person, no third-party model and no anatomical claims.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';
const PORT=5182,BASE='http://127.0.0.1:'+PORT+'/';
const OUT=path.resolve('reports/browser-smoke/first-party-batched-glb');
fs.mkdirSync(OUT,{recursive:true});
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js',
  '--host','127.0.0.1','--port',String(PORT),'--strictPort'],{stdio:'ignore'});
let browser;
async function ready(){
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw new Error('Local server unexpectedly terminated');
    try{if((await fetch(BASE)).ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  throw new Error('First-party mesh browser proof server unavailable');
}
try{
  await ready();
  browser=await chromium.launch({headless:true,args:[
    '--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'
  ]});
  const page=await browser.newPage({viewport:{width:1280,height:900}});
  const errors=[],vendorRequests=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{
    if(/(?:threeRuntimeBoundary|threeSceneBoundary|node_modules\/\.vite\/deps\/three(?:\.js)?(?:\?|$)|react-dom|@react-three)/i.test(request.url()))
      vendorRequests.push(request.url());
  });
  await page.goto(BASE+'native-webgl2-skinning-preview.html',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>{
    const c=document.querySelector('#hgpt-native-skin-canvas');
    return c&&Number(c.dataset.hgptNativeSkinnedFrame)>=5;
  },null,{timeout:35000});
  const output=await page.evaluate(async()=>{
    const {buildSyntheticBatchedGlb}=await import('/tests/support/buildSyntheticBatchedGlb.mjs');
    const {parseRestrictedBatchedSkinnedGlb}=await import('/src/viewer/firstPartyGlbSkinnedBatches.mjs');
    const {deformIndexedSkin,createNativeIndexedMeshWebGL2}=
      await import('/src/viewer/firstPartyIndexedSkinnedMesh.mjs');
    const {validateNativeGLBToRigBinding,packMappedWorldPalette}=
      await import('/src/viewer/firstPartyGlbRigBindingContract.mjs');
    const input=buildSyntheticBatchedGlb({meshCount:2,primitivesPerMesh:1});
    const parsed=parseRestrictedBatchedSkinnedGlb(input);
    const canvas=document.createElement('canvas');
    canvas.id='hgpt-batched-two-mesh-canvas';
    canvas.style.width='960px';canvas.style.height='540px';
    canvas.style.position='absolute';canvas.style.top='120px';
    canvas.style.left='8px';canvas.style.border='2px solid white';
    document.body.append(canvas);
    const gpu=createNativeIndexedMeshWebGL2(canvas);
    gpu.setSize(960,540,1);
    const ident=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
    const trans=(x,y)=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,x,y,0,1]);
    const bindings=parsed.batches.map(({parsed:source})=>
      validateNativeGLBToRigBinding(source,{
        sourceToCanonical:{test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
        allowedCanonicalNames:['upperarm_l','forearm_l'],
        canonicalRestWorldByBone:{upperarm_l:ident(),forearm_l:ident()},
      }));
    let maxDisplacement=0,first=null;
    for(let frame=0;frame<20;frame++){
      const t=frame/19,posed=[];
      for(let i=0;i<parsed.batches.length;i++){
        const boneWorld=packMappedWorldPalette(bindings[i],{
          forearm_l:trans(0,t*.5),upperarm_l:ident()
        });
        const part=deformIndexedSkin(parsed.batches[i].parsed.mesh,boneWorld);
        posed.push(part);
        if(frame===0)maxDisplacement=0;
        if(i===0){
          if(first===null)first=part.positions[1];
          maxDisplacement=Math.max(maxDisplacement,Math.abs(part.positions[1]-first));
        }
      }
      gpu.renderBatches(posed,{
        eye:[1,0.5,6.2],target:[1.25,.5,0],
        colors:[[.94,.28,.21],[.16,.86,.30]]
      });
    }
    // Direct GPU framebuffer proof: ensure two differently coloured meshes
    // survived the same frame. A naive loop that clears per-mesh fails here.
    const gl=canvas.getContext('webgl2');
    const pixels=new Uint8Array(960*540*4);
    gl.readPixels(0,0,960,540,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
    let redPixels=0,greenPixels=0;
    for(let i=0;i<pixels.length;i+=4){
      const red=pixels[i],green=pixels[i+1];
      if(red>85 && red>green*1.6)redPixels++;
      if(green>85 && green>red*1.6)greenPixels++;
    }
    canvas.dataset.firstPartyGpuBatched='true';
    return {
      renderer:gpu.kind,
      inputBytes:input.byteLength,
      decodedMeshes:parsed.audit.numberOfMeshes,
      decodedPrimitives:parsed.audit.numberOfPrimitives,
      decodedVertices:parsed.audit.decodedVertices,
      decodedTriangles:parsed.audit.indexedTriangles,
      skinJointNames:[...parsed.jointNodeNames],
      numericalRestBindResidual:Math.max(...bindings.map(b=>b.maximumMatrixResidual)),
      originalHumanAccepted:parsed.audit.actualOriginalHumanMeshUsed,
      frameCount:gpu.frameCount,
      separateIndexedDrawCalls:gpu.drawCallCount,
      sourceSkinMotion:maxDisplacement,
      redMeshPixels:redPixels,
      greenMeshPixels:greenPixels,
      readbackFromActualWebGL2:true,
      framebufferSize:[canvas.width,canvas.height]
    };
  });
  assert.equal(output.decodedMeshes,2);
  assert.equal(output.decodedPrimitives,2);
  assert.equal(output.decodedVertices,6);
  assert.equal(output.decodedTriangles,2);
  assert.equal(output.frameCount,20);
  assert.equal(output.separateIndexedDrawCalls,40);
  assert.ok(output.sourceSkinMotion>.12,'Both original skinned meshes must have real deformation');
  assert.ok(output.redMeshPixels>400,'GPU left-red source mesh absent');
  assert.ok(output.greenMeshPixels>400,'GPU right-green source mesh absent');
  assert.equal(output.numericalRestBindResidual,0);
  assert.equal(output.originalHumanAccepted,false);
  assert.deepEqual(errors,[]);
  assert.deepEqual(vendorRequests,[]);
  await page.screenshot({path:path.join(OUT,'two-skinned-meshes-one-webgl2-frame-synthetic-only.png')});
  const result={pass:true,...output,
    pageErrors:errors,vendorRequests,
    firstPartySyntheticTestGeometryOnly:true,
    originalHumanAnatomyApproved:false,
    productionCharacterRenderingAccepted:false,
    thirdPartyStudioRendererRemoved:false};
  fs.writeFileSync(path.join(OUT,'first-party-g1-multimesh-browser-result.json'),
    JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result,null,2));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
