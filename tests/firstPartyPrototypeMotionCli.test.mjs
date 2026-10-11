import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {buildSyntheticFirstPartyGlb} from './support/buildSyntheticFirstPartyGlb.mjs';
import {HGPT_PROTOTYPE_HANDOFF_KIND as MK,digestOriginalGlbSha256}
  from '../src/viewer/firstPartyPrototypeModelHandoff.mjs';
import {HGPT_PROTOTYPE_CLIP_KIND as CK}
  from '../src/viewer/firstPartyPrototypePoseSequence.mjs';

const id=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const t=x=>[1,0,0,0,0,1,0,0,0,0,1,0,x,0,0,1];
const cmd='scripts/verify-provisional-motion.mjs';
async function withFiles(fn){
  const dir=await mkdtemp(join(tmpdir(),'hgpt-g4b-'));
  try{
    const glb=buildSyntheticFirstPartyGlb(),sha=await digestOriginalGlbSha256(glb);
    const m={
      kind:MK,candidateId:'SynthOriginal',status:'PROTOTYPE_ONLY',
      glb:{sha256:sha,layout:'single',sourceFeatures:{
        flatColors:false,uv0:false,normals:false}},
      frame:{unit:'metre',up:'Y',handedness:'right',
        basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
      rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
        thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
      rig:{
        sourceToRuntimeBone:{test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
        runtimeBoneNames:['upperarm_l','forearm_l'],
        restWorldByRuntimeBone:{upperarm_l:id(),forearm_l:id()},
        lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED'},
      releaseApproved:false,
    };
    const p={
      kind:CK,candidateId:'SynthOriginal',sourceSha256:sha,
      exerciseId:'diagnostic-elbow',approvalStatus:'DIAGNOSTIC_ONLY',
      durationSeconds:1,
      frames:[
        {timeSeconds:0,posedWorldByRuntimeBone:{
          upperarm_l:id(),forearm_l:id()}},
        {timeSeconds:1,posedWorldByRuntimeBone:{
          upperarm_l:t(.2),forearm_l:t(.3)}},
      ]
    };
    const files=[join(dir,'model.glb'),join(dir,'handoff.json'),join(dir,'poses.json')];
    await writeFile(files[0],Buffer.from(glb));
    await writeFile(files[1],JSON.stringify(m));
    await writeFile(files[2],JSON.stringify(p));
    await fn(files,p,m);
  }finally{await rm(dir,{recursive:true,force:true});}
}
test('actual local model + rig + motion files jointly pass offline preflight',async()=>{
  await withFiles(files=>{
    const p=spawnSync(process.execPath,[cmd,...files],{encoding:'utf8',timeout:15000});
    assert.equal(p.status,0,p.stderr);
    const r=JSON.parse(p.stdout);
    assert.equal(r.verdict,'VERIFIED_NUMERIC_PROTOTYPE_ONLY');
    assert.equal(r.frameCount,2);
    assert.equal(r.sourcePaletteJoints,2);
    assert.equal(r.modelAudit.modelProductionReady,false);
    assert.equal(r.motionAudit.wholeBodyExerciseAccuracyAccepted,false);
    assert.equal(r.motionAudit.productionClipApproved,false);
    assert.ok(!p.stdout.includes(files[0]),'private path must not leak');
  });
});
test('motion cannot be swapped after a model passes SHA and bind',async()=>{
  await withFiles(async(files,clip)=>{
    clip.sourceSha256='f'.repeat(64);
    await writeFile(files[2],JSON.stringify(clip));
    const p=spawnSync(process.execPath,[cmd,...files],{encoding:'utf8',timeout:15000});
    assert.equal(p.status,1);
    assert.match(p.stderr,/SHA\/candidate mismatch/);
    assert.equal(p.stdout,'');
  });
});
test('offline CLI rejects missing inputs and never reports false success',()=>{
  const p=spawnSync(process.execPath,[cmd],{encoding:'utf8',timeout:15000});
  assert.equal(p.status,1);
  assert.match(p.stderr,/Usage/);
  assert.equal(p.stdout,'');
});
