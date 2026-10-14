// Wholly synthetic nonhuman fixture; cannot demonstrate exercise biomechanics.
import {buildSyntheticFirstPartyGlb} from './buildSyntheticFirstPartyGlb.mjs';
import {HGPT_PROTOTYPE_HANDOFF_KIND as MODEL_KIND,digestOriginalGlbSha256,validateProvisionalModelHandoff} from '../../src/viewer/firstPartyPrototypeModelHandoff.mjs';
import {HGPT_PROTOTYPE_CLIP_KIND as CLIP_KIND} from '../../src/viewer/firstPartyPrototypePoseSequence.mjs';
import {HGPT_INTENT_CLIP_DECLARATION_KIND as DECL_KIND} from '../../src/exercise/firstPartyExercisePoseBinding.mjs';
const I=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const T=x=>[1,0,0,0,0,1,0,0,0,0,1,0,x,0,0,1];
export async function buildSyntheticExerciseHandoff(command='left arm standing dumbbell shoulder press neutral grip'){
  const glb=buildSyntheticFirstPartyGlb();
  const sha=await digestOriginalGlbSha256(glb);
  const model=await validateProvisionalModelHandoff(glb,{
    kind:MODEL_KIND,candidateId:'OriginalFunctionalPrototype',
    status:'PROTOTYPE_ONLY',
    glb:{sha256:sha,layout:'single',
      sourceFeatures:{flatColors:false,uv0:false,normals:false}},
    frame:{unit:'metre',up:'Y',handedness:'right',
      basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
    rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
      thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
    rig:{sourceToRuntimeBone:{
      test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
      runtimeBoneNames:['upperarm_l','forearm_l'],
      restWorldByRuntimeBone:{upperarm_l:I(),forearm_l:I()},
      lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED'},
    releaseApproved:false
  });
  const clip={
    kind:CLIP_KIND,candidateId:model.candidateId,sourceSha256:model.sourceSha256,
    exerciseId:'overhead_press',approvalStatus:'DIAGNOSTIC_ONLY',
    durationSeconds:1,
    frames:[
      {timeSeconds:0,posedWorldByRuntimeBone:{upperarm_l:I(),forearm_l:I()}},
      {timeSeconds:.5,posedWorldByRuntimeBone:{
        upperarm_l:T(.25),forearm_l:T(.35)}},
      {timeSeconds:1,posedWorldByRuntimeBone:{
        upperarm_l:T(.5),forearm_l:T(.7)}},
    ]
  };
  const declaration={
    kind:DECL_KIND,sourcePoseSetId:'OriginalOverheadDiagnosticA01',
    candidateId:model.candidateId,
    sourceSha256:model.sourceSha256,exerciseId:'overhead_press',
    parameters:{equipment:'dumbbell',laterality:'left',posture:'standing',grip:'neutral'},
    statedOrigin:'WORK_AUTHORED_SOURCE_CLAIM',
    biomechanicsReview:'UNVERIFIED_DIAGNOSTIC',
  };
  return {command,model,clip,declaration,glb};
}
