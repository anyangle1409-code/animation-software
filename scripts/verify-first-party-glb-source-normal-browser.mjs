#!/usr/bin/env node
/** Real Chromium import/GLB normal-source acceptance; NOT normal GPU skinning. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';
const port=5187,base='http://127.0.0.1:'+port+'/';
const out=path.resolve('reports/browser-smoke/first-party-g1d-source-normals');
fs.mkdirSync(out,{recursive:true});
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js',
  '--host','127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});
let browser;
try{
  let running=false;
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw Error('Browser test server exited');
    try{if((await fetch(base)).ok){running=true;break;}}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  assert.equal(running,true,'Browser test server never ready');
  browser=await chromium.launch({headless:true,args:[
    '--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'
  ]});
  const page=await browser.newPage();
  const errors=[],vendors=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',req=>{
    if(/threeRuntimeBoundary|node_modules\/\.vite\/deps\/three(?:\.js)?(?:\?|$)|react-dom|@react-three/.test(req.url()))
      vendors.push(req.url());
  });
  await page.goto(base+'native-webgl2-skinning-preview.html',{waitUntil:'domcontentloaded'});
  const probe=await page.evaluate(async()=>{
    const {buildSyntheticSourceNormalGLB}=
      await import('/tests/support/buildSyntheticSourceNormalGlb.mjs');
    const {parseRestrictedBatchedSkinnedGlb}=
      await import('/src/viewer/firstPartyGlbSkinnedBatches.mjs');
    const {validateNativeGLBToRigBinding,packMappedWorldPalette}=
      await import('/src/viewer/firstPartyGlbRigBindingContract.mjs');
    const {deformIndexedSkin}=
      await import('/src/viewer/firstPartyIndexedSkinnedMesh.mjs');
    const glb=buildSyntheticSourceNormalGLB({meshCount:2,primitivesPerMesh:2});
    const r=parseRestrictedBatchedSkinnedGlb(glb,{
      allowSourceNormals:true,allowSourceUV0:true
    });
    const id=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
    const sourceNormalSignature=[];
    const sourceBindErrors=[];
    const triangleCounts=[];
    for(const item of r.batches){
      const contract=validateNativeGLBToRigBinding(item.parsed,{
        sourceToCanonical:{test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
        allowedCanonicalNames:['upperarm_l','forearm_l'],
        canonicalRestWorldByBone:{upperarm_l:id(),forearm_l:id()}
      });
      const palette=packMappedWorldPalette(contract,{
        upperarm_l:id(),forearm_l:id()
      });
      triangleCounts.push(deformIndexedSkin(item.parsed.mesh,palette).triangleCount);
      sourceBindErrors.push(contract.maximumMatrixResidual);
      sourceNormalSignature.push([...item.sourceNormals.slice(0,3)]);
    }
    return {
      originalGLBBytes:glb.byteLength,
      decodedSourceNormalPrimitives:r.batches.length,
      sourceNormalSignature,
      exactJointBindResiduals:sourceBindErrors,
      triangleCounts,
      glTFNormalsFetchedFromExternalAsset:false,
      sourceNormalValuesAccepted:r.audit.originalUnitLengthSourceNormalsValidated,
      sourceNormalGpuSkinningImplemented:r.audit.sourceNormalsGPUSkinned,
      realOriginalHumanModelRendered:r.audit.actualOriginalHumanMeshUsed,
      noThirdPartySkinningCode:r.audit.noExternalModelCodeUsed
    };
  });
  assert.equal(probe.decodedSourceNormalPrimitives,4);
  assert.deepEqual(probe.sourceNormalSignature,[
    [0,0,1],[0,1,0],[0,1,0],[0,0,1]
  ]);
  assert.deepEqual(probe.exactJointBindResiduals,[0,0,0,0]);
  assert.deepEqual(probe.triangleCounts,[1,1,1,1]);
  assert.equal(probe.sourceNormalValuesAccepted,true);
  assert.equal(probe.sourceNormalGpuSkinningImplemented,false);
  assert.equal(probe.realOriginalHumanModelRendered,false);
  assert.deepEqual(errors,[]);
  assert.deepEqual(vendors,[]);
  const report={passed:true,...probe,browserErrors:errors,vendorRequests:vendors};
  fs.writeFileSync(path.join(out,'g1d-source-normal-real-chromium.json'),
    JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
