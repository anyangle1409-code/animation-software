/**
 * G4s: source-verified, ORIGINAL-v1 full-body GPU REST preview input.
 * No access to Work source bytes after the original G4r parser, no vendor,
 * no inferred 206->67 mapping, no morph activation, no unapproved animation.
 */
import {isAuthenticatedOriginalFullBodyReview,
  assertAuthenticatedOriginalFullBodyReviewUnmodified}
  from './firstPartyOriginalFullBodyReview.mjs';
import {validateNativeSkinnedMesh}
  from './firstPartyIndexedSkinnedMesh.mjs';
export const HGPT_FULLBODY_GPU_REST_KIND=
  'hgpt-original-fullbody-native-gpu-rest-only-v1';
const fail=s=>{throw new RangeError('Original full-body GPU rest rejected: '+s)};
const authenticatedGpuRestPreviews=new WeakSet();
const originalGpuRestSnapshots=new WeakMap();
export function prepareVerifiedOriginalFullBodyRestGpu(review){
  if(!isAuthenticatedOriginalFullBodyReview(review)||
    review.audit?.originalSourceSHA256Verified!==true||
    review.audit?.actualSourceJointRestAndInverseBindMatched!==true||
    review.audit?.maximumRestInverseBindResidual>1e-4||
    review.audit?.independentAnatomicalAcceptance!==false||
    review.audit?.productionReady!==false)
    fail('source-authenticated review-only SHA/bind handle required');
  if(review.vertices!==17946||review.bones!==67||
    review.triangles!==35888||
    !Array.isArray(review.jointNames)||review.jointNames.length!==67)
    fail('original 17,946-vertex 67-joint 35,888-triangle model required');
  if(!Array.isArray(review.sparseCorrectives)||
    review.sparseCorrectives.length!==6||
    review.sparseCorrectives.some(s=>s.restWeight!==0||
      s.actualCorrectiveSynthesisValidated!==false))
    fail('original six sparse correctives must remain unanimated at zero rest');
  const shape=validateNativeSkinnedMesh(review.mesh);
  if(shape.bones!==67||shape.vertices!==17946||
    shape.triangles!==35888)
    fail('original source mesh skin topology mismatch');
  if(!(review.sourceNormals instanceof Float32Array)||
    review.sourceNormals.length!==shape.vertices*3||
    !Array.from(review.sourceNormals).every(Number.isFinite))
    fail('actual source normal vectors must be preserved');
  const palette=new Float32Array(shape.bones*16);
  for(let i=0;i<review.jointNames.length;i++){
    const name=review.jointNames[i],m=review.restWorldByJointName[name];
    if(!Array.isArray(m)||m.length!==16||!m.every(Number.isFinite))
      fail('missing exact source rest-world matrix '+name);
    palette.set(m,16*i);
  }
  const color=review.sourceMaterial?.sourceBaseColor;
  if(!Array.isArray(color)||color.length!==3||
    color.some(v=>!Number.isFinite(v)||v<0||v>1)||
    typeof review.sourceMaterial.sourceDoubleSided!=='boolean')
    fail('actual source material not preserved');
  // Existing original pilot shader declares uv0 attribute, but the genuine
  // full-body material has no source texture/UV. Neutral GPU attribute padding
  // is strictly non-source, never authoring/provenance output.
  const part=Object.freeze({
    mesh:review.mesh,
    posedWorld:palette,
    sourceNormals:review.sourceNormals,
    uv0:new Float32Array(shape.vertices*2),
    materialColor:Object.freeze([...color]),
    sourceDoubleSided:review.sourceMaterial.sourceDoubleSided,
  });
  const preview=Object.freeze({
    kind:HGPT_FULLBODY_GPU_REST_KIND,
    originalSourceSha256:review.sourceSha256,
    sourceJointCount:67,
    originalTriangleCount:35888,
    sourceMorphCount:6,
    originalMorphWeightsAllZero:true,
    gpuParts:Object.freeze([part]),
    renderOptions:Object.freeze({pilotLambertPreview:true}),
    sourceUVsInvented:false,
    diagnosticShaderAttributePaddingOnly:true,
    fullBodyNaturalMovementApproved:false,
    morphDeformationApproved:false,
    productionReady:false,
  });
  // This private reference and matrix snapshot closes the gap between the
  // AUTHENTICATED source-preparation event and the later browser render call.
  // Freezing a part object does not freeze its Uint16/Float32Array bytes.
  originalGpuRestSnapshots.set(preview,{
    review,part,mesh:part.mesh,normals:part.sourceNormals,
    posedWorld:part.posedWorld,
    posedWorldBytes:new Uint8Array(part.posedWorld.buffer,
      part.posedWorld.byteOffset,part.posedWorld.byteLength).slice(),
    uv0:part.uv0,
  });
  authenticatedGpuRestPreviews.add(preview);
  return preview;
}
export function renderVerifiedOriginalFullBodyRestGpu(renderer,preview,options={}){
  if(!authenticatedGpuRestPreviews.has(preview) ||
    preview?.kind!==HGPT_FULLBODY_GPU_REST_KIND ||
    preview.gpuParts?.length!==1 ||
    !preview.originalMorphWeightsAllZero ||
    !preview.diagnosticShaderAttributePaddingOnly ||
    renderer?.kind!=='hgpt-native-webgl2-rgba32f-4weight-gpu-lbs-v1' ||
    typeof renderer.renderBatches!=='function')
    fail('verified first-party GPU renderer and rest-only preview required');
  const snapshot=originalGpuRestSnapshots.get(preview);
  if(!snapshot||preview.gpuParts[0]!==snapshot.part ||
    snapshot.part.mesh!==snapshot.mesh ||
    snapshot.part.sourceNormals!==snapshot.normals ||
    snapshot.part.posedWorld!==snapshot.posedWorld ||
    snapshot.part.uv0!==snapshot.uv0)
    fail('verified full-body source/GPU part reference changed after preparation');
  try{
    assertAuthenticatedOriginalFullBodyReviewUnmodified(snapshot.review);
  }catch{
    fail('authenticated full-body source changed since GLB SHA verification');
  }
  const current=new Uint8Array(snapshot.posedWorld.buffer,
    snapshot.posedWorld.byteOffset,snapshot.posedWorld.byteLength);
  if(current.length!==snapshot.posedWorldBytes.length||
    current.some((b,i)=>b!==snapshot.posedWorldBytes[i])||
    !(snapshot.uv0 instanceof Float32Array) ||
    snapshot.uv0.some(x=>x!==0))
    fail('original joint rest palette or untextured GPU attribute padding changed');
  if(options.normalPreview===true||options.texturePreview===true||
    options.colorManagedTexturePreview===true ||
    options.pilotFlatColorPreview===true ||
    options.pilotLambertPreview===false)
    fail('rest view cannot enable a different material or unverified morph');
  const drawn=renderer.renderBatches(preview.gpuParts,{
    ...options,
    pilotLambertPreview:true,
    normalPreview:false,texturePreview:false,
    colorManagedTexturePreview:false,pilotFlatColorPreview:false
  });
  return Object.freeze({drawn:drawn===true,
    originalSourceSha256:preview.originalSourceSha256,
    drawCallsIfSuccessful:drawn===true?1:0,
    sourceRestOnly:true,
    sourceHumanDeformationVerified:false,
    clinicalApproved:false,productionReady:false});
}
