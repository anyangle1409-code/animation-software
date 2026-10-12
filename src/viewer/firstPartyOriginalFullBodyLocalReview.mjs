/**
 * G4u: manually supplied ORIGINAL-v1 local review GLB -> real WebGL2 rest
 * preview. No fetch, storage, canvas auto-mount, third-party runtime, or
 * automatic publishing. User chooses a File; source SHA/rig/morphs must pass
 * actual first-party G4r/G4s/G4t checks before ANY GPU draw.
 *
 * This does not invent movements. It cannot make the original skeleton,
 * deformation, feet, rights or clinical status approved.
 */
import {parseOriginalFullBodyReviewGLB}
  from './firstPartyOriginalFullBodyReview.mjs';
import {prepareVerifiedOriginalFullBodyRestGpu,
  renderVerifiedOriginalFullBodyRestGpu}
  from './firstPartyOriginalFullBodyGpuRest.mjs';
import {createNativePaletteSkinnedWebGL2}
  from './firstPartyGpuPaletteSkinning.mjs';

export const HGPT_LOCAL_FULLBODY_REVIEW_KIND=
  'hgpt-original-local-owner-file-neutral-review-v1';
export const ORIGINAL_V1_REVIEW_PINNED_SHA=
  'd267dac344affb5d52c7155f8d0254794e818a8eab3ad54f7f263694f36c390d';
export const ORIGINAL_V1_REVIEW_PINNED_BYTES=1495720;
const modes=Object.freeze(['front','rear','left','right','three-quarter']);
const cameraSettings=Object.freeze({
  front:Object.freeze([0,1.0,3.45]),
  rear:Object.freeze([0,1.0,-3.45]),
  left:Object.freeze([-3.45,1.0,0]),
  right:Object.freeze([3.45,1.0,0]),
  'three-quarter':Object.freeze([2.45,1.18,2.45]),
});
const fail=s=>{throw new RangeError('Original local body review blocked: '+s)};
const need=(ok,s)=>{if(!ok)fail(s)};
const finite=(x)=>Number.isFinite(x);
export function cameraForOriginalFullBodyReview(view='front'){
  need(typeof view==='string'&&modes.includes(view),
    'camera must be one of the five bounded original neutral views');
  // Camera coordinates are original source glTF Y-up metres, not native
  // Blender Z-up joint transforms or a claim to medical front/back landmarks.
  return {
    view,
    eye:[...cameraSettings[view]],
    target:[0,.91,0],
    status:'DIAGNOSTIC_CAMERA_UNVERIFIED_MEDICAL_ORIENTATION',
  };
}
/**
 * Returns an authenticated, nonrelease neutral viewer *only* on a browser
 * where the actual original native WebGL2 renderer can initialize.
 * There is no silent CPU render, mesh swap or synthetic-manikin fallback.
 */
export async function openOriginalFullBodyOwnerLocalReview({
  ownerFile,canvas,view='front',width=900,height=1200,pixelRatio=1
}={}){
  need(ownerFile&&typeof ownerFile==='object'&&
    ownerFile.name==='HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb' &&
    ownerFile.size===ORIGINAL_V1_REVIEW_PINNED_BYTES &&
    typeof ownerFile.arrayBuffer==='function',
    'select the exact ORIGINAL_v1 review GLB locally; no URL or remote asset');
  need(canvas&&typeof canvas.getContext==='function'&&
    typeof canvas.addEventListener==='function'&&
    typeof canvas.removeEventListener==='function',
    'local WebGL2 canvas required; no remote viewer fallback');
  need(Number.isInteger(width)&&width>=160&&width<=2000&&
    Number.isInteger(height)&&height>=160&&height<=2400&&
    finite(pixelRatio)&&pixelRatio>=.5&&pixelRatio<=2,
    'bounded local preview viewport required');
  const firstCamera=cameraForOriginalFullBodyReview(view);
  const original=await ownerFile.arrayBuffer();
  need(original instanceof ArrayBuffer&&
    original.byteLength===ORIGINAL_V1_REVIEW_PINNED_BYTES,
    'locally selected original GLB file bytes changed during read');
  const source=await parseOriginalFullBodyReviewGLB(original,{
    expectedSha256:ORIGINAL_V1_REVIEW_PINNED_SHA,
  });
  const plan=prepareVerifiedOriginalFullBodyRestGpu(source);
  let renderer;
  try{
    renderer=createNativePaletteSkinnedWebGL2(canvas);
    renderer.setSize(width,height,pixelRatio);
    let alive=true,currentView=null,frameCount=0;
    const renderView=(mode)=>{
      need(alive,'review session has been disposed');
      const camera=cameraForOriginalFullBodyReview(mode);
      // Source plan/palette are reverified by G4t immediately before draw.
      const result=renderVerifiedOriginalFullBodyRestGpu(
        renderer,plan,{eye:camera.eye,target:camera.target});
      need(result.drawn===true,
        'no actual original source GPU draw occurred');
      currentView=mode;
      frameCount++;
      return Object.freeze({
        kind:HGPT_LOCAL_FULLBODY_REVIEW_KIND,
        originalSourceSha256:ORIGINAL_V1_REVIEW_PINNED_SHA,
        view:mode,drawn:true,diagnosticRestOnly:true,
        sourceMeshVertices:17946,sourceSkinJoints:67,
        sourceSparseMorphsStillZero:true,
        originalWorkBodyChanged:false,
        originalRightsForReleaseApproved:false,
        anatomicalMotionApproved:false,
        fullBodyLiveExerciseApproved:false,
        productionReady:false,
      });
    };
    const initial=renderView(firstCamera.view);
    const session=Object.freeze({
      kind:HGPT_LOCAL_FULLBODY_REVIEW_KIND,
      originalSourceSha256:ORIGINAL_V1_REVIEW_PINNED_SHA,
      get currentView(){return currentView;},
      get drawsMade(){return frameCount;},
      initial,renderView,
      dispose(){if(!alive)return;alive=false;renderer.dispose();},
    });
    return session;
  }catch(e){
    renderer?.dispose();
    // Throw actual inability to obtain WebGL2; never call it a passing
    // full-body GPU test or silently replace the model with a mannequin.
    throw e;
  }
}
/**
 * A small optional DOM wiring helper, not auto-invoked. All controls belong
 * to the local caller; nothing is sent to a remote server or production PT.
 */
export function bindOriginalFullBodyOwnerLocalControls({
  fileInput,canvas,cameraSelector,statusTarget
}={}){
  need(fileInput?.type==='file'&&typeof fileInput.addEventListener==='function' &&
    cameraSelector?.tagName==='SELECT'&&
    typeof cameraSelector.addEventListener==='function'&&
    statusTarget&&typeof statusTarget.textContent==='string',
    'manual source file/select/status DOM controls required');
  let session=null;
  const onFile=async()=>{
    const f=fileInput.files?.[0];
    session?.dispose();session=null;
    if(!f){statusTarget.textContent='Select the original review-only GLB.';return}
    statusTarget.textContent='Checking original source SHA, rig and rest...';
    try{
      session=await openOriginalFullBodyOwnerLocalReview({
        ownerFile:f,canvas,view:cameraSelector.value
      });
      statusTarget.textContent='Original REST preview displayed; no exercise/morph approval.';
    }catch(e){
      statusTarget.textContent='Original preview not available: '+e.message;
    }
  };
  const onView=()=>{
    if(!session)return;
    try{session.renderView(cameraSelector.value)}
    catch(e){statusTarget.textContent='Original review render blocked: '+e.message}
  };
  fileInput.addEventListener('change',onFile);
  cameraSelector.addEventListener('change',onView);
  return Object.freeze({
    dispose(){
      fileInput.removeEventListener('change',onFile);
      cameraSelector.removeEventListener('change',onView);
      session?.dispose();session=null;
    }
  });
}
