/**
 * G4p: strictly opt-in camera input for the authentic W1 Work shoulder GPU
 * diagnostic. This module never loads assets, creates poses or changes bones.
 * Only the seven separately registered source-authored samples may be shown.
 */
export const HGPT_W1_ORBIT_DIAGNOSTIC_KIND='hgpt-g4p-original-work-w1-orbit-diagnostic-v1';
export const HGPT_W1_SOURCE_SHA256=
  'fda9c5e653044988fd1e5c58fe352f074071c4be008eceba702bbbef96a4ea5f';
const fail=why=>{throw new RangeError('W1 orbit diagnostic rejected: '+why)};
const need=(yes,why)=>{if(!yes)fail(why)};
const clamp=(v,lo,hi)=>Math.min(hi,Math.max(lo,v));
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const pointerValid=e=>Number.isSafeInteger(e.pointerId)&&e.pointerId>=0&&
  finite(e.clientX)&&finite(e.clientY)&&
  Math.abs(e.clientX)<=1e6&&Math.abs(e.clientY)<=1e6;

export function createOriginalWorkOrbitCamera({canvas,model,registered,
  renderPose,diagnosticOptIn=false}={}){
  need(diagnosticOptIn===true,'explicit diagnostic opt-in required');
  need(model?.sourceSha256===HGPT_W1_SOURCE_SHA256&&
    model.kind==='hgpt-provisional-original-model-handoff-v1'&&
    model.numberOfPrimitives===18&&model.sourceJointNames?.length===6&&
    model.audit?.allGLBPrimitivesDecodedAndBound===true&&
    model.audit?.provisionalLargeSceneDiagnosticOnly===true&&
    model.audit?.independentlyVerifiedSourceRights===false&&
    model.audit?.modelProductionReady===false,
    'exact original SHA-bound provisional 18-part W1 model required');
  need(registered?.modelSha256===HGPT_W1_SOURCE_SHA256&&
    registered.status==='REGISTERED_SOURCE_POSES_DIAGNOSTIC_ONLY'&&
    registered.originalFrameCount===7&&
    registered.motionIsRelativeFromRestNotAbsoluteElevation===true&&
    registered.interpolationInvented===false&&
    registered.modelProductionReady===false,
    'seven authentic source-registered W1 poses required');
  need(canvas?.addEventListener&&canvas?.removeEventListener&&
    typeof renderPose==='function','canvas and native GPU render callback required');
  const target=Object.freeze([0,1.5,0]);
  let yaw=0,polar=Math.PI/2,distance=3.4,poseIndex=0,disposed=false;
  const pointers=new Map();
  const previousTouchAction=canvas.style?.touchAction;
  if(canvas.style)canvas.style.touchAction='none';
  const snapshot=()=>Object.freeze({
    kind:HGPT_W1_ORBIT_DIAGNOSTIC_KIND,
    sourceSha256:HGPT_W1_SOURCE_SHA256,
    poseIndex,eye:Object.freeze([
      target[0]+distance*Math.sin(polar)*Math.sin(yaw),
      target[1]+distance*Math.cos(polar),
      target[2]+distance*Math.sin(polar)*Math.cos(yaw)]),
    target,distance,yaw,polar,originalHumanMotionValidated:false,
    independentRightsReview:false,releaseApproved:false,
  });
  const draw=()=>{
    need(!disposed,'viewer disposed');
    const state=snapshot();
    const result=renderPose(state.poseIndex,{eye:state.eye,target:state.target});
    need(result?.drewAllOriginalPilotParts===true&&
      result.originalPrimitiveCount===18&&result.productionReady===false,
      'native original-source GPU draw incomplete');
    return state;
  };
  const pointerDown=e=>{
    if(disposed||(e.pointerType==='mouse'&&e.button!==0))return;
    if(!pointerValid(e))return;
    pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    try{canvas.setPointerCapture?.(e.pointerId)}catch{}
  };
  const pointerMove=e=>{
    if(disposed||!pointers.has(e.pointerId))return;
    if(!pointerValid(e))return;
    const old=pointers.get(e.pointerId);
    if(pointers.size===1){
      const height=Math.max(1,canvas.clientHeight||canvas.height||1);
      yaw=(yaw-(e.clientX-old.x)*Math.PI*2/height)%(Math.PI*2);
      polar=clamp(polar-(e.clientY-old.y)*Math.PI*2/height,.12,Math.PI-.12);
      pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    }else{
      const other=[...pointers.entries()].find(([id])=>id!==e.pointerId)?.[1];
      if(!other)return;
      const before=Math.hypot(old.x-other.x,old.y-other.y);
      const after=Math.hypot(e.clientX-other.x,e.clientY-other.y);
      if(before>1e-6&&after>1e-6)
        distance=clamp(distance*before/after,1.2,8);
      pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    }
    draw();
  };
  const pointerUp=e=>{
    pointers.delete(e.pointerId);
    if(canvas.hasPointerCapture?.(e.pointerId))
      canvas.releasePointerCapture?.(e.pointerId);
  };
  const wheel=e=>{
    if(disposed)return;
    e.preventDefault?.();
    if(!finite(e.deltaY))return;
    distance=clamp(distance*Math.exp(clamp(e.deltaY,-500,500)*.0015),1.2,8);
    draw();
  };
  canvas.addEventListener('pointerdown',pointerDown);
  canvas.addEventListener('pointermove',pointerMove);
  canvas.addEventListener('pointerup',pointerUp);
  canvas.addEventListener('pointercancel',pointerUp);
  canvas.addEventListener('wheel',wheel,{passive:false});
  return Object.freeze({
    kind:HGPT_W1_ORBIT_DIAGNOSTIC_KIND,
    draw,
    snapshot,
    setPoseIndex(index){
      need(!disposed,'viewer disposed');
      need(Number.isSafeInteger(index)&&index>=0&&index<7,
        'only exact authored pose sample indices 0..6 supported');
      const previous=poseIndex;
      poseIndex=index;
      try{return draw()}catch(error){poseIndex=previous;throw error}
    },
    dispose(){
      if(disposed)return;
      disposed=true;pointers.clear();
      for(const [event,handler] of [
        ['pointerdown',pointerDown],['pointermove',pointerMove],
        ['pointerup',pointerUp],['pointercancel',pointerUp],['wheel',wheel]])
        canvas.removeEventListener(event,handler);
      if(canvas.style)canvas.style.touchAction=previousTouchAction;
    },
  });
}
