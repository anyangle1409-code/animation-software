/**
 * G4b: bounded, first-party OFFLINE sampled motion compatibility for Work's
 * provisional original human rig; NOT a biomechanical movement validator.
 *
 * Each source frame contains explicit world transforms of all named runtime
 * joints. Previous G4 SHA/rest-binder preserves original source skin palette
 * order. No bone placement, animation interpolator, CT source, vendor plugin,
 * third-party library or network request is used here.
 */
import {HGPT_PROTOTYPE_HANDOFF_KIND,packProvisionalModelPose}
  from './firstPartyPrototypeModelHandoff.mjs';

export const HGPT_PROTOTYPE_CLIP_KIND='hgpt-provisional-human-pose-frames-v1';
const fail=m=>{throw new RangeError('G4b pose clip rejected: '+m);};
const assert=(v,m)=>{if(!v)fail(m);};
const record=v=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&
  (Object.getPrototypeOf(v)===Object.prototype||Object.getPrototypeOf(v)===null);
const exactly=(x,fields,name)=>{
  assert(record(x)&&Object.keys(x).length===fields.length&&
    Object.keys(x).every(k=>fields.includes(k))&&
    fields.every(k=>Object.hasOwn(x,k)),name+' must have exact fields');
};
const label=v=>typeof v==='string'&&v.length>0&&v.length<=80&&
  /^[a-zA-Z0-9_-]+$/.test(v);
const seqVerified=new WeakSet();

/**
 * Never interpolates world matrices: naive linear matrix interpolation
 * violates rotations and can shear/refelect the human. Caller must supply
 * properly-authored time samples or separately verified interpolation.
 */
export function compileProvisionalPoseSequence(model,clip){
  assert(model?.kind===HGPT_PROTOTYPE_HANDOFF_KIND&&
    typeof model.sourceSha256==='string'&&
    Array.isArray(model.runtimeJointNames),'previous G4 prototype required');
  exactly(clip,['kind','candidateId','sourceSha256','exerciseId',
    'approvalStatus','durationSeconds','frames'],'clip');
  assert(clip.kind===HGPT_PROTOTYPE_CLIP_KIND,'unsupported clip schema');
  assert(clip.candidateId===model.candidateId &&
    clip.sourceSha256===model.sourceSha256,
    'model SHA/candidate mismatch; do not animate a different character');
  assert(label(clip.exerciseId),'explicit exercise identity required');
  assert(clip.approvalStatus==='DIAGNOSTIC_ONLY',
    'this interface cannot approve whole-body exercise biomechanics');
  const duration=clip.durationSeconds;
  assert(Number.isFinite(duration)&&duration>=.05&&duration<=180,
    'finite .05..180 second duration required');
  assert(Array.isArray(clip.frames)&&clip.frames.length>=2&&
    clip.frames.length<=600,'2..600 explicit frames required');
  const names=model.runtimeJointNames;
  assert(names.length>=1&&names.length<=128&&new Set(names).size===names.length,
    'invalid source-bound runtime joint inventory');
  let previous=-Infinity,previousPacked=null,maxTranslationStep=0,maxAngularStep=0;
  const frames=[];
  for(const [i,frame]of clip.frames.entries()){
    exactly(frame,['timeSeconds','posedWorldByRuntimeBone'],'frame '+i);
    const time=frame.timeSeconds;
    assert(Number.isFinite(time)&&time>=0&&time<=duration&&
      time>previous+1e-8,'frame timestamps must be strictly increasing and in duration');
    if(i===0)assert(time===0,'first frame must start at 0');
    if(i===clip.frames.length-1)assert(Math.abs(time-duration)<1e-8,
      'final frame must reach exact exercise duration');
    const byName=frame.posedWorldByRuntimeBone;
    assert(record(byName)&&Object.keys(byName).length===names.length&&
      names.every(n=>Object.hasOwn(byName,n)),'exact runtime world pose joints required');
    // G4 genuine binder validates all rigid world matrices, source palette
    // order and no source suffix or invented anatomical coordinate conversion.
    const packed=packProvisionalModelPose(model,byName);
    assert(packed.length===names.length*16,'packed source skin palette incomplete');
    for(let j=0;j<packed.length;j+=16){
      assert(Math.max(Math.abs(packed[j+12]),Math.abs(packed[j+13]),
        Math.abs(packed[j+14]))<=10,
        'world translation exceeds broad software guard (not a ROM limit)');
      if(previousPacked){
        const delta=Math.hypot(
          packed[j+12]-previousPacked[j+12],
          packed[j+13]-previousPacked[j+13],
          packed[j+14]-previousPacked[j+14]);
        maxTranslationStep=Math.max(maxTranslationStep,delta);
        // Relative proper rotation R_prev^T * R_current:
        let trace=0;
        for(let axis=0;axis<3;axis++){
          const k=axis*4;
          trace+=previousPacked[k]*packed[k]+
                 previousPacked[k+1]*packed[k+1]+
                 previousPacked[k+2]*packed[k+2];
        }
        const angle=Math.acos(Math.max(-1,Math.min(1,(trace-1)/2)));
        maxAngularStep=Math.max(maxAngularStep,angle);
      }
    }
    frames.push(Object.freeze({timeSeconds:time,sourceOrderedWorldMatrices:packed}));
    previousPacked=packed;
    previous=time;
  }
  const result=Object.freeze({
    kind:HGPT_PROTOTYPE_CLIP_KIND,
    candidateId:clip.candidateId,sourceSha256:clip.sourceSha256,
    exerciseId:clip.exerciseId,durationSeconds:duration,
    runtimeBoneNames:Object.freeze([...names]),
    frames:Object.freeze(frames),
    audit:Object.freeze({
      allFramesOriginalSkinOrderNumericallyScreened:true,
      sampledFrameCount:frames.length,
      maxConsecutiveJointTranslationMetres:maxTranslationStep,
      maxConsecutiveJointRotationRadians:maxAngularStep,
      frameMatricesInterpolated:false,
      physiologicalRangeOfMotionApproved:false,
      loadDependentPhysicsVerified:false,
      realHumanVideoComparisonPassed:false,
      wholeBodyExerciseAccuracyAccepted:false,
      productionClipApproved:false,
    }),
  });
  seqVerified.add(result);
  return result;
}

/** Exact authored keyframe only. Never round time or fabricate in-betweens. */
export function getProvisionalPoseFrame(clip,index){
  assert(seqVerified.has(clip),'validated G4b clip required');
  assert(Number.isSafeInteger(index)&&index>=0&&index<clip.frames.length,
    'existing integer keyframe index required; no implicit interpolation');
  return clip.frames[index];
}
