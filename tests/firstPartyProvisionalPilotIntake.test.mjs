import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSyntheticBatchedGlb} from './support/buildSyntheticBatchedGlb.mjs';
import {parseRestrictedBatchedSkinnedGlb} from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';
import {validateProvisionalModelHandoff,digestOriginalGlbSha256,
  HGPT_PROTOTYPE_HANDOFF_KIND} from '../src/viewer/firstPartyPrototypeModelHandoff.mjs';
const id=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const t=x=>[1,0,0,0,0,1,0,0,0,0,1,0,x,0,0,1];
const glb=()=>buildSyntheticBatchedGlb({meshCount:18,allowProvisionalPilot:true});
async function manifest(asset,layout='pilot'){
  return {
    kind:HGPT_PROTOTYPE_HANDOFF_KIND,
    candidateId:'WorkShoulderPilot_DIAGNOSTIC_ONLY',
    status:'PROTOTYPE_ONLY',
    glb:{sha256:await digestOriginalGlbSha256(asset),layout,
      sourceFeatures:{flatColors:false,uv0:false,normals:false}},
    frame:{unit:'metre',up:'Y',handedness:'right',
      basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
    rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
      thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
    rig:{sourceToRuntimeBone:{test_upperarm_l:'upperarm_l',
      test_forearm_l:'forearm_l'},
      runtimeBoneNames:['upperarm_l','forearm_l'],
      restWorldByRuntimeBone:{upperarm_l:id(),forearm_l:id()},
      lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED'},
    releaseApproved:false,
  };
}
test('G4f explicit diagnostic mode decodes/binds all 18 source meshes, never dropping parts',async()=>{
  const source=glb(),unchanged=new Uint8Array(source).slice();
  const m=await manifest(source);
  const r=await validateProvisionalModelHandoff(source,m);
  assert.equal(r.numberOfPrimitives,18);
  assert.equal(r.scene.audit.numberOfMeshes,18);
  assert.deepEqual(r.scene.batches.map(p=>p.meshIndex),
    Array.from({length:18},(_,i)=>i));
  assert.equal(r.audit.maximumRestMatrixResidual,0);
  assert.equal(r.audit.provisionalLargeSceneDiagnosticOnly,true);
  assert.equal(r.scene.audit.provisionalLargeSceneDiagnosticOnly,true);
  assert.equal(r.audit.sourceFramePhysicallyRegistered,false);
  assert.equal(r.audit.realisticWholeBodyDeformationVerified,false);
  assert.equal(r.audit.modelProductionReady,false);
  assert.deepEqual(new Uint8Array(source),unchanged);
  const palette=(await import('../src/viewer/firstPartyPrototypeModelHandoff.mjs'))
    .packProvisionalModelPose(r,{upperarm_l:t(.25),forearm_l:t(.5)});
  assert.equal(palette.length,32);
});
test('regular 1..4-mesh production adapter still refuses 18-mesh scene',async()=>{
  const source=glb();
  assert.throws(()=>parseRestrictedBatchedSkinnedGlb(source),/bounded original skinned meshes/);
  const standardManifest=await manifest(source,'batched');
  await assert.rejects(()=>validateProvisionalModelHandoff(source,
    standardManifest),/bounded original skinned meshes/);
});
test('pilot mode is never implicit or enabled with false or non-boolean flag',()=>{
  const source=glb();
  assert.throws(()=>parseRestrictedBatchedSkinnedGlb(source,
    {allowProvisionalPilot:'true'}),/pilot diagnostic opt-in must be boolean/);
  assert.throws(()=>parseRestrictedBatchedSkinnedGlb(source,
    {allowProvisionalPilot:false}),/bounded original skinned meshes/);
});
test('pilot still fails closed on extra meshes, external references and invalid laterality',async()=>{
  assert.throws(()=>buildSyntheticBatchedGlb({meshCount:25,
    allowProvisionalPilot:true}),/fixture budget invalid/);
  const source=glb();
  const m=await manifest(source);
  m.rig.lateralityStatus='AUTO_INFERRED';
  await assert.rejects(()=>validateProvisionalModelHandoff(source,m),
    /no inferred bone suffix/);
  const bad=buildSyntheticBatchedGlb({meshCount:18,allowProvisionalPilot:true,
    mutate:r=>{r.extensionsUsed=['KHR_draco_mesh_compression']}});
  assert.throws(()=>parseRestrictedBatchedSkinnedGlb(bad,
    {allowProvisionalPilot:true}),/extensions/);
});
test('diagnostic mode forbids embedded PNG bypass and unregistered Z-up manifest',async()=>{
  const source=glb(),m=await manifest(source);
  m.glb.sourceFeatures={flatColors:true,uv0:true,normals:false,
    embeddedPngBaseColor:true};
  await assert.rejects(()=>validateProvisionalModelHandoff(source,m),
    /embedded PNG source handoff requires/);
  const n=await manifest(source);n.frame.up='Z';
  await assert.rejects(()=>validateProvisionalModelHandoff(source,n),
    /metre\/Y\/right-handed/);
});
