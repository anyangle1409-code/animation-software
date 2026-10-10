#!/usr/bin/env node
/** Real-browser zero-Three entry proof for first-party CPU skinned indexed mesh. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
const PORT=5180,BASE='http://127.0.0.1:'+PORT+'/';
const OUT=path.resolve('reports/browser-smoke/first-party-native-indexed-skinned-mesh');
fs.mkdirSync(OUT,{recursive:true});
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js',
  '--host','127.0.0.1','--port',String(PORT),'--strictPort'],
  {stdio:['ignore','pipe','pipe']});
let browser,finished=false;
async function ready(){
  for(let i=0;i<80;i++){
    if(server.exitCode!==null)throw new Error('Local Vite exited early');
    try{if((await fetch(BASE)).ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,250));
  }
  throw new Error('Unable to start local isolated renderer test server');
}
try{
  await ready();
  browser=await chromium.launch({headless:true,args:[
    '--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'
  ]});
  const page=await browser.newPage({viewport:{width:1280,height:800},deviceScaleFactor:1});
  const pageErrors=[],vendorRequests=[],webGLFailures=[];
  page.on('pageerror',e=>pageErrors.push(e.message));
  page.on('console',msg=>{if(msg.type()==='error')webGLFailures.push(msg.text())});
  page.on('request',request=>{
    if(/(?:threeRuntimeBoundary|threeSceneBoundary|node_modules\/\.vite\/deps\/three(?:\.js)?(?:\?|$)|react-dom|@react-three)/i.test(request.url()))
      vendorRequests.push(request.url());
  });
  await page.goto(BASE+'native-webgl2-skinning-preview.html',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>{
    const canvas=document.querySelector('#hgpt-native-skin-canvas');
    return canvas && canvas.dataset.hgptNativeSkinned==='true'
      && Number(canvas.dataset.hgptNativeSkinnedFrame)>=5
      && Number(canvas.dataset.hgptNativeSkinnedTriangles)>100;
  },null,{timeout:35000});
  await page.waitForFunction(()=>{
    const canvas=document.querySelector('#hgpt-native-skin-canvas');
    return Number(canvas?.dataset.hgptNativeSkinnedMotion||0)>.005;
  },null,{timeout:20000});
  const result=await page.evaluate(()=>{
    const canvas=document.querySelector('#hgpt-native-skin-canvas');
    const description=document.querySelector('#hgpt-native-skin-description')?.textContent;
    return {
      nativeRenderer:canvas.dataset.hgptNativeSkinnedRenderer,
      nativeActualExercise:canvas.dataset.hgptNativeExercise,
      skinnedFrameCount:Number(canvas.dataset.hgptNativeSkinnedFrame),
      poseMotionMeters:Number(canvas.dataset.hgptNativeSkinnedMotion),
      triangles:Number(canvas.dataset.hgptNativeSkinnedTriangles),
      meshTriangles:Number(canvas.dataset.hgptNativeMeshTriangles),
      canvas:[canvas.width,canvas.height],
      noThirdPartyDiagnostic:canvas.dataset.hgptNativeThirdPartyModules==='none',
      description,
    };
  });
  assert.equal(result.nativeRenderer,'hgpt-native-webgl2-indexed-cpu-lbs-v1');
  assert.equal(result.nativeActualExercise,'dumbbell_bicep_curl');
  assert.ok(result.skinnedFrameCount>=5);
  assert.ok(result.triangles>100 && result.meshTriangles>100);
  assert.ok(result.poseMotionMeters>.005);
  assert.ok(result.canvas[0]>0 && result.canvas[1]>0);
  assert.ok(result.noThirdPartyDiagnostic);
  assert.deepEqual(vendorRequests,[],'Unexpected third-party Three/React module fetched');
  assert.deepEqual(pageErrors,[],'Browser runtime error');
  assert.deepEqual(webGLFailures,[],'GPU browser console error');
  await page.screenshot({path:path.join(OUT,'original-webgl2-two-bone-indexed-mesh-diagnostic.png')});
  const output={
    pass:true,rendering_source:'first-party actual WebGL2 indexed TRIANGLES',
    skinning:'first-party CPU 4-weight LBS (prototype reference)',
    tested_in:'real Chromium headless with software WebGL2',
    source_runtime_vendors_loaded:vendorRequests.length,
    shape_is_original_procedural_two_bone_proxy:true,
    realistic_flesh_mesh_rendered:false,
    production_glb_compatibility_verified:false,
    model_anatomy_accepted:false,
    ...result,pageErrors,webGLFailures,vendorRequests
  };
  fs.writeFileSync(path.join(OUT,'native-indexed-skin-browser-proof.json'),
    JSON.stringify(output,null,2)+'\n');
  console.log(JSON.stringify(output,null,2));
  finished=true;
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
if(!finished)process.exitCode=1;
