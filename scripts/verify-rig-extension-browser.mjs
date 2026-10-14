/** Synthetic 79-joint helper/toe + morph-before-LBS WebGL2 experiment.
 * No human/model acceptance claim. Uses existing first-party GPU renderer.
 */
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdirSync,writeFileSync} from 'node:fs';
import {chromium} from 'playwright';
const base='http://127.0.0.1:5187/';
const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','--host','127.0.0.1',
  '--port','5187','--strictPort'],{stdio:'ignore'});
let browser;
try{
  let ready=false;
  for(let i=0;i<100;i++){
    try{if((await fetch(base)).ok){ready=true;break;}}catch{}
    if(server.exitCode!==null)throw Error('local server exited');
    await new Promise(r=>setTimeout(r,100));
  }
  assert.ok(ready,'local server not ready');
  browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
  const page=await browser.newPage();
  const errors=[],vendor=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(/threeRuntimeBoundary|threeSceneBoundary|node_modules\/\.vite\/deps\/three|react-dom/.test(r.url()))vendor.push(r.url());});
  await page.goto(base+'native-webgl2-skinning-preview.html');
  const result=await page.evaluate(async()=>{
    const {compileRigExtension,packExtendedReviewPose}=await import('/src/viewer/firstPartyRigExtension.mjs');
    const {compileDiagnosticMorphs,prepareDiagnosticMorphFrame}=await import('/src/viewer/firstPartyCorrectiveMorphs.mjs');
    const {createNativePaletteSkinnedWebGL2}=await import('/src/viewer/firstPartyGpuPaletteSkinning.mjs');
    const {deformIndexedSkin}=await import('/src/viewer/firstPartyIndexedSkinnedMesh.mjs');
    const id=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
    const names=Array.from({length:67},(_,i)=>'base_'+i);
    const ext=[...['l','r'].map(s=>({name:'deltoid_helper_'+s,parent:'base_10',role:'shoulder_helper'})),
      ...['l','r'].flatMap(s=>Array.from({length:5},(_,i)=>({name:'toe_'+i+'_'+s,parent:'base_60',role:'individual_toe'})))];
    const c=compileRigExtension({sourceSha256:'a'.repeat(64),jointNames:names},{
      kind:'hgpt-provisional-rig-extension-v2',status:'REVIEW_ONLY',baseSourceSha256:'a'.repeat(64),
      sourceSha256:'b'.repeat(64),baseJointNames:names,extensions:ext,
      morphNames:['knee_contact_l'],releaseApproved:false},{reviewOnly:true});
    const bind=new Float32Array(c.jointNames.length*16);
    for(let i=0;i<c.jointNames.length;i++)bind.set(id(),i*16);
    const mesh={positions:new Float32Array([0,0,0,1,0,0,0,1,0]),indices:new Uint16Array([0,1,2]),
      jointIndices:new Uint16Array(Array.from({length:3},()=>[67,68,69,78]).flat()),
      weights:new Float32Array(Array.from({length:3},()=>[.1,.2,.3,.4]).flat()),inverseBindMatrices:bind};
    const h=compileDiagnosticMorphs(mesh,new Float32Array([0,0,1,0,0,1,0,0,1]),[{
      name:'knee_contact_l',position:{indices:new Uint32Array([0]),deltas:new Float32Array([0,.1,0])},
      normal:{indices:new Uint32Array([0]),deltas:new Float32Array([.2,0,0])}}],{reviewOnly:true});
    const canvas=document.createElement('canvas');document.body.append(canvas);
    const gpu=createNativePaletteSkinnedWebGL2(canvas);gpu.setSize(320,240,1);
    let maxError=0,motion=0,normalError=0;
    for(let i=0;i<11;i++){
      const t=i/10,byName=Object.fromEntries(c.jointNames.map(n=>[n,id()]));
      for(const [j,k] of [67,68,69,78].entries())byName[c.jointNames[k]][12]=t*(j+1)*.1;
      const packed=packExtendedReviewPose(c,{sourceSha256:c.sourceSha256,posedWorldByJoint:byName,morphWeights:{knee_contact_l:t}});
      const p=prepareDiagnosticMorphFrame(h,{knee_contact_l:packed.morphWeights[0]});
      const part={...p,posedWorld:packed.posedWorld,uv0:new Float32Array([0,0,1,0,0,1])};
      gpu.renderBatches([part]);
      const observed=gpu.captureIndexedSkinnedPositions(part),cpu=deformIndexedSkin(part.mesh,part.posedWorld);
      const normals=gpu.captureIndexedSkinnedNormals(part);
      for(let k=0;k<observed.length;k++)maxError=Math.max(maxError,Math.abs(observed[k]-cpu.positions[k]));
      for(let k=0;k<normals.length;k++)normalError=Math.max(normalError,Math.abs(normals[k]-p.sourceNormals[k]));
      motion=Math.max(motion,observed[0]);
    }
    const {buildSyntheticExerciseHandoff}=await import('/tests/support/buildSyntheticExerciseHandoff.mjs');
    const {bindFirstPartyExerciseToDiagnosticPose,getBoundDiagnosticExerciseFrame}=
      await import('/src/exercise/firstPartyExercisePoseBinding.mjs');
    const x=await buildSyntheticExerciseHandoff('dumbbell shoulder press');
    // Generic text must match generic authored metadata; never silently select a side/grip.
    x.declaration.parameters={equipment:'dumbbell',laterality:null,posture:null,grip:null};
    const bound=bindFirstPartyExerciseToDiagnosticPose(x.command,x.model,x.clip,x.declaration);
    const source=x.model.scene.batches[0].parsed;
    let commandGpuError=0;
    for(let i=0;i<bound.frameCount;i++){
      const posedWorld=getBoundDiagnosticExerciseFrame(bound,i).sourceJointOrderedPalette;
      const part={mesh:source.mesh,posedWorld,uv0:new Float32Array([0,0,1,0,0,1])};
      gpu.renderBatches([part]);
      const observed=gpu.captureIndexedSkinnedPositions(part),expected=deformIndexedSkin(part.mesh,posedWorld);
      for(let k=0;k<observed.length;k++)commandGpuError=Math.max(commandGpuError,Math.abs(observed[k]-expected.positions[k]));
    }
    let mismatchRejected=false;
    try{bindFirstPartyExerciseToDiagnosticPose('barbell shoulder press',x.model,x.clip,x.declaration);}
    catch{mismatchRejected=true;}
    const glError=canvas.getContext('webgl2').getError();gpu.dispose();
    return {joints:c.jointNames.length,frames:11,maxError,normalError,motion,glError,
      commandGpuError,commandFrames:bound.frameCount,mismatchRejected,
      realHumanRendered:false,productionApproved:false};
  });
  assert.equal(result.joints,79);assert.ok(result.maxError<1e-5);assert.ok(result.normalError<1e-5);
  assert.ok(result.motion>.29);assert.equal(result.glError,0);
  assert.ok(result.commandGpuError<1e-5);assert.equal(result.commandFrames,3);
  assert.equal(result.mismatchRejected,true);
  assert.deepEqual(errors,[]);assert.deepEqual(vendor,[]);
  mkdirSync('reports/browser-smoke/work-rig-extension',{recursive:true});
  writeFileSync('reports/browser-smoke/work-rig-extension/result.json',JSON.stringify({...result,errors,vendor},null,2)+'\n');
  console.log('SYNTHETIC_RIG_EXTENSION_GPU_PASS',JSON.stringify(result));
}finally{if(browser)await browser.close();server.kill();}
