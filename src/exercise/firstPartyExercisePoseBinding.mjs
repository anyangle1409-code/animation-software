/**
 * G4d: first-party exercise text -> matching original model/rig/pose *binding*.
 *
 * A text intent MUST NOT silently select a motion for a different exercise,
 * piece of equipment, posture, handedness or grip. Work-authored source pose
 * metadata here is a declaration, NOT independently observed biomechanics.
 * The result is unapproved, diagnostic source-pose playback only.
 *
 * No network, vendor dependency, new poses, interpolator or physics engine.
 */
import {parseFirstPartyExerciseIntent}
  from './firstPartyExerciseIntent.mjs';
import {compileProvisionalPoseSequence}
  from '../viewer/firstPartyPrototypePoseSequence.mjs';

export const HGPT_INTENT_CLIP_DECLARATION_KIND=
  'hgpt-first-party-clip-intent-declaration-v1';
export const HGPT_BOUND_EXERCISE_KIND=
  'hgpt-first-party-bound-exercise-diagnostic-v1';
const fail=s=>{throw new RangeError('Exercise-to-pose binding rejected: '+s);};
const need=(ok,s)=>{if(!ok)fail(s);};
const record=o=>o!==null&&typeof o==='object'&&!Array.isArray(o)&&
  (Object.getPrototypeOf(o)===Object.prototype||
   Object.getPrototypeOf(o)===null);
const exact=(o,fields,name)=>{
  need(record(o)&&Object.keys(o).length===fields.length&&
    Object.keys(o).every(k=>fields.includes(k))&&
    fields.every(k=>Object.hasOwn(o,k)),
    name+' must have exact explicit fields');
};
const has=o=>Object.hasOwn;
const label=s=>typeof s==='string' && /^[a-zA-Z0-9_-]{1,80}$/.test(s);
const boundFrames=new WeakMap();
const PARAMETERS=Object.freeze(['equipment','laterality','posture','grip']);

function parseDeclaration(decl,intent,model,clip){
  exact(decl,['kind','sourcePoseSetId','candidateId','sourceSha256',
    'exerciseId','parameters','statedOrigin','biomechanicsReview'],
    'clip declaration');
  need(decl.kind===HGPT_INTENT_CLIP_DECLARATION_KIND,
    'unsupported clip-to-intent schema');
  need(label(decl.sourcePoseSetId),
    'bounded explicit source pose set identifier required');
  need(decl.candidateId===model.candidateId &&
    decl.sourceSha256===model.sourceSha256 &&
    decl.exerciseId===intent.source.movementId &&
    decl.exerciseId===clip.exerciseId,
    'source pose identity, exercise and model SHA must match EXACTLY');
  need(decl.statedOrigin==='WORK_AUTHORED_SOURCE_CLAIM' &&
    decl.biomechanicsReview==='UNVERIFIED_DIAGNOSTIC',
    'source authorship is a declaration, not externally verified evidence');
  exact(decl.parameters,PARAMETERS,'authored clip parameters');
  for(const key of PARAMETERS){
    need(decl.parameters[key]===intent.source[key],
      'explicit '+key+' request differs from authored clip');
  }
}

/**
 * Input: original user text + previously G4-verified source model + actual
 * G4b-authored raw clip + explicit claim of Work's intended exercise variant.
 * Return: defensible source-identity matched DIAGNOSTIC ONLY binding. Not a
 * statement that supplied poses really satisfy the command biomechanics.
 */
export function bindFirstPartyExerciseToDiagnosticPose(
  userCommand,originalModel,authoredClip,authoredDeclaration
){
  const intent=parseFirstPartyExerciseIntent(userCommand);
  need(originalModel?.audit?.allGLBPrimitivesDecodedAndBound===true,
    'previously source-validated G4 model required');
  need(record(authoredClip),
    'complete raw Work-authored source clip required');
  parseDeclaration(authoredDeclaration,intent,originalModel,authoredClip);
  // The G4b source-bound parser must accept EVERY rigid world matrix,
  // ordered sample timestamp, original model SHA, and named runtime joint;
  // fabricated G4 models or foreign GLBs are explicitly rejected there.
  const compiled=compileProvisionalPoseSequence(originalModel,authoredClip);
  need(compiled.exerciseId===intent.source.movementId &&
    compiled.candidateId===originalModel.candidateId &&
    compiled.sourceSha256===originalModel.sourceSha256,
    'compiled source clip must preserve original exercise and model identity');
  need(compiled.audit.productionClipApproved===false &&
    compiled.audit.wholeBodyExerciseAccuracyAccepted===false,
    'cannot promote unreviewed human motion');
  const frames=compiled.frames.map((f)=>({
    timeSeconds:f.timeSeconds,
    // Copy every source joint palette to prevent later mutation of the user
    // input, compiled clip, or a returned frame from changing the binding.
    palette:new Float32Array(f.sourceOrderedWorldMatrices),
  }));
  const result=Object.freeze({
    kind:HGPT_BOUND_EXERCISE_KIND,
    status:'BOUND_DIAGNOSTIC_ONLY',
    sourcePoseSetId:authoredDeclaration.sourcePoseSetId,
    exerciseId:intent.source.movementId,
    candidateId:compiled.candidateId,
    sourceSha256:compiled.sourceSha256,
    requestedParameters:Object.freeze(Object.fromEntries(
      PARAMETERS.map(k=>[k,intent.source[k]])
    )),
    runtimeJointNames:Object.freeze([...compiled.runtimeBoneNames]),
    frameCount:frames.length,
    durationSeconds:compiled.durationSeconds,
    requiredBiomechanicsVerification:Object.freeze([
      ...intent.requiredBiomechanicsVerification
    ]),
    audit:Object.freeze({
      sourceGLBExactSHAAndBindValidated:true,
      everyPoseFrameOriginalRigNumericallyScreened:true,
      textAndClipExerciseIdMatch:true,
      explicitEquipmentLateralityPostureAndGripMatch:true,
      sourcePoseAuthorshipIndependentlyVerified:false,
      realHumanMotionIndependentlyVerified:false,
      physiologicalRangeOfMotionAccepted:false,
      realEquipmentContactOrDynamicsVerified:false,
      movementWasGeneratedByText:false,
      productionReady:false,
    }),
  });
  boundFrames.set(result,frames);
  return result;
}

/** Exact source pose sample only; returns an independent copied palette. */
export function getBoundDiagnosticExerciseFrame(binding,index){
  const frames=boundFrames.get(binding);
  need(Boolean(frames),'validated G4d exercise binding handle required');
  need(Number.isSafeInteger(index)&&index>=0&&index<frames.length,
    'existing whole-number authored source pose index required');
  const item=frames[index];
  return Object.freeze({
    timeSeconds:item.timeSeconds,
    sourceJointOrderedPalette:new Float32Array(item.palette),
    interpolationPerformed:false,
    realHumanKinematicsApproved:false,
  });
}
