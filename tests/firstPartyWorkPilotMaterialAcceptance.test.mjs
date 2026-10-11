import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSyntheticBatchedGlb}
  from './support/buildSyntheticBatchedGlb.mjs';
import {parseRestrictedBatchedSkinnedGlb as parse}
  from '../src/viewer/firstPartyGlbSkinnedBatches.mjs';

const material=(roughness=.4,doubleSided=true)=>({
  name:'WorkOriginalSourceDiagnostic',
  doubleSided,
  pbrMetallicRoughness:{
    baseColorFactor:[.84,.62,.19,1],
    metallicFactor:0,roughnessFactor:roughness,
  },
});
function source({pilot=true,roughness=.4,doubleSided=true,
  omitMaterial=false}={}){
  return buildSyntheticBatchedGlb({
    meshCount:pilot?18:2,allowProvisionalPilot:pilot,
    mutate:r=>{
      r.materials=[material(roughness,doubleSided)];
      for(const mesh of r.meshes)
        for(const primitive of mesh.primitives)
          if(!omitMaterial)primitive.material=0;
      if(pilot){
        const roots=[...r.scenes[0].nodes],p=r.nodes.length;
        r.nodes.push({name:'AuthorIdentitySceneRoot',children:roots});
        r.scenes[0].nodes=[p];
      }
    },
  });
}
test('actual-type Work pilot doubleSided original material and roughness metadata preserved across 18 meshes',()=>{
  const raw=source(),copy=new Uint8Array(raw).slice();
  const scene=parse(raw,{allowProvisionalPilot:true,
    allowSourceFlatColors:true,allowSourceUV0:true});
  assert.equal(scene.audit.numberOfMeshes,18);
  assert.equal(scene.audit.pilotSourceTwoSidedAndRoughnessMetadataPreserved,true);
  assert.equal(scene.audit.originalUV0NeverFabricated,true);
  assert.equal(scene.audit.clinicalAnatomyApproved,false);
  assert.equal(scene.batches.length,18);
  for(const part of scene.batches){
    assert.equal(part.sourceDoubleSided,true);
    assert.ok(Math.abs(part.sourceRoughness-.4)<1e-8);
    assert.equal(part.sourceMaterialIndex,0);
    assert.deepEqual(part.materialColor,[.84,.62,.19]);
    assert.equal(part.sourceUV0,null);
    assert.equal(part.sourcePBRLightingActuallyImplemented,false);
  }
  assert.deepEqual(new Uint8Array(raw),copy);
});
test('non-pilot strict original contract continues refusing two-sided and non-matte material',()=>{
  assert.throws(()=>parse(source({pilot:false}),{
    allowSourceFlatColors:true}),/two-sided material shader parity not proven/);
  assert.throws(()=>parse(source({pilot:false,doubleSided:false}),{
    allowSourceFlatColors:true}),/source metallic\/roughness outside supported preview/);
});
test('pilot rejects impossible roughness/metallic combinations rather than silently remapping PBR',()=>{
  for(const bad of [-.2,1.2,NaN,Infinity]){
    const b=source({roughness:bad});
    assert.throws(()=>parse(b,{
      allowProvisionalPilot:true,allowSourceFlatColors:true,allowSourceUV0:true
    }),/metallic\/roughness outside supported preview/);
  }
});
test('pilot source retains absent UV0 only for original untextured primitives',()=>{
  const r=parse(source(),{allowProvisionalPilot:true,
    allowSourceFlatColors:true,allowSourceUV0:true});
  assert.ok(r.batches.every(b=>b.sourceUV0===null));
});
test('pilot rejects unsupported alpha, source extras and unreferenced materials',()=>{
  const alpha=buildSyntheticBatchedGlb({
    meshCount:18,allowProvisionalPilot:true,
    mutate:r=>{
      r.materials=[{...material(),alphaMode:'BLEND'}];
      for(const mesh of r.meshes)mesh.primitives[0].material=0;
    }
  });
  assert.throws(()=>parse(alpha,{allowProvisionalPilot:true,
    allowSourceFlatColors:true}),/only OPAQUE/);
  const invalid=buildSyntheticBatchedGlb({
    meshCount:18,allowProvisionalPilot:true,
    mutate:r=>{
      r.materials=[{...material(),extensions:{notApproved:1}}];
      for(const mesh of r.meshes)mesh.primitives[0].material=0;
    }
  });
  assert.throws(()=>parse(invalid,{allowProvisionalPilot:true,
    allowSourceFlatColors:true}),/unsupported glTF material field/);
});
test('pilot source metadata is not a claim to a production material or real human skeleton',()=>{
  const r=parse(source(),{allowProvisionalPilot:true,allowSourceFlatColors:true,
    allowSourceUV0:true});
  assert.equal(r.audit.metallicRoughnessPBRImplemented,false);
  assert.equal(r.audit.sourceBoneHierarchyChanged,false);
  assert.equal(r.audit.actualOriginalHumanMeshUsed,false);
  assert.equal(r.audit.rightsAndProvenanceApproved,false);
  assert.equal(r.audit.productionRuntimeReady,false);
});
