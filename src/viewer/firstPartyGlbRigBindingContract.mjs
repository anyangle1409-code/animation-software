/**
 * HGPT first-party GLB skin-to-rig BINDING CONTRACT (numerical screening).
 *
 * Strictly requires an EXPLICIT per-source-joint canonical identity mapping
 * and rig rest-world matrices, then verifies worldRest * inverseBind == I.
 * Never uses suffix _l/_r to infer clinical laterality, fabricates a pose,
 * rescales patient anatomy, or declares production asset provenance approved.
 *
 * Assumes GLB mesh node identity and compatible coordinate frames established
 * by the upstream restricted GLB importer. No CT/RAS/LPS/Blender conversion.
 * Explicit matrix compatibility only is NOT clinical anatomical correctness.
 */
import { FIRST_PARTY_GLB_GATE } from './firstPartyGlbSkinnedGeometry.mjs';
import { multiplyNativeMat4 } from './firstPartyWebGL2SkeletonPreview.mjs';

export const NATIVE_RIG_BIND_CONTRACT = 'hgpt-strict-glb-native-rig-joint-bind-v1';

const IDENTITY=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const verifiedPlans=new WeakSet(); // only products of full source/bind compatibility checks
const isRecord=(v)=>v!==null && typeof v==='object' && !Array.isArray(v);
function checkedMatrix(value, label) {
  if(!value || value.length!==16 ||
      (!Array.isArray(value) && !(value instanceof Float32Array) &&
       !(value instanceof Float64Array)))throw new TypeError(label+' requires 16 numeric column-major elements');
  const m=Array.from(value);
  if(!m.every(Number.isFinite))throw new RangeError(label+' has nonfinite numbers');
  if(Math.abs(m[3])+Math.abs(m[7])+Math.abs(m[11])+Math.abs(m[15]-1)>1e-4)
    throw new RangeError(label+' is not an affine 4x4 matrix');
  // This bounded first-party stage accepts only proper, orthonormal rigid
  // transforms. No mirrored coordinate frame or scale/shear compensation.
  const axes=[[m[0],m[1],m[2]],[m[4],m[5],m[6]],[m[8],m[9],m[10]]];
  for(let i=0;i<3;i++){
    if(Math.abs(Math.hypot(...axes[i])-1)>1e-3)
      throw new RangeError(label+' has unapproved scale/stretch');
    for(let j=0;j<i;j++){
      let dot=0;for(let k=0;k<3;k++)dot+=axes[i][k]*axes[j][k];
      if(Math.abs(dot)>1e-3)throw new RangeError(label+' has unapproved shear');
    }
  }
  const [x,y,z]=axes;
  const determinant =
    x[0]*(y[1]*z[2]-y[2]*z[1])-
    x[1]*(y[0]*z[2]-y[2]*z[0])+
    x[2]*(y[0]*z[1]-y[1]*z[0]);
  if(Math.abs(determinant-1)>2e-3)
    throw new RangeError(label+' has unapproved reflected/left-handed basis');
  return new Float32Array(m);
}
function safeName(value) {
  return typeof value==='string' && value.length>0 && value.length<=80 &&
    value!=='__proto__' && value!=='constructor' && value!=='prototype' &&
    !value.includes('\0');
}
function getOwn(data,key,label) {
  if(!Object.hasOwn(data,key))throw new RangeError(label+' missing '+key);
  return data[key];
}
function checkBoneOrder(parsed,options) {
  if(!parsed || parsed.kind!==FIRST_PARTY_GLB_GATE ||
     !parsed.mesh || !(parsed.mesh.inverseBindMatrices instanceof Float32Array) ||
     !Array.isArray(parsed.jointNodeNames))
    throw new TypeError('Must supply the actual restricted GLB parser output');
  const names=parsed.jointNodeNames;
  if(!names.length || names.length>128 || !names.every(safeName) ||
     new Set(names).size!==names.length ||
     parsed.mesh.inverseBindMatrices.length!==names.length*16)
    throw new RangeError('Source GLB joint identity/palette invalid');
  const {sourceToCanonical,allowedCanonicalNames,canonicalRestWorldByBone}=options||{};
  if(!isRecord(sourceToCanonical)||!isRecord(canonicalRestWorldByBone)||
     !Array.isArray(allowedCanonicalNames) || !allowedCanonicalNames.length ||
     !allowedCanonicalNames.every(safeName) ||
     new Set(allowedCanonicalNames).size!==allowedCanonicalNames.length)
    throw new TypeError('Explicit unique trusted rig names, mapping and rest-world matrices required');
  if(Object.keys(sourceToCanonical).length!==names.length)
    throw new RangeError('Source mapping must cover EXACTLY every GLB skin joint');
  const allowed=new Set(allowedCanonicalNames);
  const canonicalNames=[],seen=new Set();
  for(const source of names){
    const target=getOwn(sourceToCanonical,source,'Source mapping');
    if(!safeName(target)||!allowed.has(target))
      throw new RangeError('Unmapped/unknown canonical bone for source joint '+source);
    if(seen.has(target))throw new RangeError('Duplicate canonical bone mapping');
    seen.add(target);
    canonicalNames.push(target);
  }
  return {names,canonicalNames,canonicalRestWorldByBone};
}
/**
 * Verifies numerical binding in identical **claimed** frames.
 *
 * The 1e-4 tolerance is an implementation screening threshold, NOT an accepted
 * anatomical tolerance. No coercion, rescale, handedness flip, mesh rewriting
 * or inferred side correction is ever performed.
 */
export function validateNativeGLBToRigBinding(parsed,options){
  const {names,canonicalNames,canonicalRestWorldByBone}=
    checkBoneOrder(parsed,options);
  const errors=[];
  const rigRestPalette=new Float32Array(names.length*16);
  for(let i=0;i<names.length;i++){
    const target=canonicalNames[i];
    const world=checkedMatrix(getOwn(canonicalRestWorldByBone,target,'Rig rest world'),target);
    const inverseBind=checkedMatrix(
      parsed.mesh.inverseBindMatrices.subarray(i*16,i*16+16),names[i]+' inverse bind');
    const product=multiplyNativeMat4(world,inverseBind);
    let error=0;
    for(let j=0;j<16;j++)error=Math.max(error,Math.abs(product[j]-IDENTITY[j]));
    if(error>1e-4)throw new RangeError(
      'Rig bind mismatch source '+names[i]+' -> '+target+
      ': restWorld * inverseBind != identity; do not transform bones to force fit');
    errors.push(error);
    rigRestPalette.set(world,i*16);
  }
  const plan={
    kind:NATIVE_RIG_BIND_CONTRACT,
    orderedSourceJointNames:[...names],
    orderedCanonicalBoneNames:canonicalNames,
    numericallyCompatibleSameFrameRestBinds:true,
    maximumMatrixResidual:Math.max(...errors),
    verifiedJointCount:names.length,
    checkedRestPoseWorldMatrices:rigRestPalette,
    audit:{
      sourceBoneNameMappingExplicit:true,
      sourceLateralityInferredFromSuffix:false,
      autoScaleOrHandednessConversion:false,
      restWorldInverseBindIdentityOnly:true,
      originalGltfSourceJointHierarchyPhysicallyVerified:false,
      independentAnatomicalJointCentresAccepted:false,
      sourceFramePhysicallyRegistered:false,
      originalCharacterAssetProvenanceApproved:false,
      fullBodyDeformationAccepted:false,
      finalRuntimeApproval:false,
    }
  };
  verifiedPlans.add(plan);
  return plan;
}
export function packMappedWorldPalette(plan,posedWorldByBone){
  if(!plan || !verifiedPlans.has(plan) || plan.kind!==NATIVE_RIG_BIND_CONTRACT ||
     !plan.numericallyCompatibleSameFrameRestBinds ||
     !Array.isArray(plan.orderedCanonicalBoneNames) ||
     !isRecord(posedWorldByBone))
    throw new TypeError('Validated native GLB-to-rig binding plan and explicit posed matrices required');
  const result=new Float32Array(plan.orderedCanonicalBoneNames.length*16);
  for(let i=0;i<plan.orderedCanonicalBoneNames.length;i++){
    const name=plan.orderedCanonicalBoneNames[i];
    result.set(checkedMatrix(getOwn(posedWorldByBone,name,'Rig animated world'),name),16*i);
  }
  return result;
}
