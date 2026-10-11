import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,rm,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync,spawnSync} from 'node:child_process';
import {buildSyntheticFirstPartyGlb} from './support/buildSyntheticFirstPartyGlb.mjs';
import {
  HGPT_PROTOTYPE_HANDOFF_KIND as KIND,
  digestOriginalGlbSha256 as sha256,
} from '../src/viewer/firstPartyPrototypeModelHandoff.mjs';

const ID=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const cli='scripts/verify-provisional-handoff.mjs';
async function withFixture(callback){
  const dir=await mkdtemp(join(tmpdir(),'hgpt-g4-handoff-'));
  try{
    const glb=buildSyntheticFirstPartyGlb();
    const gpath=join(dir,'original.glb'), mpath=join(dir,'handoff.json');
    const m={
      kind:KIND,candidateId:'WorkOriginalPrototype',status:'PROTOTYPE_ONLY',
      glb:{sha256:await sha256(glb),layout:'single',
        sourceFeatures:{flatColors:false,uv0:false,normals:false}},
      frame:{unit:'metre',up:'Y',handedness:'right',
        basisStatus:'DECLARED_NOT_INDEPENDENTLY_REGISTERED'},
      rights:{projectAuthoredClaim:true,medicalSourceGeometryEmbedded:false,
        thirdPartyCharacterGeometryEmbedded:false,independentRightsReview:false},
      rig:{sourceToRuntimeBone:{
        test_upperarm_l:'upperarm_l',test_forearm_l:'forearm_l'},
        runtimeBoneNames:['upperarm_l','forearm_l'],
        restWorldByRuntimeBone:{upperarm_l:ID,forearm_l:ID},
        lateralityStatus:'EXPLICIT_MAPPING_UNVERIFIED'},
      releaseApproved:false,
    };
    await writeFile(gpath,Buffer.from(glb));
    await writeFile(mpath,JSON.stringify(m));
    await callback({gpath,mpath,m});
  }finally{await rm(dir,{recursive:true,force:true});}
}
test('Work offline CLI verifies real GLB file, reports only safe source hashes',async()=>{
  await withFixture(({gpath,mpath})=>{
    const output=execFileSync(process.execPath,[cli,gpath,mpath],{
      encoding:'utf8',timeout:15000,
    });
    const report=JSON.parse(output);
    assert.equal(report.verdict,'VERIFIED_PROTOTYPE_ONLY');
    assert.equal(report.primitives,1);
    assert.deepEqual(report.runtimeJointNames,['upperarm_l','forearm_l']);
    assert.equal(report.audit.medicallyApprovedHumanSkeleton,false);
    assert.equal(report.audit.modelProductionReady,false);
    assert.ok(!output.includes(gpath),'local private filepath must not leak');
  });
});
test('Work offline CLI refuses changed hash rather than silently accepting stale geometry',async()=>{
  await withFixture(async({gpath,mpath,m})=>{
    m.glb.sha256='0'.repeat(64);
    await writeFile(mpath,JSON.stringify(m));
    const p=spawnSync(process.execPath,[cli,gpath,mpath],{
      encoding:'utf8',timeout:15000,
    });
    assert.equal(p.status,1);
    assert.match(p.stderr,/SHA-256 mismatch/);
    assert.equal(p.stdout,'');
  });
});
test('Work offline CLI refuses missing file arguments without success outputs',()=>{
  const p=spawnSync(process.execPath,[cli],{encoding:'utf8',timeout:15000});
  assert.equal(p.status,1);
  assert.match(p.stderr,/Usage:/);
  assert.equal(p.stdout,'');
});
