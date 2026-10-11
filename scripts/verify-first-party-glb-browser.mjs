#!/usr/bin/env node
/** First-party GLB2 synthetic-asset decoding AND actual native WebGL2 triangle proof. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
const PORT=5181,BASE='http://127.0.0.1:'+PORT+'/';
const OUT=path.resolve('reports/browser-smoke/first-party-glb-skinned-data-only');
fs.mkdirSync(OUT,{recursive:true});
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js',
  '--host','127.0.0.1','--port',String(PORT),'--strictPort'],{stdio:'ignore'});
let browser;
async function ready(){
  for(let i=0;i<80;i++){
    if(server.exitCode!==null)throw Error('Local Vite stopped');
    try{if((await fetch(BASE)).ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,250));
  }
  throw new Error('Unable to start headless GLB WebGL2 harness');
}
try{
  await ready();
  browser=await chromium.launch({headless:true,args:[
    '--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'
  ]});
  const page=await browser.newPage({viewport:{width:1280,height:800}});
  const failures=[],vendors=[];
  page.on('pageerror',error=>failures.push(error.message));
  page.on('request',r=>{
    if(/(?:threeRuntimeBoundary|threeSceneBoundary|node_modules\/\.vite\/deps\/three(?:\.js)?(?:\?|$)|react-dom|@react-three)/i.test(r.url()))
      vendors.push(r.url());
  });
  await page.goto(BASE+'native-webgl2-skinning-preview.html',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>{
    const c=document.querySelector('#hgpt-native-skin-canvas');
    return c&&Number(c.dataset.hgptNativeSkinnedFrame)>5;
  },null,{timeout:35000});
  const outcome=await page.evaluate(async()=>{
    const {buildSyntheticFirstPartyGlb}=await import('/tests/support/buildSyntheticFirstPartyGlb.mjs');
    const {parseRestrictedSkinnedGlb}=await import('/src/viewer/firstPartyGlbSkinnedGeometry.mjs');
    const {createNativeIndexedMeshWebGL2,deformIndexedSkin}=await import('/src/viewer/firstPartyIndexedSkinnedMesh.mjs');
    const {validateNativeGLBToRigBinding,packMappedWorldPalette}=await import('/src/viewer/firstPartyGlbRigBindingContract.mjs');
    const sample=buildSyntheticFirstPartyGlb();
    const parsed=parseRestrictedSkinnedGlb(sample);
    const identity=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
    const binding=validateNativeGLBToRigBinding(parsed,{
      allowedCanonicalNames:['upperarm_l','forearm_l'],
      sourceToCanonical:{
        test_upperarm_l:'upperarm_l',
        test_forearm_l:'forearm_l',
      },
      canonicalRestWorldByBone:{
        upperarm_l:identity(),forearm_l:identity(),
      }
    });
    const canvas=document.createElement('canvas');
    canvas.dataset.hgptGLBLoaderProof='first-party';
    canvas.style.width='440px';canvas.style.height='360px';
    canvas.style.position='absolute';canvas.style.right='8px';canvas.style.top='90px';
    canvas.style.border='2px solid #35d1b4';
    document.body.append(canvas);
    const gpu=createNativeIndexedMeshWebGL2(canvas);
    gpu.setSize(440,360,1);
    const mat=(x,y,z)=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1]);
    let displacement=0,initial=null;
    for(let frame=0;frame<18;frame++){
      const t=frame/17;
      const world=packMappedWorldPalette(binding,{
        forearm_l:mat(0,.5*t,0),
        upperarm_l:mat(0,0,0),
      });
      const positioned=deformIndexedSkin(parsed.mesh,world);
      if(initial===null)initial=positioned.positions[1];
      displacement=Math.max(displacement,Math.abs(positioned.positions[1]-initial));
      gpu.render(positioned,{eye:[0,0,3],target:[.4,.4,0],color:[.75,.9,.65]});
    }
    return {
      kind:parsed.kind,
      vertices:parsed.audit.vertices,
      triangles:parsed.audit.indexedTriangles,
      skinNodes:parsed.jointNodeNames,
      canonicalNames:binding.orderedCanonicalBoneNames,
      jointBindingsChecked:binding.verifiedJointCount,
      numericalRestBindResidual:binding.maximumMatrixResidual,
      anatomyMappingAccepted:binding.audit.independentAnatomicalJointCentresAccepted,
      drawFrames:gpu.frameCount,
      displacement:displacement,
      unknownProvenanceAccepted:parsed.audit.sourceProvenanceOrRedistributionApproved,
      trueHumanModelApproved:parsed.audit.originalFullBodyCharacterLoaded,
      bornFirstPartySyntheticFixture:true
    };
  });
  assert.equal(outcome.kind,'hgpt-strict-glb2-skinned-geometry-v1');
  assert.equal(outcome.vertices,3);assert.equal(outcome.triangles,1);
  assert.equal(outcome.drawFrames,18);
  assert.ok(outcome.displacement>.05,'GLB-decoded vertex weights did not deform in browser');
  assert.deepEqual(outcome.skinNodes,['test_upperarm_l','test_forearm_l']);
  assert.deepEqual(outcome.canonicalNames,['upperarm_l','forearm_l']);
  assert.equal(outcome.jointBindingsChecked,2);
  assert.equal(outcome.numericalRestBindResidual,0);
  assert.equal(outcome.anatomyMappingAccepted,false);
  assert.equal(outcome.unknownProvenanceAccepted,false);
  assert.equal(outcome.trueHumanModelApproved,false);
  assert.deepEqual(vendors,[]);
  assert.deepEqual(failures,[]);
  await page.screenshot({path:path.join(OUT,'native-webgl2-synthetic-glb-skinning-proof.png')});
  const output={pass:true,...outcome,vendorModuleRequests:vendors,browserErrors:failures,
    originalCharacterLoaded:false,productionModelApproval:false};
  fs.writeFileSync(path.join(OUT,'glb-parser-browser-proof.json'),JSON.stringify(output,null,2)+'\n');
  console.log(JSON.stringify(output,null,2));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
