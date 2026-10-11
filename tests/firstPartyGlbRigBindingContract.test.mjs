import test from 'node:test';
import assert from 'node:assert/strict';
import {parseRestrictedSkinnedGlb} from '../src/viewer/firstPartyGlbSkinnedGeometry.mjs';
import {buildSyntheticFirstPartyGlb} from './support/buildSyntheticFirstPartyGlb.mjs';
import {deformIndexedSkin} from '../src/viewer/firstPartyIndexedSkinnedMesh.mjs';
import {validateNativeGLBToRigBinding as bind,packMappedWorldPalette as posePalette,NATIVE_RIG_BIND_CONTRACT} from '../src/viewer/firstPartyGlbRigBindingContract.mjs';

const id=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const t=(x,y,z)=>[1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1];
const parsed=()=>parseRestrictedSkinnedGlb(buildSyntheticFirstPartyGlb());
const opts=()=>({
  allowedCanonicalNames:['upperarm_l','forearm_l','root'],
  sourceToCanonical:{
    test_upperarm_l:'upperarm_l',
    test_forearm_l:'forearm_l',
  },
  canonicalRestWorldByBone:{
    upperarm_l:id(),
    forearm_l:id(),
  }
});
test('2 original synthetic GLB source joints map by explicit names and order',()=>{
  const plan=bind(parsed(),opts());
  assert.equal(plan.kind,NATIVE_RIG_BIND_CONTRACT);
  assert.equal(plan.verifiedJointCount,2);
  assert.equal(plan.numericallyCompatibleSameFrameRestBinds,true);
  assert.equal(plan.maximumMatrixResidual,0);
  assert.deepEqual(plan.orderedSourceJointNames,['test_upperarm_l','test_forearm_l']);
  assert.deepEqual(plan.orderedCanonicalBoneNames,['upperarm_l','forearm_l']);
});
test('GLB binder drives existing first-party four-weight deform exactly',()=>{
  const skin=parsed();
  const plan=bind(skin,opts());
  const posed=posePalette(plan,{
    upperarm_l:t(1,0,0),
    forearm_l:t(0,2,0)
  });
  const deform=deformIndexedSkin(skin.mesh,posed);
  assert.ok(Math.abs(deform.positions[0]-.75)<1e-6);
  assert.ok(Math.abs(deform.positions[1]-.5)<1e-6);
  assert.ok(Math.abs(deform.positions[3]-1.75)<1e-6);
  assert.ok(Math.abs(deform.positions[4]-.5)<1e-6);
  assert.equal(deform.triangleCount,1);
});
test('source-to-canonical names are not inferred from letter suffix',()=>{
  const options=opts();
  options.sourceToCanonical={
    test_upperarm_l:'forearm_l',
    test_forearm_l:'upperarm_l'
  };
  const plan=bind(parsed(),options);
  assert.deepEqual(plan.orderedCanonicalBoneNames,['forearm_l','upperarm_l']);
  assert.equal(plan.audit.sourceLateralityInferredFromSuffix,false);
});
test('source inverse bind cannot be silently retargeted to a displaced rig rest skeleton',()=>{
  const options=opts();
  options.canonicalRestWorldByBone.forearm_l=t(0.2,0,0);
  assert.throws(()=>bind(parsed(),options),/Rig bind mismatch/);
});
test('bind refuses unmapped/extra GLB source joint identity keys',()=>{
  const options=opts();
  delete options.sourceToCanonical.test_forearm_l;
  assert.throws(()=>bind(parsed(),options),/EXACTLY/);
  options.sourceToCanonical.unknown='root';
  assert.throws(()=>bind(parsed(),options),/EXACTLY/);
});
test('unknown legitimate source identity cannot be accepted by rig name guess',()=>{
  const options=opts();
  options.sourceToCanonical.test_forearm_l='carpal_new_guess';
  assert.throws(()=>bind(parsed(),options),/unknown canonical/);
});
test('two different glTF source joints must not collide onto one rig bone',()=>{
  const options=opts();
  options.sourceToCanonical.test_forearm_l='upperarm_l';
  assert.throws(()=>bind(parsed(),options),/Duplicate canonical/);
});
test('explicit rig inventory must be unique and anatomically named, not prototypes',()=>{
  const options=opts();
  options.allowedCanonicalNames.push('forearm_l');
  assert.throws(()=>bind(parsed(),options),/unique trusted rig names/);
  const other=opts();
  other.sourceToCanonical.test_upperarm_l='__proto__';
  assert.throws(()=>bind(parsed(),other),/unknown canonical/);
});
test('no missing or NaN original rest matrix is allowed',()=>{
  const options=opts();
  delete options.canonicalRestWorldByBone.forearm_l;
  assert.throws(()=>bind(parsed(),options),/missing forearm_l/);
  const other=opts();
  other.canonicalRestWorldByBone.forearm_l[4]=NaN;
  assert.throws(()=>bind(parsed(),other),/nonfinite/);
});
test('malformed and non-affine rigid transforms fail closed before use',()=>{
  const options=opts();
  options.canonicalRestWorldByBone.forearm_l=new Array(16).fill(0);
  assert.throws(()=>bind(parsed(),options),/affine/);
  const other=opts();
  other.canonicalRestWorldByBone.forearm_l=[1,2];
  assert.throws(()=>bind(parsed(),other),/16 numeric/);
});
test('reflected coordinate frames cannot turn source anatomical left into right silently',()=>{
  const options=opts();
  options.canonicalRestWorldByBone.upperarm_l=[
    -1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1
  ];
  assert.throws(()=>bind(parsed(),options),/reflected/);
});
test('non-uniform scaling and unit-length shear must not pass compatibility',()=>{
  const options=opts();
  options.canonicalRestWorldByBone.upperarm_l=[
    2,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1
  ];
  assert.throws(()=>bind(parsed(),options),/scale/);
  const other=opts();
  other.canonicalRestWorldByBone.upperarm_l=[
    1,.5,0,0,0,Math.sqrt(.75),0,0,0,0,1,0,0,0,0,1
  ];
  assert.throws(()=>bind(parsed(),other),/shear/);
});
test('stale or malformed incoming model is refused',()=>{
  assert.throws(()=>bind(null,opts()),/restricted GLB/);
  assert.throws(()=>bind({kind:'unknown'},opts()),/restricted GLB/);
  const bad=parsed();
  bad.jointNodeNames.push('injected');
  assert.throws(()=>bind(bad,opts()),/joint identity\/palette invalid/);
});
test('tampered inverse bind with source/rig mismatch cannot be auto-corrected',()=>{
  const bad=parsed();
  bad.mesh.inverseBindMatrices[12]=5;
  assert.throws(()=>bind(bad,opts()),/Rig bind mismatch/);
});
test('pose palette must preserve original source GLB joint order even with reordered object keys',()=>{
  const plan=bind(parsed(),opts());
  const pose=posePalette(plan,{forearm_l:t(0,2,0),upperarm_l:t(1,0,0)});
  assert.equal(pose[12],1);
  assert.equal(pose[28],0);
  assert.equal(pose[29],2);
});
test('missing/invalid runtime pose matrices rejected at boundary, no bind rollback',()=>{
  const plan=bind(parsed(),opts());
  assert.throws(()=>posePalette(plan,{forearm_l:id()}),/missing upperarm_l/);
  assert.throws(()=>posePalette(plan,{upperarm_l:id(),forearm_l:t(NaN,0,0)}),/nonfinite/);
  assert.throws(()=>posePalette({},{}),/Validated native/);
});
test('numeric match is not evidence of accepted medical anatomy or final model provenance',()=>{
  const a=bind(parsed(),opts()).audit;
  for(const key of [
    'sourceLateralityInferredFromSuffix','autoScaleOrHandednessConversion',
    'originalGltfSourceJointHierarchyPhysicallyVerified',
    'independentAnatomicalJointCentresAccepted',
    'sourceFramePhysicallyRegistered',
    'originalCharacterAssetProvenanceApproved',
    'fullBodyDeformationAccepted','finalRuntimeApproval'
  ])assert.equal(a[key],false,key+' must not be silently accepted');
  assert.equal(a.restWorldInverseBindIdentityOnly,true);
});
