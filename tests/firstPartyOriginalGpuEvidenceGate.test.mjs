import test from 'node:test';
import assert from 'node:assert/strict';
import {assessOriginalGpuReviewEvidence} from '../src/viewer/firstPartyOriginalGpuEvidenceGate.mjs';
const good=()=>({source:'private-original-v1',
sha256:'d267dac344affb5d52c7155f8d0254794e818a8eab3ad54f7f263694f36c390d',
skinJoints:67,vertices:17946,gpuCapture:{type:'original-fullbody-webgl2',
captureVerified:true,artifactSha256:'a'.repeat(64)},
renderReview:{ownerAccepted:true}});
test('no evidence never becomes accepted',()=>assert.equal(
 assessOriginalGpuReviewEvidence(null).reason,'MISSING_EVIDENCE'));
test('rejects diagnostic-only evidence despite GPU capability success',()=>{
 const e=good();delete e.gpuCapture;e.capabilityProbe={supported:true};
 assert.equal(assessOriginalGpuReviewEvidence(e).reason,'ACTUAL_ORIGINAL_GPU_CAPTURE_MISSING');
});
test('rejects substituted original model and geometry',()=>{
 for(const [change,reason] of [
 [e=>e.sha256='b'.repeat(64),'ORIGINAL_SOURCE_MISMATCH'],
 [e=>e.vertices=17945,'ORIGINAL_CHARACTER_GEOMETRY_MISMATCH'],
 [e=>e.skinJoints=66,'ORIGINAL_CHARACTER_GEOMETRY_MISMATCH']]){
 const e=good();change(e);assert.equal(assessOriginalGpuReviewEvidence(e).reason,reason);
 }
});
test('requires human review even with claimed capture',()=>{
 const e=good();delete e.renderReview;
 assert.equal(assessOriginalGpuReviewEvidence(e).reason,'OWNER_RENDER_REVIEW_PENDING');
});
test('approval flag is not a production release or proof authenticity',()=>{
 const r=assessOriginalGpuReviewEvidence(good());
 assert.equal(r.approved,false);assert.equal(r.evidenceFieldsComplete,true);assert.equal(r.productionReady,false);
 assert.match(r.reason,/INDEPENDENT_VERIFICATION/);
 assert.ok(Object.isFrozen(r));
});
