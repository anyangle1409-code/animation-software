import test from 'node:test';
import assert from 'node:assert/strict';
import {
  convertNativeWorkZupRowsToGltfYupWorld as convert,
  registerWorkNativePoseSamplesToOriginalGLTF as register,
  readRegisteredWorkPoseFrame as frame,
} from '../src/viewer/firstPartyWorkNativePoseRegistration.mjs';
function rest(){
  return [
    [1,0,0,.15],[0,1,0,.25],[0,0,1,1.6],[0,0,0,1],
  ];
}
const toRows=a=>a.map(x=>[...x]);
test('actual Blender axis basis left-multiplies original native Z-up WORLD (not conjugation)',()=>{
  const x=convert(rest());
  assert.deepEqual([...x],[
    1,0,0,0,
    0,0,-1,0,
    0,1,0,0,
    .15,1.6,-.25,1
  ].map((v,i)=>i===12?.15000000596046448:i===13?1.600000023841858:v));
});
test('source-native arbitrary rigid world orientation remains proper after proper axis basis',()=>{
  const angle=.7,c=Math.cos(angle),s=Math.sin(angle);
  const rows=[
    [c,-s,0,.22],[s,c,0,-.15],[0,0,1,1.43],[0,0,0,1],
  ];
  const x=convert(rows);
  assert.ok(Math.abs(x[12]-.22)<1e-6);
  assert.ok(Math.abs(x[13]-1.43)<1e-6);
  assert.ok(Math.abs(x[14]-.15)<1e-6);
  const ax=[x[0],x[1],x[2]],ay=[x[4],x[5],x[6]],az=[x[8],x[9],x[10]];
  const det=ax[0]*(ay[1]*az[2]-ay[2]*az[1]) -
    ax[1]*(ay[0]*az[2]-ay[2]*az[0]) +
    ax[2]*(ay[0]*az[1]-ay[1]*az[0]);
  assert.ok(Math.abs(det-1)<1e-6,'preserve right-handed Blender orientation');
});
test('row-major error, shell payload and non-affine matrices fail closed',()=>{
  assert.throws(()=>convert(null),/4x4 finite/);
  assert.throws(()=>convert(new Array(16).fill(0)),/4x4 finite/);
  const invalid=toRows(rest());invalid[2][3]=Infinity;
  assert.throws(()=>convert(invalid),/4x4 finite/);
  const bad=toRows(rest());bad[3][0]=.1;
  assert.throws(()=>convert(bad),/non-affine/);
});
test('unverified G4/G4j model handles and forged pose handles must be refused',()=>{
  assert.throws(()=>register({kind:'fake'},null,null),
    /original verified source Work G4 pilot/);
  assert.throws(()=>frame({},0),
    /only in-memory source validated/);
});
