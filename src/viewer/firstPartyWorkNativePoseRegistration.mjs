/**
 * G4l: register Work-authored Blender Z-up ROW-MAJOR absolute source WORLD poses
 * against an independently source-SHA-verified glTF Y-up COLUMN-MAJOR rig.
 *
 * The actual W1 Blender glTF exporter uses left-multiplication by Rx(-90°)
 * for WORLD joint transforms: glTFWorld = BlenderToGLTF * NativeWorld.
 * This is verified independently for every source rest bone, not assumed
 * from vague frame conventions or a bone-name heuristic. For skin palettes:
 * glTFPalette = BlenderToGLTF * NativeSkinPalette * GLTFToBlender.
 *
 * Source contract is PROVISIONAL SHOULDER ONLY. "arm_rotation_from_rest"
 * does NOT mean absolute measured humerothoracic elevation or realism.
 */
import {multiplyNativeMat4}
  from './firstPartyWebGL2SkeletonPreview.mjs';
import {packProvisionalModelPose,HGPT_PROTOTYPE_HANDOFF_KIND}
  from './firstPartyPrototypeModelHandoff.mjs';
import {HGPT_GLTF_REST_WORLD_KIND}
  from './firstPartyOriginalGltfRestWorld.mjs';

export const HGPT_WORK_NATIVE_POSE_BRIDGE_KIND=
  'hgpt-original-work-zup-to-gltf-yup-authored-pose-v1';
const WIDTH=6;
const EPS=.0001;
const fail=s=>{throw new RangeError('Original Work pose basis rejected: '+s)};
const need=(yes,s)=>{if(!yes)fail(s)};
const rec=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const own=(obj,name)=>Object.prototype.hasOwnProperty.call(obj,name);
const B=new Float32Array([
  1,0,0,0,
  0,0,-1,0,
  0,1,0,0,
  0,0,0,1
]);
const Bi=new Float32Array([
  1,0,0,0,
  0,0,1,0,
  0,-1,0,0,
  0,0,0,1
]);
const UNIT=new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
const cache=new WeakMap();
function sourceRowsToColumnMajor(nativeRows){
  need(Array.isArray(nativeRows)&&nativeRows.length===4 &&
    nativeRows.every(row=>Array.isArray(row)&&row.length===4&&
      row.every(x=>typeof x==='number'&&Number.isFinite(x))),
    '4x4 finite original Work ROW MAJOR matrix required');
  need(nativeRows[3].every((x,i)=>Math.abs(x-(i===3?1:0))<=EPS),
    'non-affine original native source matrix');
  const out=new Float32Array(16);
  // Matrix memory layout change only: no implicit basis or topology rewrite.
  for(let r=0;r<4;r++)for(let c=0;c<4;c++)
    out[r+c*4]=nativeRows[r][c];
  return out;
}
function worst(a,b){
  need(a.length===16&&b.length===16,'complete 4x4 matrix pair required');
  let maximum=0;
  for(let i=0;i<16;i++)maximum=Math.max(maximum,Math.abs(a[i]-b[i]));
  return maximum;
}
const toGltfWorld=native=>multiplyNativeMat4(B,
  sourceRowsToColumnMajor(native));
const toGltfSkin=native=>multiplyNativeMat4(
  multiplyNativeMat4(B,sourceRowsToColumnMajor(native)),Bi);

/**
 * Input Work manifest metadata and the real G4/G4j verified in-memory source
 * model/rig handle, not a parsed arbitrary user JSON pose file. Fails closed
 * unless REST and native skin palette independently match original GLB.
 */
export function registerWorkNativePoseSamplesToOriginalGLTF(
  sourceModel,sourceRest,workManifest
){
  need(sourceModel?.kind===HGPT_PROTOTYPE_HANDOFF_KIND&&
    sourceModel.audit?.allGLBPrimitivesDecodedAndBound===true&&
    sourceModel.audit?.provisionalLargeSceneDiagnosticOnly===true&&
    sourceModel.audit?.modelProductionReady===false &&
    typeof sourceModel.sourceSha256==='string' &&
    /^[a-f0-9]{64}$/.test(sourceModel.sourceSha256),
    'original verified source Work G4 pilot model handle required');
  need(sourceRest?.kind===HGPT_GLTF_REST_WORLD_KIND&&
    sourceRest.frame==='glTF_Y_UP_RIGHT_HANDED_METRES_COLUMN_MAJOR'&&
    sourceRest.productionReady===false&&
    sourceRest.nativeWorkZUpRowMajorPoseFramesIndependentlyRegistered===false,
    'independently derived original glTF source WORLD REST required');
  const names=sourceModel.runtimeJointNames;
  need(Array.isArray(names)&&names.length===WIDTH &&
    names.every((n,i)=>n===sourceRest.orderedSourceJointNames[i]) &&
    new Set(names).size===WIDTH,'exact original source joint order required');
  need(rec(workManifest)&&
    workManifest.candidate===sourceModel.candidateId &&
    workManifest.status==='PROVISIONAL_SHOULDER_ONLY_NOT_ORIGINAL_HUMAN' &&
    workManifest.anatomy_approved===false &&
    workManifest.motion_approved===false &&
    workManifest.production_approved===false &&
    typeof workManifest.native_frame==='string' &&
    workManifest.native_frame.includes('+Z superior')&&
    typeof workManifest.glb_frame==='string'&&
    workManifest.glb_frame.includes('Y-up conversion')&&
    rec(workManifest.files_sha256)&&
    workManifest.files_sha256['PROVISIONAL_FUNCTIONAL_SHOULDER_v1.glb']===
      sourceModel.sourceSha256,
    'Work unapproved W1 original model, native and GLB frame record required');
  need(rec(workManifest.rig_mapping) &&
    Object.keys(workManifest.rig_mapping).length===WIDTH &&
    names.every(n=>own(workManifest.rig_mapping,n)),
    'all six Work source bones must have exact anatomical identity mappings');
  const key='clavicle_left,scapula_left,humerus_left,clavicle_right,scapula_right,humerus_right';
  need(names.join(',')===key,'only declared original W1 shoulder layout may be registered');
  need(Array.isArray(workManifest.frames)&&
    workManifest.frames.length===7,
    'the original pinned Work W1 seven authored pose samples required');
  const first=workManifest.frames[0],last=workManifest.frames.at(-1);
  need(first.time_seconds===0&&
    first.authored_arm_rotation_from_rest_deg===0&&
    last.authored_arm_rotation_from_rest_deg===0,
    'explicit original neutral/return bookends required');
  const expectedAngles=[0,45,90,135,160,90,0];
  const sourceInverseBind=sourceModel.scene?.batches?.[0]?.parsed?.mesh?.inverseBindMatrices;
  need(sourceInverseBind instanceof Float32Array&&
    sourceInverseBind.length===WIDTH*16,
    'original verified GLB inverse bind matrices are required');
  const frames=[];
  let maxRest=0,maxNativePalette=0,maxZero=0;
  for(let i=0;i<workManifest.frames.length;i++){
    const frame=workManifest.frames[i];
    need(rec(frame)&&Number.isFinite(frame.time_seconds)&&
      frame.time_seconds>=0&&frame.time_seconds<=180 &&
      (i===0||frame.time_seconds>frames[i-1].timeSeconds) &&
      frame.authored_arm_rotation_from_rest_deg===expectedAngles[i] &&
      rec(frame.controls)&&Object.keys(frame.controls).length===WIDTH&&
      names.every(n=>own(frame.controls,n)),
      'exact ascending Work sample times, relative-from-rest angles and six controls required');
    const poses={};
    for(let j=0;j<WIDTH;j++){
      const name=names[j],c=frame.controls[name];
      need(rec(c)&&
        Array.isArray(c.rest_world_row_major)&&
        Array.isArray(c.pose_world_row_major)&&
        Array.isArray(c.skin_palette_native_row_major),
        'all three original Work authored matrices required for '+name);
      const nativeRest=toGltfWorld(c.rest_world_row_major),
        nativePose=toGltfWorld(c.pose_world_row_major);
      const sourceRestMatrix=sourceRest.sourceWorldRestByName[name];
      need(Array.isArray(sourceRestMatrix)&&sourceRestMatrix.length===16,
        'true source glTF rest matrix missing: '+name);
      const restErr=worst(nativeRest,sourceRestMatrix);
      maxRest=Math.max(maxRest,restErr);
      need(restErr<=EPS,
        'actual native Blender rest does not match source GLB Y-up rest: '+name);
      const matrix=sourceInverseBind.subarray(j*16,j*16+16);
      const gltfSkin=multiplyNativeMat4(nativePose,matrix);
      const nativeSkin=toGltfSkin(c.skin_palette_native_row_major);
      const skinErr=worst(gltfSkin,nativeSkin);
      maxNativePalette=Math.max(maxNativePalette,skinErr);
      need(skinErr<=EPS,
        'native authored skin palette disagrees with original source inverse bind: '+name);
      if(i===0||i===workManifest.frames.length-1){
        const zero=worst(gltfSkin,UNIT);
        maxZero=Math.max(maxZero,zero);
        need(zero<=EPS,'Work neutral/rest poses must return original source skin to identity');
      }
      poses[name]=nativePose;
    }
    // G4 private WeakMap source rig authority verifies full rigid source joints;
    // source model and bone order can't be forged solely with JSON claims.
    const palette=packProvisionalModelPose(sourceModel,poses);
    frames.push({timeSeconds:frame.time_seconds,
      authoredArmRotationFromRestDegrees:expectedAngles[i],
      posedWorldByBone:poses,palette});
  }
  const result=Object.freeze({
    kind:HGPT_WORK_NATIVE_POSE_BRIDGE_KIND,
    status:'REGISTERED_SOURCE_POSES_DIAGNOSTIC_ONLY',
    modelSha256:sourceModel.sourceSha256,
    candidateId:sourceModel.candidateId,
    originalFrameCount:frames.length,
    orderedSourceJointNames:Object.freeze([...names]),
    originalSampleTimesSeconds:Object.freeze(frames.map(f=>f.timeSeconds)),
    originalArmRotationFromRestDegrees:Object.freeze([...expectedAngles]),
    maximumNativeRestToGLTFWorldResidual:maxRest,
    maximumNativeSkinVsGLTFSkinResidual:maxNativePalette,
    maximumReturnToRestSkinResidual:maxZero,
    nativeZupToGLTFYupReferenceVerified:true,
    motionIsRelativeFromRestNotAbsoluteElevation:true,
    interpolationInvented:false,
    actualOriginalHumanSkeletalBiomechanicsVerified:false,
    actualMuscleSkinDeformationValidated:false,
    equipmentContactVerified:false,
    modelProductionReady:false,
  });
  cache.set(result,frames);
  return result;
}

export function readRegisteredWorkPoseFrame(handle,index){
  const frames=cache.get(handle);
  need(Boolean(frames),'only in-memory source validated registered motion handles accepted');
  need(Number.isSafeInteger(index)&&index>=0&&index<frames.length,
    'exact existing source authored sample index required (no interpolation)');
  const f=frames[index];
  return Object.freeze({
    timeSeconds:f.timeSeconds,
    authoredArmRotationFromRestDegrees:f.authoredArmRotationFromRestDegrees,
    sourceJointWorldPalette:new Float32Array(f.palette),
    actualHumanMotionClinicallyVerified:false,
    sourceFrameConversionApprovedNumerically:true,
    generatedNewMovement:false,
  });
}
