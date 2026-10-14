/** Bounded sparse corrective reference path. Prototype opt-in only.
 * Additive glTF POSITION/NORMAL deltas precede existing LBS; no pose drivers
 * or anatomical geometry synthesized. Actual human corrective acceptance is separate.
 */
import {validateNativeSkinnedMesh} from './firstPartyIndexedSkinnedMesh.mjs';
const handles=new WeakMap();
const must=(ok,msg)=>{if(!ok)throw new RangeError('Diagnostic morphs: '+msg);};
const label=x=>typeof x==='string'&&/^[A-Za-z0-9_-]{1,80}$/.test(x)&&
  !['__proto__','constructor','prototype'].includes(x);
const exact=(x,keys)=>must(x&&typeof x==='object'&&!Array.isArray(x)&&
  [Object.prototype,null].includes(Object.getPrototypeOf(x))&&
  Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k)),'exact fields required');
const copyMesh=m=>Object.fromEntries(['positions','jointIndices','weights','indices','inverseBindMatrices']
  .map(k=>[k,m[k].slice()]));
function sparse(x,n,limit){
  exact(x,['indices','deltas']);
  must(x.indices instanceof Uint32Array&&x.deltas instanceof Float32Array&&
    x.indices.length<=n&&x.deltas.length===x.indices.length*3,'bounded typed sparse arrays required');
  let last=-1;
  for(const i of x.indices){must(i>last&&i<n,'sparse indices must increase and stay in range');last=i;}
  for(const d of x.deltas)must(Number.isFinite(d)&&Math.abs(d)<=limit,'nonfinite/unbounded sparse delta');
  return {indices:x.indices.slice(),deltas:x.deltas.slice()};
}
export function compileDiagnosticMorphs(mesh,sourceNormals,morphs,{reviewOnly=false}={}){
  must(reviewOnly===true,'explicit review-only opt-in required');
  const {vertices}=validateNativeSkinnedMesh(mesh);
  must(sourceNormals instanceof Float32Array&&sourceNormals.length===vertices*3,'source normal count mismatch');
  for(let i=0;i<sourceNormals.length;i+=3){
    const len=Math.hypot(...sourceNormals.subarray(i,i+3));
    must(Number.isFinite(len)&&len>=.998&&len<=1.002,'unit source normal required');
  }
  must(Array.isArray(morphs)&&morphs.length>=1&&morphs.length<=16,'1..16 corrective targets required');
  const names=new Set(),targets=[];
  let entries=0;
  for(const m of morphs){
    exact(m,['name','position','normal']);
    must(label(m.name)&&!names.has(m.name),'unique safe morph name required');names.add(m.name);
    // Check lengths before copies to preserve an aggregate 1M sparse-entry budget.
    must(m.position?.indices instanceof Uint32Array&&m.normal?.indices instanceof Uint32Array,
      'typed sparse indices required');
    entries+=m.position.indices.length+m.normal.indices.length;
    must(entries<=1000000,'aggregate sparse entry budget exceeded');
    targets.push({name:m.name,position:sparse(m.position,vertices,.25),normal:sparse(m.normal,vertices,2)});
  }
  const h=Object.freeze({kind:'hgpt-diagnostic-sparse-correctives-v1',
    morphNames:Object.freeze([...names]),vertices,productionApproved:false,sourceBytesVerified:false});
  handles.set(h,{mesh:copyMesh(mesh),normals:sourceNormals.slice(),targets});return h;
}
export function prepareDiagnosticMorphFrame(handle,weights){
  must(handles.has(handle),'compiled diagnostic morph handle required');
  exact(weights,handle.morphNames);
  for(const n of handle.morphNames)must(Number.isFinite(weights[n])&&weights[n]>=0&&weights[n]<=1,
    'explicit finite 0..1 corrective weights required');
  const original=handles.get(handle),mesh=copyMesh(original.mesh),normals=original.normals.slice();
  for(const t of original.targets){
    const weight=weights[t.name];
    if(weight===0)continue;
    for(const [dst,s] of [[mesh.positions,t.position],[normals,t.normal]]){
      for(let i=0;i<s.indices.length;i++)for(let k=0;k<3;k++)
        dst[s.indices[i]*3+k]+=weight*s.deltas[i*3+k];
    }
  }
  for(let i=0;i<normals.length;i+=3){
    const len=Math.hypot(...normals.subarray(i,i+3));
    must(Number.isFinite(len)&&len>1e-6,'active corrective produces invalid normal');
    for(let k=0;k<3;k++)normals[i+k]/=len;
  }
  validateNativeSkinnedMesh(mesh);
  return {mesh,sourceNormals:normals,productionApproved:false};
}
