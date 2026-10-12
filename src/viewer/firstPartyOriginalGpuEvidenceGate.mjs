/**
 * G5b: explicit evidence boundary between browser compatibility diagnostics
 * and a source-authenticated, actual original full-body GPU render.
 * Never accepts self-reported booleans as GPU capture evidence.
 */
export const ORIGINAL_GPU_EVIDENCE_KIND='hgpt-original-full-body-gpu-proof-gate-v1';
export function assessOriginalGpuReviewEvidence(evidence){
  const fail=reason=>Object.freeze({kind:ORIGINAL_GPU_EVIDENCE_KIND,
    approved:false,reason,productionReady:false});
  if(!evidence||typeof evidence!=='object')return fail('MISSING_EVIDENCE');
  if(evidence.source!== 'private-original-v1')return fail('WRONG_MODEL_SOURCE');
  if(typeof evidence.sha256!=='string'||!/^[0-9a-f]{64}$/.test(evidence.sha256))
    return fail('SOURCE_SHA256_UNVERIFIED');
  if(evidence.sha256!=='d267dac344affb5d52c7155f8d0254794e818a8eab3ad54f7f263694f36c390d')
    return fail('ORIGINAL_SOURCE_MISMATCH');
  if(evidence.skinJoints!==67||evidence.vertices!==17946)
    return fail('ORIGINAL_CHARACTER_GEOMETRY_MISMATCH');
  // Device capability, palette upload and shader-link preflight are useful
  // but never substitute for genuine traceable GPU execution/capture.
  if(evidence.gpuCapture?.type!=='original-fullbody-webgl2'||
     evidence.gpuCapture?.captureVerified!==true||
     typeof evidence.gpuCapture?.artifactSha256!=='string'||
     !/^[0-9a-f]{64}$/.test(evidence.gpuCapture.artifactSha256))
    return fail('ACTUAL_ORIGINAL_GPU_CAPTURE_MISSING');
  if(evidence.renderReview?.ownerAccepted!==true)
    return fail('OWNER_RENDER_REVIEW_PENDING');
  // Prevent this diagnostic from granting production release: anatomical
  // skeleton, foot correction and natural motion are separate gates.
  return Object.freeze({kind:ORIGINAL_GPU_EVIDENCE_KIND,approved:true,
    reason:'GPU_REVIEW_EVIDENCE_PRESENT_NOT_INDEPENDENTLY_AUTHENTICATED',
    productionReady:false});
}
