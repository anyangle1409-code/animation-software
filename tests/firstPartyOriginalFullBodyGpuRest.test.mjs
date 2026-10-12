import test from 'node:test';
import assert from 'node:assert/strict';
import {
  HGPT_FULLBODY_GPU_REST_KIND,
  prepareVerifiedOriginalFullBodyRestGpu,
  renderVerifiedOriginalFullBodyRestGpu,
} from '../src/viewer/firstPartyOriginalFullBodyGpuRest.mjs';
import {HGPT_ORIGINAL_FULLBODY_REVIEW_KIND,
  isAuthenticatedOriginalFullBodyReview}
  from '../src/viewer/firstPartyOriginalFullBodyReview.mjs';

const faked=()=>({
  kind:HGPT_ORIGINAL_FULLBODY_REVIEW_KIND,vertices:17946,bones:67,
  triangles:35888,sourceSha256:'a'.repeat(64),
  jointNames:Array.from({length:67},(_,i)=>'joint_'+i),
  sparseCorrectives:Array.from({length:6},()=>({
    restWeight:0,actualCorrectiveSynthesisValidated:false
  })),
  audit:{
    originalSourceSHA256Verified:true,
    actualSourceJointRestAndInverseBindMatched:true,
    maximumRestInverseBindResidual:0,
    independentAnatomicalAcceptance:false,productionReady:false,
  },
});
test('the exact target is 67 bones, 17,946 source vertices and six NO-movement correctives',()=>{
  assert.equal(HGPT_FULLBODY_GPU_REST_KIND,
    'hgpt-original-fullbody-native-gpu-rest-only-v1');
  assert.equal(isAuthenticatedOriginalFullBodyReview(faked()),false);
});
test('forged metadata cannot replace a genuine source SHA/rig review handle',()=>{
  const x=faked();
  assert.throws(()=>prepareVerifiedOriginalFullBodyRestGpu(x),
    /source-authenticated review-only SHA\/bind handle required/);
  assert.throws(()=>prepareVerifiedOriginalFullBodyRestGpu(
    {...x,mesh:{},audit:{...x.audit}}),
    /source-authenticated review-only SHA\/bind handle required/);
});
test('forged 67-bone GPU plan may not invoke any third-party or first-party draws',()=>{
  let draws=0;
  const fakeRenderer={kind:'hgpt-native-webgl2-rgba32f-4weight-gpu-lbs-v1',
    renderBatches(){draws++;return true;}};
  assert.throws(()=>renderVerifiedOriginalFullBodyRestGpu(fakeRenderer,{
    kind:HGPT_FULLBODY_GPU_REST_KIND,gpuParts:[{}],
    originalMorphWeightsAllZero:true,diagnosticShaderAttributePaddingOnly:true,
  }),/verified first-party GPU renderer and rest-only preview required/);
  assert.equal(draws,0);
});
test('source normal/texture/morph render options never enable unverified exercise movement',()=>{
  let draws=0;
  const fakeRenderer={kind:'hgpt-native-webgl2-rgba32f-4weight-gpu-lbs-v1',
    renderBatches(){draws++;return true;}};
  for(const mode of ['normalPreview','texturePreview','colorManagedTexturePreview',
    'pilotFlatColorPreview']){
    assert.throws(()=>renderVerifiedOriginalFullBodyRestGpu(fakeRenderer,{
      kind:HGPT_FULLBODY_GPU_REST_KIND,gpuParts:[{}],
      originalMorphWeightsAllZero:true,diagnosticShaderAttributePaddingOnly:true
    },{[mode]:true}),/verified first-party GPU renderer and rest-only preview required/);
  }
  assert.equal(draws,0);
});
