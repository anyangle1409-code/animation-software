import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {buildSyntheticFirstPartyGlb}
  from './support/buildSyntheticFirstPartyGlb.mjs';
import {HGPT_ORIGINAL_FULLBODY_REVIEW_KIND,
  parseOriginalFullBodyReviewGLB}
  from '../src/viewer/firstPartyOriginalFullBodyReview.mjs';

const digest=b=>createHash('sha256').update(new Uint8Array(b)).digest('hex');
test('original-source parser loads as first-party ES module',()=>{
  assert.equal(HGPT_ORIGINAL_FULLBODY_REVIEW_KIND,
    'hgpt-original-fullbody-review-only-source-v1');
});
test('source SHA is mandatory and checked before decoding any untrusted model',async()=>{
  const f=buildSyntheticFirstPartyGlb(),sha=digest(f);
  await assert.rejects(
    ()=>parseOriginalFullBodyReviewGLB(f),
    /caller must supply previously recorded exact source SHA-256/);
  await assert.rejects(
    ()=>parseOriginalFullBodyReviewGLB(f,{expectedSha256:'f'.repeat(64)}),
    /original Work full-body GLB source SHA mismatch/);
  // Hash equality does not promote a small synthetic/foreign model:
  await assert.rejects(
    ()=>parseOriginalFullBodyReviewGLB(f,{expectedSha256:sha}),
    /original full body needs only first four joint influences|one original body mesh, one complete runtime skin|one explicit original scene root|one original skinned mesh node|required/);
});
test('mutating one source byte always refuses a previously accepted digest',async()=>{
  const f=buildSyntheticFirstPartyGlb(),sha=digest(f);
  const copy=f.slice(0);new Uint8Array(copy)[65]^=1;
  await assert.rejects(
    ()=>parseOriginalFullBodyReviewGLB(copy,{expectedSha256:sha}),
    /original Work full-body GLB source SHA mismatch/);
});
test('bogus raw buffer and nonlowercase SHA cannot bypass the strict boundary',async()=>{
  await assert.rejects(()=>parseOriginalFullBodyReviewGLB('not a GLB',
    {expectedSha256:'a'.repeat(64)}),/raw original ArrayBuffer required/);
  await assert.rejects(()=>parseOriginalFullBodyReviewGLB(
    buildSyntheticFirstPartyGlb(),{expectedSha256:'A'.repeat(64)}),
  /caller must supply previously recorded exact source SHA-256/);
});
