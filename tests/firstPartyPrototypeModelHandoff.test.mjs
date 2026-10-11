import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSyntheticFirstPartyGlb} from './support/buildSyntheticFirstPartyGlb.mjs';
import {buildSyntheticBatchedGlb} from './support/buildSyntheticBatchedGlb.mjs';
import {deformIndexedSkin} from '../src/viewer/firstPartyIndexedSkinnedMesh.mjs';
import {
  HGPT_PROTOTYPE_HANDOFF_KIND as KIND,
  digestOriginalGlbSha256 as hash,
  validateProvisionalModelHandoff as validate,
  packProvisionalModelPose as pose,
} from '../src/viewer/firstPartyPrototypeModelHandoff.mjs';

const id=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const t=(x,y,z)=>[1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1];
const glb=(layout='single')=>layout==='single'?
  buildSyntheticFirstPartyGlb():buildSyntheticBatchedGlb();
async function fixture(layout='single'){
  const asset=glb(layout);
  const m={
    kind:KIND,candidateId:'HGPT_Male_FUNCTIONAL_PROTOTYPE_001',
    status:'PROTOTYPE_ONLY',
    glb:{sha256:await hash(asset),layout,
      sourceFeatures:{flatColors:false,uv0:false,normals:false}},
    frame:{unit:'metre',up:'Y',handedness:'right',
      basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
    rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
      thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
    rig:{
      sourceToRuntimeBone:{
        test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'
      },
      runtimeBoneNames:['upperarm_l','forearm_l'],
      restWorldByRuntimeBone:{upperarm_l:id(),forearm_l:id()},
      lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED',
    },
    releaseApproved:false,
  };
  return {asset,manifest:m};
}
const verifyFail=async (change,pattern,layout='single')=>{
  const {asset,manifest}=await fixture(layout);
  change(manifest,asset);
  await assert.rejects(()=>validate(asset,manifest),pattern);
};
test('SHA-256 digest checks exact original ArrayBuffer deterministically',async()=>{
  const asset=glb();
  const digest=await hash(asset);
  assert.match(digest,/^[a-f0-9]{64}$/);
  assert.equal(digest,await hash(asset));
  await assert.rejects(()=>hash(new Uint8Array(asset)),/ArrayBuffer/);
  await assert.rejects(()=>hash(new ArrayBuffer(0)),/bounded/);
});
test('fully validates original synthetic single-primitive Work prototype',async()=>{
  const {asset,manifest}=await fixture();
  const r=await validate(asset,manifest);
  assert.equal(r.kind,KIND);
  assert.equal(r.numberOfPrimitives,1);
  assert.equal(r.sourceSha256,manifest.glb.sha256);
  assert.deepEqual(r.sourceJointNames,['test_upperarm_l','test_forearm_l']);
  assert.deepEqual(r.runtimeJointNames,['upperarm_l','forearm_l']);
  assert.equal(r.audit.maximumRestMatrixResidual,0);
  assert.equal(r.audit.allGLBPrimitivesDecodedAndBound,true);
  assert.equal(r.audit.verifiedAnatomicalLaterality,false);
  assert.equal(r.audit.medicallyApprovedHumanSkeleton,false);
  assert.equal(r.audit.realisticWholeBodyDeformationVerified,false);
  assert.equal(r.audit.modelProductionReady,false);
});
test('two mesh parts are checked, not silently dropped',async()=>{
  const {asset,manifest}=await fixture('batched');
  const r=await validate(asset,manifest);
  assert.equal(r.numberOfPrimitives,2);
  assert.equal(r.scene.audit.numberOfMeshes,2);
  const posed=pose(r,{upperarm_l:t(1,0,0),forearm_l:t(0,2,0)});
  assert.equal(posed.length,32);
  for(const part of r.scene.batches){
    const mesh=part.parsed.mesh;
    const d=deformIndexedSkin(mesh,posed);
    assert.equal(d.triangleCount,1);
    assert.ok(Math.abs(d.positions[0]-mesh.positions[0]-.75)<1e-6);
    assert.ok(Math.abs(d.positions[1]-mesh.positions[1]-.5)<1e-6);
  }
});
test('full source SHA verification refuses changed bytes or stale model metadata',async()=>{
  await verifyFail((m,b)=>{new Uint8Array(b)[24]^=1},/SHA-256 mismatch/);
  await verifyFail(m=>{m.glb.sha256='0'.repeat(64)},/SHA-256 mismatch/);
});
test('caller mutation after async validation start does not alter snapshotted GLB',async()=>{
  const {asset,manifest}=await fixture();
  const pending=validate(asset,manifest);
  new Uint8Array(asset)[24]^=1;
  const r=await pending;
  assert.equal(r.sourceSha256,manifest.glb.sha256);
  assert.equal(r.numberOfPrimitives,1);
});
test('explicit GLB layout cannot mask incompatible source geometry',async()=>{
  await verifyFail(m=>{m.glb.layout='batched'},/2..8/);
  await verifyFail(m=>{m.glb.layout='unrestricted'},/single or batched/);
  await verifyFail(m=>{m.glb.sourceFeatures.normals=true},
    /single primitive has no opt-in/);
  await verifyFail(m=>{m.glb.sourceFeatures.uv0=true},
    /single primitive has no opt-in/);
});
test('bad or invented early model release/rights/source frame claims fail closed',async()=>{
  await verifyFail(m=>{m.status='APPROVED'},/PROTOTYPE_ONLY|production/);
  await verifyFail(m=>{m.releaseApproved=true},/production|clinical/);
  await verifyFail(m=>{m.frame.unit='centimetre'},/metre/);
  await verifyFail(m=>{m.frame.up='Z'},/metre\/Y\/right-handed/);
  await verifyFail(m=>{m.frame.handedness='left'},/metre\/Y\/right-handed/);
  await verifyFail(m=>{m.frame.basisStatus='CLINICALLY_APPROVED'},/unverified/);
  await verifyFail(m=>{m.rights.independentRightsReview=true},/rights claims/);
  await verifyFail(m=>{m.rights.projectAuthoredClaim=false},/rights claims/);
  await verifyFail(m=>{m.rights.medicalSourceGeometryEmbedded=true},/rights claims/);
  await verifyFail(m=>{m.rights.thirdPartyCharacterGeometryEmbedded=true},/rights claims/);
  await verifyFail(m=>{m.rig.lateralityStatus='AUTO_SUFFIX'},/inferred/);
});
test('extra/unknown manifest fields and malformed duplicate rig inventories fail',async()=>{
  await verifyFail(m=>{m.unexpected=true},/manifest fields/);
  await verifyFail(m=>{delete m.rights.medicalSourceGeometryEmbedded},/rights fields/);
  await verifyFail(m=>{m.rig.runtimeBoneNames.push('upperarm_l')},/unique/);
  await verifyFail(m=>{m.rig.runtimeBoneNames.push('skull')},/rest matrix/);
  await verifyFail(m=>{m.rig.restWorldByRuntimeBone.excess=id()},/rest matrix/);
  await verifyFail(m=>{m.candidateId='constructor'},/candidate ID/);
  await verifyFail(m=>{m.kind='unexpected-schema'},/unknown schema/);
});
test('source rig must map every joint bijectively with exact bind/rest matrices',async()=>{
  await verifyFail(m=>{delete m.rig.sourceToRuntimeBone.test_forearm_l},/EXACTLY/);
  await verifyFail(m=>{m.rig.sourceToRuntimeBone.test_forearm_l='upperarm_l'},/Duplicate/);
  await verifyFail(m=>{m.rig.restWorldByRuntimeBone.forearm_l=t(.2,0,0)},/Rig bind mismatch/);
  await verifyFail(m=>{m.rig.restWorldByRuntimeBone.forearm_l[0]=-1},/reflected/);
  await verifyFail(m=>{m.rig.sourceToRuntimeBone.test_forearm_l='guess'},/unknown canonical/);
});
test('source left/right labels are never inferred, even with valid numerical bind',async()=>{
  const {asset,manifest}=await fixture();
  manifest.rig.sourceToRuntimeBone={
    test_upperarm_l:'forearm_l',test_forearm_l:'upperarm_l'
  };
  const r=await validate(asset,manifest);
  assert.deepEqual(r.runtimeJointNames,['forearm_l','upperarm_l']);
  assert.equal(r.audit.verifiedAnatomicalLaterality,false);
  assert.equal(pose(r,{upperarm_l:t(1,0,0),forearm_l:t(0,2,0)})[12],0);
});
test('invalid second GLB primitive is rejected before any pose acceptance',async()=>{
  const asset=buildSyntheticBatchedGlb({
    mutate:r=>{r.meshes[1].primitives[0].mode=1}
  });
  const {manifest}=await fixture('batched');
  manifest.glb.sha256=await hash(asset);
  await assert.rejects(()=>validate(asset,manifest),/TRIANGLES/);
});
test('cannot forge verified handle or bypass missing animated joint',async()=>{
  const {asset,manifest}=await fixture();
  const r=await validate(asset,manifest);
  assert.throws(()=>pose({...r},{upperarm_l:id(),forearm_l:id()}),/validated prototype/);
  assert.throws(()=>pose(r,{upperarm_l:id()}),/missing forearm_l/);
  assert.throws(()=>pose(r,{upperarm_l:id(),forearm_l:t(NaN,0,0)}),/nonfinite/);
  const p=pose(r,{upperarm_l:t(1,0,0),forearm_l:t(0,2,0)});
  assert.equal(p[12],1);
  assert.equal(p[29],2);
});
