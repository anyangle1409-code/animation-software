#!/usr/bin/env node
/**
 * G2c Chromium GPU skinned source-normal transform-feedback parity + one
 * shared depth-frame Lambert diagnostic, with absolutely no human assets.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';
const port=5188,base='http://127.0.0.1:'+port+'/';
const out=path.resolve('reports/browser-smoke/first-party-g2c-skinned-normals');
fs.mkdirSync(out,{recursive:true});
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js',
  '--host','127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});
let browser;
try{
  let up=false;
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw Error('G2c local source server exited');
    try{if((await fetch(base)).ok){up=true;break;}}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  assert.ok(up,'G2c browser source server unavailable');
  browser=await chromium.launch({headless:true,args:[
    '--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'
  ]});
  const page=await browser.newPage({viewport:{width:1280,height:900}});
  const errors=[],consoleErrors=[],vendorRequests=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
  page.on('request',r=>{
    if(/threeRuntimeBoundary|threeSceneBoundary|node_modules\/\.vite\/deps\/three(?:\.js)?(?:\?|$)|react-dom|@react-three/.test(r.url()))
      vendorRequests.push(r.url());
  });
  await page.goto(base+'native-webgl2-skinning-preview.html',{waitUntil:'domcontentloaded'});
  const result=await page.evaluate(async()=>{
    const {buildSyntheticSourceNormalGLB}=
      await import('/tests/support/buildSyntheticSourceNormalGlb.mjs');
    const {parseRestrictedBatchedSkinnedGlb}=
      await import('/src/viewer/firstPartyGlbSkinnedBatches.mjs');
    const {referenceSkinOriginalUnitNormals}=
      await import('/src/viewer/firstPartySkinnedNormalReference.mjs');
    const {createNativePaletteSkinnedWebGL2}=
      await import('/src/viewer/firstPartyGpuPaletteSkinning.mjs');
    const {validateNativeGLBToRigBinding,packMappedWorldPalette}=
      await import('/src/viewer/firstPartyGlbRigBindingContract.mjs');
    const bytes=buildSyntheticSourceNormalGLB();
    const batch=parseRestrictedBatchedSkinnedGlb(bytes,{
      allowSourceNormals:true,allowSourceUV0:true
    });
    const canvas=document.createElement('canvas');
    canvas.id='first-party-g2c-gpu-skinned-unit-normal-probe';
    canvas.style.position='absolute';
    canvas.style.left='8px';canvas.style.top='120px';
    canvas.style.width='960px';canvas.style.height='540px';
    canvas.style.border='2px solid white';
    document.body.append(canvas);
    const gpu=createNativePaletteSkinnedWebGL2(canvas);
    gpu.setSize(960,540,1);
    const ident=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
    const rotateX=a=>{
      const c=Math.cos(a),s=Math.sin(a);
      return new Float32Array([1,0,0,0,0,c,s,0,0,-s,c,0,0,0,0,1]);
    };
    const validated=batch.batches.map(({parsed})=>
      validateNativeGLBToRigBinding(parsed,{
        sourceToCanonical:{test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
        allowedCanonicalNames:['upperarm_l','forearm_l'],
        canonicalRestWorldByBone:{upperarm_l:ident(),forearm_l:ident()}
      }));
    let maxNormalAbsError=0,maxPositionAbsError=0;
    let minNormalLength=Infinity,maxNormalLength=0;
    for(let frame=0;frame<20;frame++){
      const t=frame/19;
      const parts=batch.batches.map(({parsed,sourceUV0,sourceNormals},i)=>({
        mesh:parsed.mesh,uv0:sourceUV0,sourceNormals,
        posedWorld:packMappedWorldPalette(validated[i],{
          upperarm_l:ident(),forearm_l:rotateX(.6*t)
        })
      }));
      gpu.renderBatches(parts,{normalPreview:true});
      for(const p of parts){
        const actual=gpu.captureIndexedSkinnedNormals(p);
        const cpu=referenceSkinOriginalUnitNormals(p.mesh,p.sourceNormals,p.posedWorld);
        for(let i=0;i<p.mesh.indices.length;i++)for(let k=0;k<3;k++){
          const idx=p.mesh.indices[i];
          maxNormalAbsError=Math.max(maxNormalAbsError,
            Math.abs(actual[i*3+k]-cpu[idx*3+k]));
        }
        for(let i=0;i<actual.length;i+=3){
          const len=Math.hypot(...actual.slice(i,i+3));
          minNormalLength=Math.min(minNormalLength,len);
          maxNormalLength=Math.max(maxNormalLength,len);
        }
      }
    }
    // Test all FOUR nonzero skin influences INCLUDING late bone 127.
    const bind=new Float32Array(128*16),world=new Float32Array(128*16);
    for(let i=0;i<128;i++){bind.set(ident(),16*i);world.set(ident(),16*i);}
    world.set(rotateX(.25),31*16);
    world.set(rotateX(-.38),64*16);
    world.set(rotateX(.78),127*16);
    const m={
      positions:new Float32Array([0,0,0,1,0,0,0,1,0]),
      indices:new Uint16Array([0,1,2]),
      jointIndices:new Uint16Array([...Array(3)].flatMap(()=>[0,31,64,127])),
      weights:new Float32Array([...Array(3)].flatMap(()=>[.1,.2,.3,.4])),
      inverseBindMatrices:bind
    };
    const normals=new Float32Array([0,1,0,0,1,0,0,1,0]);
    const farPart={mesh:m,sourceNormals:normals,
      uv0:new Float32Array([.1,.1,.9,.1,.1,.9]),
      posedWorld:world};
    const farGPU=gpu.captureIndexedSkinnedNormals(farPart);
    const farCPU=referenceSkinOriginalUnitNormals(m,normals,world);
    for(let i=0;i<m.indices.length;i++)for(let j=0;j<3;j++){
      const idx=m.indices[i];
      maxPositionAbsError=Math.max(maxPositionAbsError,
        Math.abs(farGPU[i*3+j]-farCPU[idx*3+j]));
    }
    const gl=canvas.getContext('webgl2');
    const pixelBytes=new Uint8Array(canvas.width*canvas.height*4);
    gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,pixelBytes);
    let brightZ=0,midY=0;
    for(let i=0;i<pixelBytes.length;i+=4){
      const r=pixelBytes[i],g=pixelBytes[i+1],b=pixelBytes[i+2];
      if(Math.abs(r-g)>3||Math.abs(g-b)>3)continue;
      if(r>166)brightZ++;
      if(r>=100&&r<160)midY++;
    }
    return {
      gpuKind:gpu.kind,
      sourceNormalPrimitives:batch.batches.length,
      sourceNormalAudit:batch.audit.originalUnitLengthSourceNormalsValidated,
      frames:gpu.frameCount,
      indexedGpuDraws:gpu.drawCallCount,
      actualTransformFeedbackTriangles:gpu.capturedTriangleCount,
      maxNormalAbsError,
      max128BoneFourWeightNormalAbsError:maxPositionAbsError,
      minGpuNormalLength:minNormalLength,
      maxGpuNormalLength:maxNormalLength,
      lambertBrightZPixels:brightZ,
      lambertMidYPixels:midY,
      glError:gl.getError(),
      noAnatomicalOriginalMaleModel:true,
      sourceNormalGPUSkinningDiagnosticsOnly:true,
      imageTextureOrPhysicalPBRNotImplemented:true,
      retainedProductionThree:true
    };
  });
  console.log('G2C_NORMAL_DEBUG',JSON.stringify(result));
  assert.equal(result.sourceNormalPrimitives,2);
  assert.equal(result.sourceNormalAudit,true);
  assert.equal(result.frames,20);
  assert.equal(result.indexedGpuDraws,40);
  assert.equal(result.actualTransformFeedbackTriangles,41);
  assert.ok(result.maxNormalAbsError<1e-5,'GPU NORMAL output differs from CPU reference');
  assert.ok(result.max128BoneFourWeightNormalAbsError<1e-5,'late palette index normal GPU error');
  assert.ok(result.minGpuNormalLength>.999&&result.maxGpuNormalLength<1.001);
  assert.ok(result.lambertBrightZPixels>400,'GPU +Z Lambert diagnostic mesh missing');
  assert.ok(result.lambertMidYPixels>400,'GPU +Y Lambert diagnostic mesh missing');
  assert.equal(result.glError,0);
  assert.deepEqual(errors,[]);assert.deepEqual(consoleErrors,[]);
  assert.deepEqual(vendorRequests,[]);
  await page.screenshot({path:path.join(out,'g2c-source-normal-lambert-gpu-synthetic.png')});
  const report={pass:true,...result,browserErrors:errors,consoleErrors,vendorRequests};
  fs.writeFileSync(path.join(out,'g2c-gpu-normal-lbs-parity.json'),
    JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
