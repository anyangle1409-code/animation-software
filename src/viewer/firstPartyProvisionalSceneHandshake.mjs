/** First-party G4 prototype-only GLB scene handshake. No anatomy inference. */
import {parseRestrictedBatchedSkinnedGlb} from './firstPartyGlbSkinnedBatches.mjs';
import {validateNativeGLBToRigBinding,packMappedWorldPalette}
  from './firstPartyGlbRigBindingContract.mjs';
export const PROVISIONAL_SCENE_KIND='hgpt-g4-provisional-scene-v1';
const sessions=new WeakMap();
const check=(ok,msg)=>{if(!ok)throw new RangeError('G4 scene: '+msg);};
const abort=s=>{if(s?.aborted){const e=new Error('Cancelled');e.name='AbortError';throw e;}};
export async function openProvisionalScene({glb,manifest,signal}={}){
  abort(signal);
  check(glb instanceof ArrayBuffer,'raw GLB required');
  check(manifest?.status==='PROVISIONAL_FUNCTIONAL','provisional status required');
  check(manifest.coordinateFrame==='glTF2_RIGHT_HANDED_Y_UP_METRES',
    'explicit supported frame required');
  const parsed=parseRestrictedBatchedSkinnedGlb(glb,{
    allowSourceUV0:true,allowSourceNormals:true});
  check(parsed.jointNodeNames.length===manifest.sourceJointNames?.length&&
    parsed.jointNodeNames.every((n,i)=>n===manifest.sourceJointNames[i]),
    'source joint order mismatch');
  const options={
    sourceToCanonical:manifest.sourceToCanonical,
    allowedCanonicalNames:manifest.allowedCanonicalNames,
    canonicalRestWorldByBone:manifest.canonicalRestWorldByBone};
  const plans=parsed.batches.map(b=>validateNativeGLBToRigBinding(b.parsed,options));
  abort(signal);
  const scene=Object.freeze({kind:PROVISIONAL_SCENE_KIND,
    audit:Object.freeze({prototypeOnly:true,acceptedOriginalHuman:false})});
  sessions.set(scene,{parsed,plans,names:[...plans[0].orderedCanonicalBoneNames]});
  return scene;
}
