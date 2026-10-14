/** Immutable provisional r95 bare-source neutral WebGL2 experiment.
 * No movement, anatomy or release acceptance claim. Uses existing first-party GPU renderer.
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
    const {parseOriginalFullBodyReviewGLB,assertAuthenticatedOriginalFullBodyReviewUnmodified}=
      await import('/src/viewer/firstPartyOriginalFullBodyReview.mjs');
    const {prepareVerifiedOriginalFullBodyRestGpu,renderVerifiedOriginalFullBodyRestGpu}=
      await import('/src/viewer/firstPartyOriginalFullBodyGpuRest.mjs');
    const {cameraForOriginalFullBodyReview}=await import('/src/viewer/firstPartyOriginalFullBodyLocalReview.mjs');
    const {createNativePaletteSkinnedWebGL2}=await import('/src/viewer/firstPartyGpuPaletteSkinning.mjs');
    const {deformIndexedSkin}=await import('/src/viewer/firstPartyIndexedSkinnedMesh.mjs');
    const response=await fetch('/ORIGINAL_V1_WORK/candidates/exports/r95_phase4_freeze/HomeGymPT_Male_ORIGINAL_v1_CANDIDATE_r95_BARE.glb');
    if(!response.ok)throw Error('pinned provisional source unavailable');
    const bytes=await response.arrayBuffer();
    if(bytes.byteLength!==1496696)throw Error('pinned provisional source byte count mismatch');
    const sourceSha='c4b8e388e624a4a3d22510b40c1fc45017b3374b1ff9de2cae79f2dbb0797c85';
    const source=await parseOriginalFullBodyReviewGLB(bytes,{expectedSha256:sourceSha});
    const prepared=prepareVerifiedOriginalFullBodyRestGpu(source);
    const canvas=document.createElement('canvas');document.body.append(canvas);
    const gpu=createNativePaletteSkinnedWebGL2(canvas);gpu.setSize(320,400,1);
    try{
      const gl=canvas.getContext('webgl2'),views=[];
      for(const view of ['front','rear','left','right','three-quarter']){
        const camera=cameraForOriginalFullBodyReview(view);
        const draw=renderVerifiedOriginalFullBodyRestGpu(gpu,prepared,{eye:camera.eye,target:camera.target});
        const pixels=new Uint8Array(canvas.width*canvas.height*4);
        gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
        let visiblePixels=0;
        for(let i=0;i<pixels.length;i+=4){
          if(Math.abs(pixels[i]-10)>2||Math.abs(pixels[i+1]-13)>2||Math.abs(pixels[i+2]-20)>2)visiblePixels++;
        }
        views.push({view,drawn:draw.drawn,visiblePixels,glError:gl.getError()});
      }
      const part=prepared.gpuParts[0];
      const cpu=deformIndexedSkin(part.mesh,part.posedWorld);
      let maximumPositionError=0,capturedIndices=0,captureBatches=0;
      // Preserve the 8192-index API limit and complete triangles (8190).
      // Capture returns deindexed output; compare against the original index.
      for(let offset=0;offset<part.mesh.indices.length;offset+=8190){
        const indices=part.mesh.indices.slice(offset,offset+8190);
        const diagnosticPart={...part,mesh:{...part.mesh,indices}};
        const positions=gpu.captureIndexedSkinnedPositions(diagnosticPart);
        if(positions.length!==indices.length*3)throw Error('incomplete GPU capture');
        for(let i=0;i<indices.length;i++)for(let axis=0;axis<3;axis++){
          const observed=positions[i*3+axis];
          if(!Number.isFinite(observed))throw Error('nonfinite GPU rest position');
          maximumPositionError=Math.max(maximumPositionError,
            Math.abs(observed-cpu.positions[indices[i]*3+axis]));
        }
        capturedIndices+=indices.length;captureBatches++;
      }
      if(capturedIndices!==part.mesh.indices.length)throw Error('incomplete source triangle coverage');
      assertAuthenticatedOriginalFullBodyReviewUnmodified(source);
      const digest=await crypto.subtle.digest('SHA-256',bytes);
      const after=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');
      if(after!==sourceSha)throw Error('source bytes changed');
      return {sourceSha,sourceBytes:bytes.byteLength,vertices:source.vertices,triangles:source.triangles,
        joints:source.bones,morphs:source.sparseCorrectives.length,views,maximumPositionError,capturedIndices,captureBatches,
        glError:gl.getError(),actualProvisionalSourceRendered:true,sourceUnmodified:true,
        morphWeightsAtRestAllZero:prepared.originalMorphWeightsAllZero,
        actualHumanMovementVerified:false,anatomicalAcceptance:false,productionApproved:false};
    }finally{gpu.dispose();}
  });
  assert.equal(result.vertices,17946);assert.equal(result.triangles,35888);assert.equal(result.joints,67);
  assert.equal(result.morphs,6);assert.equal(result.morphWeightsAtRestAllZero,true);
  assert.equal(result.capturedIndices,35888*3);assert.equal(result.captureBatches,14);
  assert.ok(result.maximumPositionError<1e-5);assert.equal(result.glError,0);
  for(const view of result.views){assert.equal(view.drawn,true);assert.ok(view.visiblePixels>100);assert.equal(view.glError,0);}
  assert.deepEqual(errors,[]);assert.deepEqual(vendor,[]);
  mkdirSync('artifacts',{recursive:true});
  writeFileSync('artifacts/r95-neutral-gpu.json',JSON.stringify({...result,errors,vendor},null,2)+'\n');
  console.log('R95_PROVISIONAL_REST_GPU_PASS',JSON.stringify(result));
}finally{if(browser)await browser.close();server.kill();}
