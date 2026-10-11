import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSyntheticTexturedBatchedGlb}
  from './support/buildSyntheticTexturedBatchedGlb.mjs';
import {buildSyntheticBatchedGlb}
  from './support/buildSyntheticBatchedGlb.mjs';
import {
  HGPT_PROTOTYPE_HANDOFF_KIND as KIND,
  digestOriginalGlbSha256 as hash,
  validateProvisionalModelHandoff as validate,
  packProvisionalModelPose as pose,
} from '../src/viewer/firstPartyPrototypeModelHandoff.mjs';
import {
  HGPT_PROTOTYPE_CLIP_KIND,
  compileProvisionalPoseSequence,
} from '../src/viewer/firstPartyPrototypePoseSequence.mjs';
import {HGPT_EMBEDDED_PNG_KIND}
  from '../src/viewer/firstPartyEmbeddedPngSource.mjs';
import {deformIndexedSkin}
  from '../src/viewer/firstPartyIndexedSkinnedMesh.mjs';

const I=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const T=x=>[1,0,0,0,0,1,0,0,0,0,1,0,x,0,0,1];
async function manifest(asset,{
  features={flatColors:true,uv0:true,normals:false,
    embeddedPngBaseColor:true},
  layout='batched',
}={}){
  return {
    kind:KIND,candidateId:'ProjectOriginalTestOnly',
    status:'PROTOTYPE_ONLY',
    glb:{sha256:await hash(asset),layout,sourceFeatures:features},
    frame:{unit:'metre',up:'Y',handedness:'right',
      basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
    rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
      thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
    rig:{sourceToRuntimeBone:{
      test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
      runtimeBoneNames:['upperarm_l','forearm_l'],
      restWorldByRuntimeBone:{upperarm_l:I(),forearm_l:I()},
      lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED'},
    releaseApproved:false,
  };
}
async function accepts(asset,overrides){
  return validate(asset,await manifest(asset,overrides));
}
const expectedColor=[[247,20,23],[15,244,32]];
test('G4 SHA-bound original model contract NOW accepts strict real embedded original PNG source materials',async()=>{
  const source=buildSyntheticTexturedBatchedGlb();
  const exact=new Uint8Array(source).slice();
  const result=await accepts(source);
  assert.deepEqual(new Uint8Array(source),exact);
  assert.equal(result.numberOfPrimitives,2);
  assert.equal(result.sourceSha256,await hash(source));
  assert.deepEqual(result.runtimeJointNames,['upperarm_l','forearm_l']);
  assert.equal(result.scene.audit.numberOfMeshes,2);
  assert.equal(result.scene.audit.embeddedPngBaseColorSourceValidated,true);
  assert.equal(result.audit.sourceEmbeddedPngBaseColorValidated,true);
  assert.equal(result.audit.allGLBPrimitivesDecodedAndBound,true);
  assert.equal(result.audit.maximumRestMatrixResidual,0);
  for(const [index,part] of result.scene.batches.entries()){
    assert.equal(part.sourceBaseColorPng.kind,HGPT_EMBEDDED_PNG_KIND);
    assert.equal(part.sourceBaseColorPng.width,2);
    assert.equal(part.sourceBaseColorPng.height,2);
    assert.equal(part.sourceMaterialIndex,index);
    assert.equal(part.sourceBaseColorPng.sourceTextureIndex,index);
    assert.equal(part.sourceBaseColorPng.bytes[0],137);
    assert.equal(part.sourceUV0.length,6);
    assert.deepEqual(part.materialColor,[1,1,1]);
    assert.deepEqual(Array.from(part.parsed.mesh.weights.slice(0,4)),
      [.75,.25,0,0]);
  }
  assert.equal(result.audit.medicallyApprovedHumanSkeleton,false);
  assert.equal(result.audit.verifiedAnatomicalLaterality,false);
  assert.equal(result.audit.independentlyVerifiedSourceRights,false);
  assert.equal(result.audit.modelProductionReady,false);
});
test('inherited original two-joint full pose path retains source palette with textured GLB',async()=>{
  const source=buildSyntheticTexturedBatchedGlb();
  const model=await accepts(source);
  const clip={
    kind:HGPT_PROTOTYPE_CLIP_KIND,candidateId:model.candidateId,
    sourceSha256:model.sourceSha256,
    exerciseId:'overhead_press',approvalStatus:'DIAGNOSTIC_ONLY',
    durationSeconds:1,
    frames:[
      {timeSeconds:0,posedWorldByRuntimeBone:{
        upperarm_l:I(),forearm_l:I()}},
      {timeSeconds:1,posedWorldByRuntimeBone:{
        upperarm_l:T(.3),forearm_l:T(.5)}}
    ]
  };
  const frames=compileProvisionalPoseSequence(model,clip);
  assert.equal(frames.frames.length,2);
  assert.equal(frames.audit.allFramesOriginalSkinOrderNumericallyScreened,true);
  const palette=pose(model,clip.frames[1].posedWorldByRuntimeBone);
  assert.equal(palette.length,32);
  for(const part of model.scene.batches){
    const skinned=deformIndexedSkin(part.parsed.mesh,palette);
    assert.equal(skinned.triangleCount,1);
    assert.ok(Math.abs(
      skinned.positions[0]-part.parsed.mesh.positions[0]-.35)<1e-6);
    assert.equal(part.sourceBaseColorPng.kind,HGPT_EMBEDDED_PNG_KIND);
  }
});
test('legacy original untextured manifest with THREE explicit flags remains compatible',async()=>{
  const source=buildSyntheticBatchedGlb();
  const model=await accepts(source,{features:{
    flatColors:false,uv0:false,normals:false,
  }});
  assert.equal(model.numberOfPrimitives,2);
  assert.equal(model.audit.sourceEmbeddedPngBaseColorValidated,false);
});
test('legacy source manifest may not smuggle in PNG image data without opt-in',async()=>{
  const source=buildSyntheticTexturedBatchedGlb();
  const legacy=await manifest(source,{features:{
    flatColors:true,uv0:true,normals:false
  }});
  await assert.rejects(()=>validate(source,legacy),/texture\/unsupported/);
});
test('new flag must be a real boolean and all PNG prerequisites explicit',async()=>{
  const source=buildSyntheticTexturedBatchedGlb();
  const flags={flatColors:true,uv0:true,normals:false,
    embeddedPngBaseColor:true};
  for(const key of ['flatColors','uv0','embeddedPngBaseColor']){
    const wrong={...flags,[key]:false};
    await assert.rejects(()=>accepts(source,{features:wrong}),
      /embedded PNG source handoff requires|material|texture/);
  }
  await assert.rejects(()=>accepts(source,{features:{
    ...flags,embeddedPngBaseColor:'yes',
  }}),/explicit booleans/);
  await assert.rejects(()=>accepts(source,{features:{
    ...flags,externalImages:true,
  }}),/GLB source features fields/);
  await assert.rejects(()=>accepts(source,{
    features:flags,layout:'single',
  }),/embedded PNG source handoff requires/);
});
test('texture link with external URL fails AFTER proper matching source SHA',async()=>{
  const url=buildSyntheticTexturedBatchedGlb({mutate:root=>{
    root.images[0].uri='https://example.invalid/untrusted.png';
  }});
  await assert.rejects(()=>accepts(url),/must be embedded PNG/);
  const badSampler=buildSyntheticTexturedBatchedGlb({mutate:root=>{
    root.samplers[0].wrapS=10497;
  }});
  await assert.rejects(()=>accepts(badSampler),/linear clamp-to-edge/);
  const missingUV=buildSyntheticTexturedBatchedGlb({mutate:root=>{
    delete root.meshes[1].primitives[0].attributes.TEXCOORD_0;
  }});
  await assert.rejects(()=>accepts(missingUV),/UV0/);
});
test('source PNG CRC and material source references cannot bypass G4 validation',async()=>{
  const brokenCRC=buildSyntheticTexturedBatchedGlb({mutate:(root,bin)=>{
    const b=root.bufferViews[root.images[0].bufferView];
    bin[b.byteOffset+8+4+13]^=1;
  }});
  await assert.rejects(()=>accepts(brokenCRC),/CRC mismatch/);
  const missingLink=buildSyntheticTexturedBatchedGlb({mutate:root=>{
    root.materials[1].pbrMetallicRoughness.baseColorTexture.index=5;
  }});
  await assert.rejects(()=>accepts(missingLink),/baseColorTexture link/);
});
test('no stale source SHA or doctored second mesh permitted',async()=>{
  const asset=buildSyntheticTexturedBatchedGlb();
  const old=await manifest(asset);
  const changed=buildSyntheticTexturedBatchedGlb({imageRGBs:[
    [200,20,23],expectedColor[1],
  ]});
  await assert.rejects(()=>validate(changed,old),/source asset SHA-256 mismatch/);
  const second=buildSyntheticTexturedBatchedGlb({mutate:root=>{
    root.meshes[1].primitives[0].mode=1;
  }});
  await assert.rejects(()=>accepts(second),/TRIANGLES/);
});
