#!/usr/bin/env node
/** G4m REAL Work #68 original 7 authored converted poses × all 18 source meshes in native WebGL2. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';
const dir=process.argv[2];
if(!dir)throw Error('Usage: node scripts/verify-real-work-seven-pose-gpu-browser.mjs <actual-W1-artifact-dir>');
const name='PROVISIONAL_FUNCTIONAL_SHOULDER_v1.glb',expected=
  'fda9c5e653044988fd1e5c58fe352f074071c4be008eceba702bbbef96a4ea5f';
const work=fs.readFileSync(path.join(dir,name)),snapshot=Buffer.from(work);
assert.equal(createHash('sha256').update(work).digest('hex'),expected);
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'pilot_manifest.json'),'utf8'));
assert.equal(manifest.files_sha256[name],expected);
const output=path.resolve('reports/work-pilot/actual-work-seven-pose-native-GPU');
fs.mkdirSync(output,{recursive:true});
const port=5223,url='http://127.0.0.1:'+port+'/';
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js',
  '--host','127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});
let browser;
async function ready(){
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw Error('Vite original pilot browser server exited');
    try{if((await fetch(url)).ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  throw Error('Original Work seven-pose browser server did not start');
}
try{
  await ready();
  browser=await chromium.launch({headless:true,
    args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
  const page=await browser.newPage({viewport:{width:1200,height:800}});
  const errors=[],external=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{const u=r.url();
    if(!u.startsWith(url)&&!u.startsWith('data:')&&!u.startsWith('blob:'))external.push(u);
  });
  await page.goto(url);
  const result=await page.evaluate(async input=>{
    const {parseRestrictedBatchedSkinnedGlb}=await import(
      '/src/viewer/firstPartyGlbSkinnedBatches.mjs');
    const {deriveOriginalSourceGLTFRestWorld}=await import(
      '/src/viewer/firstPartyOriginalGltfRestWorld.mjs');
    const {HGPT_PROTOTYPE_HANDOFF_KIND,validateProvisionalModelHandoff}
      =await import('/src/viewer/firstPartyPrototypeModelHandoff.mjs');
    const {registerWorkNativePoseSamplesToOriginalGLTF,
      readRegisteredWorkPoseFrame}=await import(
        '/src/viewer/firstPartyWorkNativePoseRegistration.mjs');
    const {createNativePaletteSkinnedWebGL2}=await import(
      '/src/viewer/firstPartyGpuPaletteSkinning.mjs');
    const {deformIndexedSkin}=await import(
      '/src/viewer/firstPartyIndexedSkinnedMesh.mjs');
    const bin=new Uint8Array(input.bytes).buffer;
    const scene=parseRestrictedBatchedSkinnedGlb(bin,{
      allowProvisionalPilot:true,allowSourceFlatColors:true,
      allowSourceUV0:true,allowSourceNormals:true
    });
    const rest=deriveOriginalSourceGLTFRestWorld(bin,scene);
    const ids=[...rest.orderedSourceJointNames];
    const model=await validateProvisionalModelHandoff(bin,{
      kind:HGPT_PROTOTYPE_HANDOFF_KIND,
      candidateId:input.work.candidate,
      status:'PROTOTYPE_ONLY',
      glb:{sha256:input.hash,layout:'pilot',sourceFeatures:{
        flatColors:true,uv0:true,normals:true
      }},
      frame:{unit:'metre',up:'Y',handedness:'right',
        basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
      rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
        thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
      rig:{
        sourceToRuntimeBone:Object.fromEntries(ids.map(n=>[n,n])),
        runtimeBoneNames:ids,restWorldByRuntimeBone:rest.sourceWorldRestByName,
        lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED'
      },releaseApproved:false,
    });
    const registered=registerWorkNativePoseSamplesToOriginalGLTF(model,rest,input.work);
    const canvas=document.createElement('canvas');
    document.body.appendChild(canvas);
    const gpu=createNativePaletteSkinnedWebGL2(canvas);gpu.setSize(960,540);
    const gl=canvas.getContext('webgl2');
    const camera={eye:[0,1.5,3.4],target:[0,1.5,0]};
    const reports=[],screenshots=[];
    const zero=new Uint8Array(canvas.width*canvas.height*4);
    let initial=null,maximumError=0;
    const MAX_PER_PART_CAPTURE=8192;
    for(let i=0;i<registered.originalFrameCount;i++){
      const f=readRegisteredWorkPoseFrame(registered,i);
      const posed=Object.fromEntries(ids.map((name,j)=>[
        name,[...f.sourceJointWorldPalette.subarray(j*16,j*16+16)]
      ]));
      const draw=gpu.renderVerifiedOriginalPilotFlatPose(model,posed,camera);
      if(!draw.drewAllOriginalPilotParts || draw.originalPrimitiveCount!==18)
        throw Error('actual original 18-part draw incomplete');
      const pixels=new Uint8Array(zero.length);
      gl.readPixels(0,0,canvas.width,canvas.height,
        gl.RGBA,gl.UNSIGNED_BYTE,pixels);
      if(i===0)initial=pixels.slice();
      let visible=0,coloured=0,pixelDiff=0;
      for(let j=0;j<pixels.length;j+=4){
        const r=pixels[j],g=pixels[j+1],b=pixels[j+2];
        if(r>75||g>75||b>75)visible++;
        if((r>75||g>75||b>75)&&
          Math.max(r,g,b)-Math.min(r,g,b)>35)coloured++;
        if(Math.max(Math.abs(r-initial[j]),
          Math.abs(g-initial[j+1]),Math.abs(b-initial[j+2]))>15)pixelDiff++;
      }
      // Sample every REAL Work mesh against separate original CPU 4-weight
      // source skinning, not only the synthetic shoulder fixture.
      let maxError=0,sourceTriangleCount=0;
      for(const part of model.scene.batches){
        const mesh=part.parsed.mesh;
        if(mesh.indices.length>MAX_PER_PART_CAPTURE)
          throw Error('Work part exceeds bounded actual GPU diagnostic capture');
        const shape={
          mesh,posedWorld:f.sourceJointWorldPalette,
          uv0:part.sourceUV0 instanceof Float32Array?
            part.sourceUV0:new Float32Array(mesh.positions.length/3*2),
          sourceNormals:part.sourceNormals??undefined,
        };
        const actual=gpu.captureIndexedSkinnedPositions(shape);
        const oracle=deformIndexedSkin(mesh,f.sourceJointWorldPalette);
        for(let tri=0;tri<mesh.indices.length;tri++)for(let axis=0;axis<3;axis++)
          maxError=Math.max(maxError,Math.abs(
            actual[tri*3+axis]-oracle.positions[mesh.indices[tri]*3+axis]));
        sourceTriangleCount+=mesh.indices.length/3;
      }
      maximumError=Math.max(maximumError,maxError);
      const png=canvas.toDataURL('image/png');
      screenshots.push(png);
      reports.push({
        index:i,timeSeconds:f.timeSeconds,
        originalAuthoredRotationFromRestDegrees:f.authoredArmRotationFromRestDegrees,
        actualIndexedSourcePrimitives:18,
        originalSourceTrianglesCheckedByGPU:sourceTriangleCount,
        visiblePixels:visible,sourceColouredPixels:coloured,
        screenPixelsChangedFromFirstFrame:pixelDiff,
        maxGPUvsOriginalCPUPositionError:maxError,
        glError:gl.getError(),
      });
    }
    const out={
      originalSourceSha:model.sourceSha256,
      sourceWorksOriginal18MeshesDrawn:true,
      totalSourceDrawCalls:gpu.drawCallCount,
      frames:gpu.frameCount,
      registeredSourcePoseCount:registered.originalFrameCount,
      nativeToGLTFMaxSkinResidual:registered.maximumNativeSkinVsGLTFSkinResidual,
      maximumActualSourceGPUCPUError:maximumError,
      sourceWorkPoseIsRotationFromRestNotAbsoluteElevation:true,
      originalHumanMotionPhysiologicallyValidated:false,
      fullBodyHumanMeshAvailable:false,
      softwareProductionApproved:false,
      results:reports,screenshots,
    };
    gpu.dispose();
    return out;
  },{bytes:[...work],hash:expected,work:manifest});
  assert.deepEqual(work,snapshot,'Work original source GLB bytes must remain unchanged');
  assert.equal(result.originalSourceSha,expected);
  assert.equal(result.frames,7);
  assert.equal(result.registeredSourcePoseCount,7);
  assert.equal(result.totalSourceDrawCalls,7*18);
  assert.ok(result.maximumActualSourceGPUCPUError<.00001,
    'original Work moving GPU source positions do not match original CPU oracle');
  assert.ok(result.nativeToGLTFMaxSkinResidual<.0001);
  assert.ok(result.results.every(f=>f.actualIndexedSourcePrimitives===18&&
    f.visiblePixels>250&&f.sourceColouredPixels>100&&f.glError===0));
  assert.ok(result.results.some(f=>f.index>0&&f.index<5&&
    f.screenPixelsChangedFromFirstFrame>100),
    'no visible movement in original authored source shoulder pose sequence');
  assert.equal(result.originalHumanMotionPhysiologicallyValidated,false);
  assert.equal(result.softwareProductionApproved,false);
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  for(let i=0;i<result.screenshots.length;i++){
    const data=result.screenshots[i];
    assert.match(data,/^data:image\/png;base64,/);
    const image=Buffer.from(data.slice('data:image/png;base64,'.length),'base64');
    assert.ok(image.length>1200,'original source authored sample PNG empty');
    fs.writeFileSync(path.join(output,
      'W1-authored-pose-'+String(i).padStart(2,'0')+'-'+
      result.results[i].originalAuthoredRotationFromRestDegrees+'deg-from-rest.png'),
      image);
  }
  const {screenshots,...safe}=result;
  fs.writeFileSync(path.join(output,'W1-authored-7-poses-source-GPU-CPU-evidence.json'),
    JSON.stringify({success:true,...safe},null,2)+'\n');
  console.log(JSON.stringify({originalSourceSha:expected,
    actualSourceDrawCalls:safe.totalSourceDrawCalls,
    frames:safe.frames,
    maxRealSourceGPUvsCPUError:safe.maximumActualSourceGPUCPUError,
    sourceMovementPixelDiff:safe.results.map(x=>x.screenPixelsChangedFromFirstFrame),
    allSourceMeshMaterialRegionsVisible:safe.results.every(x=>x.sourceColouredPixels>100)}));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
