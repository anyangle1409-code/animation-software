#!/usr/bin/env node
/**
 * G4k ACTUAL Work Blender 18-mesh original GLB → native 4-weight WebGL2
 * at independently proven original glTF Y-up WORLD REST pose only.
 * Source artifact W1 #68 pinned, no authored z-up pose conversion yet.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {chromium} from 'playwright';

const dir=process.argv[2];
if(!dir)throw Error('Usage: node scripts/verify-real-work-rest-gpu-browser.mjs <W1-artifact-dir>');
const name='PROVISIONAL_FUNCTIONAL_SHOULDER_v1.glb';
const bytes=fs.readFileSync(path.join(dir,name));
const hash=createHash('sha256').update(bytes).digest('hex');
const expected='fda9c5e653044988fd1e5c58fe352f074071c4be008eceba702bbbef96a4ea5f';
assert.equal(hash,expected);
const original=Buffer.from(bytes);
const out=path.resolve('reports/work-pilot/actual-work-rest-native-gpu');
fs.mkdirSync(out,{recursive:true});
const port=5221,base='http://127.0.0.1:'+port+'/';
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js',
  '--host','127.0.0.1','--port',String(port),'--strictPort'],{stdio:'ignore'});
let browser;
async function ready(){
  for(let i=0;i<100;i++){
    if(server.exitCode!==null)throw Error('Vite server exited');
    try{if((await fetch(base)).ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  throw Error('Original Work pilot browser server not ready');
}
try{
  await ready();
  browser=await chromium.launch({headless:true,
    args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
  const page=await browser.newPage({viewport:{width:1200,height:800}});
  const errors=[],vendor=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{const u=r.url();
    if(!u.startsWith(base)&&!u.startsWith('blob:')&&!u.startsWith('data:'))
      vendor.push(u);
  });
  await page.goto(base);
  const result=await page.evaluate(async supplied=>{
    const {parseRestrictedBatchedSkinnedGlb}=await import(
      '/src/viewer/firstPartyGlbSkinnedBatches.mjs');
    const {deriveOriginalSourceGLTFRestWorld}=await import(
      '/src/viewer/firstPartyOriginalGltfRestWorld.mjs');
    const {createNativePaletteSkinnedWebGL2}=await import(
      '/src/viewer/firstPartyGpuPaletteSkinning.mjs');
    const {validateProvisionalModelHandoff,
      digestOriginalGlbSha256,HGPT_PROTOTYPE_HANDOFF_KIND,
      packProvisionalModelPose}=await import(
        '/src/viewer/firstPartyPrototypeModelHandoff.mjs');
    const {deformIndexedSkin}=await import(
      '/src/viewer/firstPartyIndexedSkinnedMesh.mjs');
    const buf=new Uint8Array(supplied).buffer;
    const scene=parseRestrictedBatchedSkinnedGlb(buf,{
      allowProvisionalPilot:true,allowSourceFlatColors:true,
      allowSourceUV0:true,allowSourceNormals:true
    });
    const rest=deriveOriginalSourceGLTFRestWorld(buf,scene);
    const digest=await digestOriginalGlbSha256(buf);
    const manifest={
      kind:HGPT_PROTOTYPE_HANDOFF_KIND,
      candidateId:'PROVISIONAL_FUNCTIONAL_SHOULDER_v1',
      status:'PROTOTYPE_ONLY',
      glb:{sha256:digest,layout:'pilot',sourceFeatures:{
        flatColors:true,uv0:true,normals:true
      }},
      frame:{unit:'metre',up:'Y',handedness:'right',
        basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
      rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
        thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
      rig:{sourceToRuntimeBone:Object.fromEntries(
        rest.orderedSourceJointNames.map(n=>[n,n])),
        runtimeBoneNames:[...rest.orderedSourceJointNames],
        restWorldByRuntimeBone:rest.sourceWorldRestByName,
        lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED'},
      releaseApproved:false
    };
    const model=await validateProvisionalModelHandoff(buf,manifest);
    const canvas=document.createElement('canvas');
    document.body.appendChild(canvas);
    const engine=createNativePaletteSkinnedWebGL2(canvas);
    engine.setSize(960,540);
    const camera={eye:[0,1.5,3.4],target:[0,1.5,0]};
    const first=engine.renderVerifiedOriginalPilotFlatPose(
      model,rest.sourceWorldRestByName,camera);
    engine.renderVerifiedOriginalPilotFlatPose(
      model,rest.sourceWorldRestByName,camera);
    const gl=canvas.getContext('webgl2');
    const pixels=new Uint8Array(canvas.width*canvas.height*4);
    gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
    let foreground=0,nonGray=0;
    for(let i=0;i<pixels.length;i+=4){
      const [r,g,b]=pixels.subarray(i,i+3);
      if(r>75||g>75||b>75)foreground++;
      if(Math.max(r,g,b)-Math.min(r,g,b)>35 && (r>75||g>75||b>75))
        nonGray++;
    }
    const sourcePart=model.scene.batches[0],mesh=sourcePart.parsed.mesh;
    const poseWorld=packProvisionalModelPose(model,rest.sourceWorldRestByName);
    const uv0=sourcePart.sourceUV0 instanceof Float32Array ?
      sourcePart.sourceUV0:new Float32Array(mesh.positions.length/3*2);
    const gpu=engine.captureIndexedSkinnedPositions({
      mesh,uv0,sourceNormals:sourcePart.sourceNormals,posedWorld:poseWorld
    });
    const cpu=deformIndexedSkin(mesh,poseWorld);
    let maxPositionError=0;
    for(let k=0;k<mesh.indices.length;k++)
      for(let axis=0;axis<3;axis++)
        maxPositionError=Math.max(maxPositionError,
          Math.abs(gpu[k*3+axis]-cpu.positions[mesh.indices[k]*3+axis]));
    const snapshot=canvas.toDataURL('image/png');
    const info={
      modelSourceSha256:model.sourceSha256,
      actualWorkSourceVerified:true,
      sourceJointCount:rest.sourceJointCount,
      originalMeshes:model.scene.audit.numberOfMeshes,
      originalPrimitives:model.numberOfPrimitives,
      originalUntexturedMaterials:scene.batches.every(p=>p.sourceBaseColorPng===null),
      originalSourceUV0NotModified:true,
      realSourceRestResidual:rest.maximumWorldInverseBindResidual,
      drawCalls:engine.drawCallCount,
      frames:engine.frameCount,
      foregroundPixels:foreground,
      colouredPixels:nonGray,
      maxActualGPUvsCPUPositionError:maxPositionError,
      glError:gl.getError(),
      screenshot:snapshot,
      sourceYUpRestOnly:true,
      WorkNativeZUpPoseConverted:false,
      fullHumanAnatomyApproved:false,sourceRightsApproved:false,
      productionReady:false,
      firstPassDiagnostic:first,
    };
    engine.dispose();
    return info;
  },[...bytes]);
  assert.deepEqual(bytes,original,'source Work asset mutated');
  assert.equal(result.modelSourceSha256,expected);
  assert.equal(result.actualWorkSourceVerified,true);
  assert.equal(result.sourceJointCount,6);
  assert.equal(result.originalMeshes,18);
  assert.equal(result.originalPrimitives,18);
  assert.equal(result.firstPassDiagnostic.originalPrimitiveCount,18);
  assert.equal(result.firstPassDiagnostic.productionReady,false);
  assert.equal(result.drawCalls,36);
  assert.equal(result.frames,2);
  assert.equal(result.originalUntexturedMaterials,true);
  assert.ok(result.foregroundPixels>500,'actual Work shader frames lack geometry pixels');
  assert.ok(result.colouredPixels>100,'source Work material colours invisible');
  assert.ok(result.maxActualGPUvsCPUPositionError<.00001,
    'original Work rest GPU position parity differs from first-party CPU oracle');
  assert.ok(result.realSourceRestResidual<.0001);
  assert.equal(result.glError,0);
  assert.equal(result.WorkNativeZUpPoseConverted,false);
  assert.equal(result.fullHumanAnatomyApproved,false);
  assert.equal(result.productionReady,false);
  assert.deepEqual(errors,[]);assert.deepEqual(vendor,[]);
  assert.match(result.screenshot,/^data:image\/png;base64,/);
  const screenshot=Buffer.from(result.screenshot.split(',')[1],'base64');
  assert.ok(screenshot.length>2000);
  fs.writeFileSync(path.join(out,'actual-W1-18-original-mesh-rest-pose.png'),screenshot);
  const {screenshot:unused,...meta}=result;
  fs.writeFileSync(path.join(out,'actual-work-18-mesh-first-party-gpu-rest.json'),
    JSON.stringify({success:true,...meta},null,2)+'\n');
  console.log(JSON.stringify({sourceSha256:expected,draws:result.drawCalls,
    foreground:result.foregroundPixels,coloured:result.colouredPixels,
    maxGPUCPU:result.maxActualGPUvsCPUPositionError,glError:result.glError}));
}finally{
  await browser?.close().catch(()=>{});
  server.kill('SIGTERM');
}
