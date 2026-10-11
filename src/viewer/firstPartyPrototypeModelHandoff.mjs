/**
 * G4: early ORIGINAL-v1 human-model integration boundary, first-party only.
 *
 * This gate accepts project-authored GLB bytes plus an explicit provisional
 * Blender/Work export manifest. It binds source joints to named runtime bones
 * and checks the entire asset digest/rest matrix contract, WITHOUT adjusting
 * any joint, assuming anatomical laterality or approving the human model.
 * Only the existing narrow GLB subset is supported (one skinned primitive,
 * or 2..8 primitives over 1..4 meshes sharing one skin).
 */
import {parseRestrictedSkinnedGlb} from './firstPartyGlbSkinnedGeometry.mjs';
import {parseRestrictedBatchedSkinnedGlb} from './firstPartyGlbSkinnedBatches.mjs';
import {validateNativeGLBToRigBinding,packMappedWorldPalette}
  from './firstPartyGlbRigBindingContract.mjs';

export const HGPT_PROTOTYPE_HANDOFF_KIND='hgpt-provisional-original-model-handoff-v1';
const MAX_GLB_BYTES=32*1024*1024;
const verified=new WeakMap();
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const record=v=>v!==null && typeof v==='object' &&
  !Array.isArray(v) && (Object.getPrototypeOf(v)===Object.prototype ||
  Object.getPrototypeOf(v)===null);
const fail=reason=>{throw new RangeError('Provisional model handoff rejected: '+reason);};
const requireThat=(yes,reason)=>{if(!yes)fail(reason);};
const exactly=(o,keys,label)=>{
  requireThat(record(o),label+' object required');
  requireThat(Object.keys(o).length===keys.length &&
    Object.keys(o).every(k=>keys.includes(k)) &&
    keys.every(k=>own(o,k)),label+' fields must be exact');
};
const safeLabel=v=>typeof v==='string' && v.length>0 && v.length<=80 &&
  v!=='__proto__' && v!=='constructor' && v!=='prototype' &&
  !v.includes('\0') && !/[\x00-\x1f]/.test(v);

/** Browser WebCrypto; Node 24 uses its built-in WebCrypto. No npm packages. */
export async function digestOriginalGlbSha256(glb){
  requireThat(glb instanceof ArrayBuffer && glb.byteLength>=28 &&
    glb.byteLength<=MAX_GLB_BYTES,'bounded complete GLB ArrayBuffer required');
  requireThat(globalThis.crypto?.subtle?.digest,
    'WebCrypto SHA-256 support required; never skip asset verification');
  const hash=await globalThis.crypto.subtle.digest('SHA-256',glb);
  return Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
}

/**
 * Work-generated manifest requirements are intentionally strict. Claims of
 * project authorship are NOT evidence of independently reviewed source rights.
 */
function checkManifest(manifest){
  exactly(manifest,['kind','candidateId','status','glb','frame','rights','rig',
    'releaseApproved'],'manifest');
  requireThat(manifest.kind===HGPT_PROTOTYPE_HANDOFF_KIND,'unknown schema');
  requireThat(safeLabel(manifest.candidateId),'candidate ID missing/unsafe');
  requireThat(manifest.status==='PROTOTYPE_ONLY' && manifest.releaseApproved===false,
    'early handoff cannot claim production or clinical approval');
  exactly(manifest.glb,['sha256','layout','sourceFeatures'],'GLB');
  requireThat(/^[a-f0-9]{64}$/.test(manifest.glb.sha256),
    'lowercase SHA-256 of exact source GLB bytes required');
  requireThat(manifest.glb.layout==='single'||manifest.glb.layout==='batched',
    'layout must be single or batched');
  exactly(manifest.glb.sourceFeatures,['flatColors','uv0','normals'],
    'GLB source features');
  requireThat(Object.values(manifest.glb.sourceFeatures)
    .every(v=>typeof v==='boolean'),'GLB features must be explicit booleans');
  requireThat(manifest.glb.layout==='batched' ||
    Object.values(manifest.glb.sourceFeatures).every(v=>!v),
    'single primitive has no opt-in source feature adapter');
  exactly(manifest.frame,['unit','up','handedness','basisStatus'],'frame');
  requireThat(manifest.frame.unit==='metre' && manifest.frame.up==='Y' &&
    manifest.frame.handedness==='right' &&
    manifest.frame.basisStatus==='DECLARED_NOT_INDEPENDENTLY_REGISTERED',
    'source frame must be explicit glTF metre/Y/right-handed and unverified');
  exactly(manifest.rights,['projectAuthoredClaim','medicalSourceGeometryEmbedded',
    'thirdPartyCharacterGeometryEmbedded','independentRightsReview'],'rights');
  requireThat(manifest.rights.projectAuthoredClaim===true &&
    manifest.rights.medicalSourceGeometryEmbedded===false &&
    manifest.rights.thirdPartyCharacterGeometryEmbedded===false &&
    manifest.rights.independentRightsReview===false,
    'provisional source-rights claims must be explicit and not falsely approved');
  exactly(manifest.rig,['sourceToRuntimeBone','runtimeBoneNames',
    'restWorldByRuntimeBone','lateralityStatus'],'rig');
  requireThat(manifest.rig.lateralityStatus==='EXPLICIT_MAPPING_UNVERIFIED',
    'no inferred bone suffix/left-right equivalence');
  requireThat(record(manifest.rig.sourceToRuntimeBone) &&
    record(manifest.rig.restWorldByRuntimeBone) &&
    Array.isArray(manifest.rig.runtimeBoneNames) &&
    manifest.rig.runtimeBoneNames.length>=1 &&
    manifest.rig.runtimeBoneNames.length<=128 &&
    manifest.rig.runtimeBoneNames.every(safeLabel) &&
    new Set(manifest.rig.runtimeBoneNames).size===
      manifest.rig.runtimeBoneNames.length,
    'unique runtime rig names/mapping/rest transforms required');
  requireThat(Object.keys(manifest.rig.restWorldByRuntimeBone).length===
    manifest.rig.runtimeBoneNames.length &&
    manifest.rig.runtimeBoneNames.every(name=>
      own(manifest.rig.restWorldByRuntimeBone,name)),
    'exactly one rest matrix per declared runtime bone required');
}

/**
 * Returns a PROTOTYPE-ONLY typed scene and a stable pose-packing boundary.
 * All source bytes are snapshotted before the async digest to prevent caller
 * mutation between hash verification and decoding. No network/Three/Blender.
 */
export async function validateProvisionalModelHandoff(input,manifest){
  requireThat(input instanceof ArrayBuffer && input.byteLength>=28 &&
    input.byteLength<=MAX_GLB_BYTES,'bounded GLB ArrayBuffer required');
  checkManifest(manifest);
  const snapshot=input.slice(0);
  const sha=await digestOriginalGlbSha256(snapshot);
  requireThat(sha===manifest.glb.sha256,
    'source asset SHA-256 mismatch; do not reuse stale rig metadata');
  const scene=manifest.glb.layout==='single' ?
    {batches:[{parsed:parseRestrictedSkinnedGlb(snapshot)}]} :
    parseRestrictedBatchedSkinnedGlb(snapshot,{
      allowSourceFlatColors:manifest.glb.sourceFeatures.flatColors,
      allowSourceUV0:manifest.glb.sourceFeatures.uv0,
      allowSourceNormals:manifest.glb.sourceFeatures.normals,
    });
  const parts=scene.batches;
  requireThat(parts.length>0 && parts.length<=8,'scene primitive budget exceeded');
  const options={
    sourceToCanonical:manifest.rig.sourceToRuntimeBone,
    allowedCanonicalNames:manifest.rig.runtimeBoneNames,
    canonicalRestWorldByBone:manifest.rig.restWorldByRuntimeBone,
  };
  const plans=parts.map(({parsed})=>validateNativeGLBToRigBinding(parsed,options));
  const order=plans[0].orderedCanonicalBoneNames;
  requireThat(plans.every(p=>p.orderedCanonicalBoneNames.length===order.length &&
    p.orderedCanonicalBoneNames.every((name,i)=>name===order[i])),
    'source skin order inconsistent across primitives');
  const maxRestResidual=Math.max(...plans.map(p=>p.maximumMatrixResidual));
  const result=Object.freeze({
    kind:HGPT_PROTOTYPE_HANDOFF_KIND,
    candidateId:manifest.candidateId,
    sourceSha256:sha,
    scene,
    numberOfPrimitives:parts.length,
    sourceJointNames:Object.freeze([...plans[0].orderedSourceJointNames]),
    runtimeJointNames:Object.freeze([...order]),
    audit:Object.freeze({
      actualGLBBytesHashed:true,
      sourceBytesCopiedBeforeAsyncHash:true,
      allGLBPrimitivesDecodedAndBound:true,
      explicitRestWorldInverseBindNumericalParity:true,
      maximumRestMatrixResidual:maxRestResidual,
      sourceFramePhysicallyRegistered:false,
      verifiedAnatomicalLaterality:false,
      independentlyVerifiedSourceRights:false,
      medicallyApprovedHumanSkeleton:false,
      realisticWholeBodyDeformationVerified:false,
      modelProductionReady:false,
      glbHasExternalNetworkDependency:false,
    }),
  });
  verified.set(result,plans[0]);
  return result;
}

/** Explicit source-joint order; cannot accept forged or unverified handles. */
export function packProvisionalModelPose(handoff,posedWorldByRuntimeBone){
  const plan=verified.get(handoff);
  requireThat(plan!==undefined,'only actual validated prototype handles can pose');
  return packMappedWorldPalette(plan,posedWorldByRuntimeBone);
}
