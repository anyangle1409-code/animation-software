/**
 * G2c independent project-owned CPU DIRECTIONAL LBS normal reference.
 * This is a verification oracle, NOT a production per-vertex skinning path.
 * Four rigid joint rotations are weighted and renormalized per source unit
 * normal. This is linear-blend normal approximation, not PBR/tangent support
 * and not the inverse transpose of an arbitrary nonrigid blended Jacobian.
 */
import {validateNativeSkinnedMesh} from './firstPartyIndexedSkinnedMesh.mjs';
import {buildNativeJointSkinPalette} from './firstPartyGpuPaletteSkinning.mjs';
export const HGPT_NORMAL_REFERENCE_KIND='hgpt-first-party-four-weight-directional-normal-reference-v1';
export function validateNativeSourceNormals(mesh,sourceNormals){
  const shape=validateNativeSkinnedMesh(mesh);
  if(!(sourceNormals instanceof Float32Array)||
    sourceNormals.length!==shape.vertices*3)
    throw new RangeError('Normal reference requires one typed XYZ source normal per source vertex');
  for(let i=0;i<sourceNormals.length;i+=3){
    const x=sourceNormals[i],y=sourceNormals[i+1],z=sourceNormals[i+2];
    const length=Math.hypot(x,y,z);
    if(!Number.isFinite(length)||length<.998||length>1.002)
      throw new RangeError('Source normal must be finite and near unit length');
  }
  return shape;
}
export function referenceSkinOriginalUnitNormals(mesh,sourceNormals,posedWorld){
  const shape=validateNativeSourceNormals(mesh,sourceNormals);
  const palette=buildNativeJointSkinPalette(mesh,posedWorld);
  const normals=new Float32Array(shape.vertices*3);
  for(let i=0;i<shape.vertices;i++){
    const x=sourceNormals[i*3],y=sourceNormals[i*3+1],z=sourceNormals[i*3+2];
    let outX=0,outY=0,outZ=0;
    for(let j=0;j<4;j++){
      const idx=i*4+j;
      const weight=mesh.weights[idx],at=mesh.jointIndices[idx]*16;
      outX+=weight*(palette[at]*x+palette[at+4]*y+palette[at+8]*z);
      outY+=weight*(palette[at+1]*x+palette[at+5]*y+palette[at+9]*z);
      outZ+=weight*(palette[at+2]*x+palette[at+6]*y+palette[at+10]*z);
    }
    const magnitude=Math.hypot(outX,outY,outZ);
    if(!Number.isFinite(magnitude)||magnitude<1e-6)
      throw new RangeError('Weighted source normal cancels: requires explicit corrective skin handling');
    normals[i*3]=outX/magnitude;
    normals[i*3+1]=outY/magnitude;
    normals[i*3+2]=outZ/magnitude;
  }
  return normals;
}
