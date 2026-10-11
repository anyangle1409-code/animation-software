#!/usr/bin/env node
/**
 * G2 definitive actual GPU four-weight LBS vertex shader vs original CPU LBS.
 * Chromium WebGL2 transform feedback reads real skinned vertex positions.
 * Wholly synthetic nonhuman geometry, no original/third-party body asset.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';
const PORT=5185,BASE='http://127.0.0.1:'+PORT+'/';
const OUT=path.resolve('reports/browser-smoke/first-party-g2-gpu-palette');
fs.mkdirSync(OUT,{recursive:true});
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js',
  '--host','127.0.0.1','--port',String(PORT),'--strictPort'],{stdio:'ignore'});
let browser;
async function ready(){
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw new Error('G2 first-party browser server stopped');
    try{if((await fetch(BASE)).ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  throw new Error('G2 first-party browser server could not start');
}
try{
  await ready();
  browser=await chromium.launch({headless:true,args:[
    '--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'
  ]});
  const page=await browser.newPage({viewport:{width:1280,height:900}});
  const errors=[],consoleErrors=[],vendorRequests=[];
  page.on('pageerror',err=>errors.push(err.message));
  page.on('console',msg=>{if(msg.type()==='error')consoleErrors.push(msg.text())});
  page.on('request',request=>{
    if(/(?:threeRuntimeBoundary|threeSceneBoundary|node_modules\/\.vite\/deps\/three(?:\.js)?(?:\?|$)|react-dom|@react-three)/i.test(request.url()))
      vendorRequests.push(request.url());
  });
  await page.goto(BASE+'native-webgl2-skinning-preview.html',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>{
    const c=document.querySelector('#hgpt-native-skin-canvas');
    return c&&Number(c.dataset.hgptNativeSkinnedFrame)>=5;
  },null,{timeout:35000});
  const result=await page.evaluate(async()=>{
    const {buildSyntheticUV0Glb}=
      await import('/tests/support/buildSyntheticUV0Glb.mjs');
    const {parseRestrictedBatchedSkinnedGlb}=
      await import('/src/viewer/firstPartyGlbSkinnedBatches.mjs');
    const {validateNativeGLBToRigBinding,packMappedWorldPalette}=
      await import('/src/viewer/firstPartyGlbRigBindingContract.mjs');
    const {deformIndexedSkin}=
      await import('/src/viewer/firstPartyIndexedSkinnedMesh.mjs');
    const {createNativePaletteSkinnedWebGL2,buildNativeJointSkinPalette}=
      await import('/src/viewer/firstPartyGpuPaletteSkinning.mjs');
    const data=buildSyntheticUV0Glb({meshCount:2,primitivesPerMesh:1});
    const batch=parseRestrictedBatchedSkinnedGlb(data,{allowSourceUV0:true});
    const canvas=document.createElement('canvas');
    canvas.id='hgpt-native-gpu-bone-palette-test';
    canvas.style.position='absolute';
    canvas.style.left='8px';canvas.style.top='120px';
    canvas.style.width='960px';canvas.style.height='540px';
    canvas.style.border='2px solid #dbeef7';
    document.body.append(canvas);
    const gpu=createNativePaletteSkinnedWebGL2(canvas);
    gpu.setSize(960,540,1);
    const id=()=>new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
    const shift=(x,y,z)=>new Float32Array([
      1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1]);
    const checked=batch.batches.map(item=>
      validateNativeGLBToRigBinding(item.parsed,{
        sourceToCanonical:{test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
        allowedCanonicalNames:['upperarm_l','forearm_l'],
        canonicalRestWorldByBone:{upperarm_l:id(),forearm_l:id()}
      }));
    let actualParityMaxError=0;
    let firstY=null,skinMotion=0;
    let sampledGpuVsCpu=null;
    for(let frame=0;frame<20;frame++){
      const t=frame/19;
      const parts=batch.batches.map((part,i)=>{
        const posedWorld=packMappedWorldPalette(checked[i],{
          upperarm_l:id(),forearm_l:shift(0,t*.5,0)
        });
        return {mesh:part.parsed.mesh,uv0:part.sourceUV0,posedWorld};
      });
      gpu.renderBatches(parts);
      for(const part of parts){
        // Compare indexed per-vertex world positions emitted by the REAL GPU
        // vertex shader with independent CPU four-influence source baseline.
        const observed=gpu.captureIndexedSkinnedPositions(part);
        const reference=deformIndexedSkin(part.mesh,part.posedWorld);
        for(let i=0;i<part.mesh.indices.length;i++)for(let k=0;k<3;k++){
          const vertex=part.mesh.indices[i];
          const correct=reference.positions[vertex*3+k];
          const actual=observed[i*3+k];
          if(sampledGpuVsCpu===null || Math.abs(actual-correct)>sampledGpuVsCpu.error){
            sampledGpuVsCpu={index:i,component:k,expected:correct,
              received:actual,error:Math.abs(actual-correct),
              gpuBufferSlice:[...observed.slice(0,9)],
              cpuPositions:[...reference.positions.slice(0,9)]};
          }
          actualParityMaxError=Math.max(actualParityMaxError,Math.abs(actual-correct));
        }
        if(part===parts[0]){
          const y=reference.positions[1];
          if(firstY===null)firstY=y;
          skinMotion=Math.max(skinMotion,Math.abs(y-firstY));
        }
      }
    }
    // Explicit four different skinning influences. GPU shader must genuinely
    // read x,y,z,w integer joint indices and four nonzero source weights.
    const four={
      positions:new Float32Array([0,0,0,1,0,0,0,1,0]),
      indices:new Uint16Array([0,1,2]),
      jointIndices:new Uint16Array([...Array(3)].flatMap(()=>[0,1,2,3])),
      weights:new Float32Array([...Array(3)].flatMap(()=>[.1,.2,.3,.4])),
      inverseBindMatrices:new Float32Array([...id(),...id(),...id(),...id()])
    };
    const fourWorld=new Float32Array([
      ...shift(1,0,0),...shift(0,2,0),
      ...shift(0,0,3),...shift(-4,0,0)
    ]);
    const fourPart={mesh:four,posedWorld:fourWorld,
      uv0:new Float32Array([.1,.1,.9,.1,.1,.9])};
    const fourGpu=gpu.captureIndexedSkinnedPositions(fourPart);
    const fourCpu=deformIndexedSkin(four,fourWorld);
    let fourWeightGpuMaxError=0;
    for(let i=0;i<four.indices.length;i++)for(let k=0;k<3;k++){
      const index=four.indices[i];
      fourWeightGpuMaxError=Math.max(fourWeightGpuMaxError,
        Math.abs(fourGpu[i*3+k]-fourCpu.positions[index*3+k]));
    }
    const cpuBonePalette=buildNativeJointSkinPalette(four,fourWorld);
    // Actual GPU texture must work with a FULL 128-bone palette rather than
    // passing only the small 2/4-bone tests. The diagnostic source remains
    // a single original synthetic triangle; no human anatomy or mesh claim.
    const bigBind=new Float32Array(128*16),bigWorld=new Float32Array(128*16);
    for(let k=0;k<128;k++){
      bigBind.set(id(),k*16);bigWorld.set(id(),k*16);
    }
    bigWorld.set(shift(1,0,0),0);
    bigWorld.set(shift(0,2,0),31*16);
    bigWorld.set(shift(0,0,3),64*16);
    bigWorld.set(shift(-4,0,0),127*16);
    const bigMesh={
      positions:new Float32Array([0,0,0,1,0,0,0,1,0]),
      indices:new Uint16Array([0,1,2]),
      jointIndices:new Uint16Array([...Array(3)].flatMap(()=>[0,31,64,127])),
      weights:new Float32Array([...Array(3)].flatMap(()=>[.1,.2,.3,.4])),
      inverseBindMatrices:bigBind,
    };
    const bigPart={mesh:bigMesh,posedWorld:bigWorld,
      uv0:new Float32Array([.1,.1,.9,.1,.1,.9])};
    const bigPalette=buildNativeJointSkinPalette(bigMesh,bigWorld);
    const bigGpu=gpu.captureIndexedSkinnedPositions(bigPart);
    const bigCPU=deformIndexedSkin(bigMesh,bigWorld);
    let max128BoneGpuVsCpuError=0;
    for(let i=0;i<bigMesh.indices.length;i++)for(let k=0;k<3;k++){
      const j=bigMesh.indices[i];
      max128BoneGpuVsCpuError=Math.max(max128BoneGpuVsCpuError,
        Math.abs(bigGpu[i*3+k]-bigCPU.positions[j*3+k]));
    }
    const gl=canvas.getContext('webgl2');
    const pixels=new Uint8Array(960*540*4);
    gl.readPixels(0,0,960,540,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
    let red=0,green=0;
    for(let i=0;i<pixels.length;i+=4){
      const r=pixels[i],g=pixels[i+1];
      if(r>85&&r>g*2.5)red++;
      if(g>85&&g>r*2.5)green++;
    }
    return {
      kind:gpu.kind,
      twoSourceOwnedSkinnedMeshes:batch.audit.numberOfMeshes,
      inputGLBBytes:data.byteLength,
      boneCountInFourInfluenceFixture:cpuBonePalette.length/16,
      verifiedLargeBonePaletteCount:bigPalette.length/16,
      rgbaFloatTexelsUploadedFor128BonePalette:bigPalette.length/4,
      max128BoneGpuVsCpuError,
      frames:gpu.frameCount,
      nativeIndexedDrawCalls:gpu.drawCallCount,
      indexedTrianglePositionCaptures:gpu.capturedTriangleCount,
      maxAbsoluteGpuVsCpuPositionError:actualParityMaxError,
      sampleGpuVsCpu:sampledGpuVsCpu,
      glErrorAfterTransformFeedback:gl.getError(),
      fourNonzeroInfluencesGpuVsCpuMaxError:fourWeightGpuMaxError,
      measuredCpuSkinMotion:skinMotion,
      redUVGpuPixels:red,greenUVGpuPixels:green,
      framebuffer:[canvas.width,canvas.height],
      texturePaletteFormat:'RGBA32F four texels per column-major mat4',
      paletteWorksWithoutUniformArrayBoneCeiling:true,
      realOriginalHumanMeshRendered:false,
      productionEditorThreeDependencyRemoved:false,
    };
  });
  console.log('G2_GPU_CPU_DEBUG',JSON.stringify(result));
  assert.equal(result.kind,'hgpt-native-webgl2-rgba32f-4weight-gpu-lbs-v1');
  assert.equal(result.twoSourceOwnedSkinnedMeshes,2);
  assert.equal(result.boneCountInFourInfluenceFixture,4);
  assert.equal(result.verifiedLargeBonePaletteCount,128);
  assert.equal(result.rgbaFloatTexelsUploadedFor128BonePalette,512);
  assert.ok(result.max128BoneGpuVsCpuError<1e-5,
    'Actual 128-bone shader omitted far-index bone or damaged matrix palette');
  assert.equal(result.frames,20);
  assert.equal(result.nativeIndexedDrawCalls,40);
  assert.ok(result.indexedTrianglePositionCaptures>=41);
  assert.ok(result.maxAbsoluteGpuVsCpuPositionError<1e-5,
    'Real GPU palette skinning disagrees with original CPU LBS');
  assert.ok(result.fourNonzeroInfluencesGpuVsCpuMaxError<1e-5,
    'Real shader discarded a fourth skin joint influence');
  assert.ok(result.measuredCpuSkinMotion>.12);
  assert.ok(result.redUVGpuPixels>400,'GPU first skinned mesh absent');
  assert.ok(result.greenUVGpuPixels>400,'GPU second skinned mesh absent');
  assert.deepEqual(errors,[]);assert.deepEqual(consoleErrors,[]);
  assert.deepEqual(vendorRequests,[]);
  await page.screenshot({path:path.join(OUT,'original-four-weight-gpu-palette-synthetic-proof.png')});
  const output={pass:true,...result,browserErrors:errors,consoleErrors,vendorRequests,
    originalHumanAssetNotUsed:true,clinicalAnatomyNotApproved:true,
    imageTexturesNotYetImplemented:true};
  fs.writeFileSync(path.join(OUT,'native-gpu-vs-cpu-lbs-palette-check.json'),
    JSON.stringify(output,null,2)+'\n');
  console.log(JSON.stringify(output,null,2));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
