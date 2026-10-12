import test from 'node:test';
import assert from 'node:assert/strict';
import {
  snapshotDecodedOriginalReview,
  assertDecodedOriginalReviewUnmodified as unchanged,
} from '../src/viewer/firstPartyOriginalFullBodyImmutableSource.mjs';
import {
  isAuthenticatedOriginalFullBodyReview,
  assertAuthenticatedOriginalFullBodyReviewUnmodified,
} from '../src/viewer/firstPartyOriginalFullBodyReview.mjs';
import {
  HGPT_FULLBODY_GPU_REST_KIND,
  renderVerifiedOriginalFullBodyRestGpu,
} from '../src/viewer/firstPartyOriginalFullBodyGpuRest.mjs';

function source(){
  const arr=(n,v=.25)=>new Float32Array(n).fill(v);
  const morph=(name)=>({
    name,restWeight:0,positionChangedVertices:2,normalChangedVertices:2,
    sourcePositionDelta:{
      indices:new Uint32Array([1,3]),delta:arr(6,.01),
      changedVertices:2,maxAbsDelta:.01
    },
    sourceNormalDelta:{
      indices:new Uint32Array([1,3]),delta:arr(6,.02),
      changedVertices:2,maxAbsDelta:.02
    },
    actualCorrectiveSynthesisValidated:false,
  });
  return {
    sourceSha256:'b'.repeat(64),vertices:4,triangles:2,bones:2,
    mesh:{
      positions:arr(12),indices:new Uint16Array([0,1,2,1,3,2]),
      jointIndices:new Uint16Array(16),weights:arr(16),
      inverseBindMatrices:arr(32),
    },
    sourceNormals:arr(12),
    jointNames:Object.freeze(['source_bone_a','source_bone_b']),
    restWorldByJointName:{
      source_bone_a:Array.from(arr(16)),source_bone_b:Array.from(arr(16)),
    },
    sourceMaterial:{sourceBaseColor:[.4,.6,.9],
      sourceDoubleSided:true,sourceRoughness:.48},
    sparseCorrectives:[morph('CORR_L'),morph('CORR_R')],
  };
}
test('exact-byte snapshot accepts untouched original-style source arrays and numeric metadata',()=>{
  const review=source(),snapshot=snapshotDecodedOriginalReview(review);
  assert.equal(unchanged(review,snapshot),true);
  assert.equal(isAuthenticatedOriginalFullBodyReview(review),false,
    'an independently made snapshot MUST NOT mint SHA/source provenance');
  assert.throws(()=>assertAuthenticatedOriginalFullBodyReviewUnmodified(review),
    /no verified private provenance/);
});
const cases=[
  ['source body POSITION',r=>r.mesh.positions[3]+=.01],
  ['source WEIGHTS_0',r=>r.mesh.weights[8]+=.5],
  ['original inverse bind',r=>r.mesh.inverseBindMatrices[17]+=.01],
  ['original indexed triangle',r=>r.mesh.indices[4]=2],
  ['original JOINTS_0',r=>r.mesh.jointIndices[3]=1],
  ['original source normal',r=>r.sourceNormals[5]=.01],
  ['original world bind-rest joint',r=>r.restWorldByJointName.source_bone_b[12]+=.3],
  ['morph source sparse vertex index',r=>r.sparseCorrectives[0].sourcePositionDelta.indices[1]=2],
  ['morph original sparse positional delta',r=>r.sparseCorrectives[1].sourcePositionDelta.delta[3]+=.01],
  ['morph original sparse normal delta',r=>r.sparseCorrectives[1].sourceNormalDelta.delta[1]=.2],
  ['morph source rest weight',r=>r.sparseCorrectives[1].restWeight=.4],
  ['material source roughness',r=>r.sourceMaterial.sourceRoughness=.8],
  ['source SHA reference',r=>r.sourceSha256='f'.repeat(64)],
  ['typed buffer substitution',r=>r.mesh.positions=r.mesh.positions.slice()],
  ['original mesh object substitution',r=>r.mesh={...r.mesh}],
  ['original morph source reference',r=>r.sparseCorrectives=r.sparseCorrectives.slice()],
  ['original source rest object',r=>r.restWorldByJointName={...r.restWorldByJointName}],
];
for(const [description,mutate]of cases){
  test('original authenticated source must reject post-validation mutation: '+description,()=>{
    const review=source(),snapshot=snapshotDecodedOriginalReview(review);
    mutate(review);
    assert.throws(()=>unchanged(review,snapshot),
      /Original source post-validation mutation:/);
  });
}
test('a fake GPU-only review object cannot reach actual drawElements',()=>{
  let rendered=0;
  const fake={kind:HGPT_FULLBODY_GPU_REST_KIND,
    gpuParts:[{mesh:{}}],originalMorphWeightsAllZero:true,
    diagnosticShaderAttributePaddingOnly:true};
  const renderer={kind:'hgpt-native-webgl2-rgba32f-4weight-gpu-lbs-v1',
    renderBatches(){rendered++;return true;}};
  assert.throws(()=>renderVerifiedOriginalFullBodyRestGpu(renderer,fake),
    /verified first-party GPU renderer and rest-only preview required/);
  assert.equal(rendered,0);
});
