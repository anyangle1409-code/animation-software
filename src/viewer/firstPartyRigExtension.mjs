/** Versioned metadata/pose compatibility only. Does not approve or load a GLB.
 * Existing SHA-pinned 67-joint importer and rest-only viewer stay unchanged.
 * Helpers require complete authored world transforms; no guessed half-motion.
 */
import {invertRigidBind} from './firstPartyIndexedSkinnedMesh.mjs';
export const RIG_EXTENSION_KIND='hgpt-provisional-rig-extension-v2';
const compiled=new WeakSet();
const requireThat=(ok,msg)=>{if(!ok)throw new RangeError('Rig extension: '+msg);};
const record=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&
  [Object.prototype,null].includes(Object.getPrototypeOf(x));
const exact=(x,keys)=>requireThat(record(x)&&Object.keys(x).length===keys.length&&
  keys.every(k=>Object.hasOwn(x,k)),'exact fields required');
const label=x=>typeof x==='string'&&/^[A-Za-z0-9_-]{1,80}$/.test(x)&&
  !['__proto__','constructor','prototype'].includes(x);
const sha=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const names=(x,max)=>Array.isArray(x)&&x.length<=max&&x.every(label)&&new Set(x).size===x.length;

export function compileRigExtension(base,manifest,{reviewOnly=false}={}){
  requireThat(reviewOnly===true,'explicit review-only opt-in required');
  exact(base,['sourceSha256','jointNames']);
  requireThat(sha(base.sourceSha256)&&names(base.jointNames,67)&&base.jointNames.length===67,
    'explicit 67-joint baseline required');
  exact(manifest,['kind','status','baseSourceSha256','sourceSha256','baseJointNames',
    'extensions','morphNames','releaseApproved']);
  requireThat(manifest.kind===RIG_EXTENSION_KIND&&manifest.status==='REVIEW_ONLY'&&
    manifest.releaseApproved===false,'v2 review-only schema required');
  requireThat(manifest.baseSourceSha256===base.sourceSha256&&sha(manifest.sourceSha256),
    'source SHA declarations required');
  requireThat(names(manifest.baseJointNames,67)&&manifest.baseJointNames.length===67&&
    base.jointNames.every((n,i)=>n===manifest.baseJointNames[i]),'baseline order must be preserved');
  requireThat(Array.isArray(manifest.extensions)&&manifest.extensions.length<=61,
    'maximum 128 joints including baseline');
  requireThat(names(manifest.morphNames,16),'maximum 16 uniquely named corrective morphs');
  const jointNames=[...base.jointNames],extensions=[];
  for(const entry of manifest.extensions){
    exact(entry,['name','parent','role']);
    requireThat(label(entry.name)&&!jointNames.includes(entry.name),'unique joint name required');
    requireThat(jointNames.includes(entry.parent),'parent must precede appended child');
    requireThat(['shoulder_helper','individual_toe'].includes(entry.role),'unknown extension role');
    extensions.push(Object.freeze({...entry}));jointNames.push(entry.name);
  }
  const result=Object.freeze({kind:RIG_EXTENSION_KIND,status:'REVIEW_ONLY',
    baseSourceSha256:base.sourceSha256,sourceSha256:manifest.sourceSha256,
    jointNames:Object.freeze(jointNames),extensions:Object.freeze(extensions),
    morphNames:Object.freeze([...manifest.morphNames]),
    sourceBytesVerified:false,anatomicalApproval:false,humanMovementApproved:false,releaseApproved:false});
  compiled.add(result);return result;
}

export function packExtendedReviewPose(contract,frame){
  requireThat(compiled.has(contract),'compiled review contract required');
  exact(frame,['sourceSha256','posedWorldByJoint','morphWeights']);
  requireThat(frame.sourceSha256===contract.sourceSha256,'pose/source SHA declaration mismatch');
  exact(frame.posedWorldByJoint,contract.jointNames);
  exact(frame.morphWeights,contract.morphNames);
  const posedWorld=new Float32Array(contract.jointNames.length*16);
  for(const [i,name] of contract.jointNames.entries()){
    const m=frame.posedWorldByJoint[name];
    requireThat((Array.isArray(m)||m instanceof Float32Array)&&m.length===16&&
      Array.from(m).every(Number.isFinite),'complete finite world matrix required');
    invertRigidBind(m); // existing first-party rigid/no reflection/shear/scale validation
    requireThat(Math.max(Math.abs(m[12]),Math.abs(m[13]),Math.abs(m[14]))<=10,
      'world translation exceeds software guard, not an anatomical limit');
    posedWorld.set(m,i*16);
  }
  const morphWeights=new Float32Array(contract.morphNames.length);
  for(const [i,name] of contract.morphNames.entries()){
    const w=frame.morphWeights[name];
    requireThat(Number.isFinite(w)&&w>=0&&w<=1,'corrective weight must be within 0..1');
    morphWeights[i]=w;
  }
  return {posedWorld,morphWeights,productionApproved:false};
}
