/** G2d original first-party GLB source validation and GPU shader sources. */
import {validateNativeSkinnedMesh} from './firstPartyIndexedSkinnedMesh.mjs';
import {validateNativeSourceNormals} from './firstPartySkinnedNormalReference.mjs';
import {HGPT_EMBEDDED_PNG_KIND} from './firstPartyEmbeddedPngSource.mjs';
export const G2D_KIND='hgpt-g2d-native-moving-source-png-fourweight-normal-v1';
const requireIt=(v,s)=>{if(!v)throw new RangeError('G2d source rejected: '+s);};
export function checkG2dSource(part){
  const mesh=part?.parsed?.mesh;
  requireIt(mesh,'strict parsed source mesh required');
  const shape=validateNativeSkinnedMesh(mesh);
  validateNativeSourceNormals(mesh,part.sourceNormals);
  requireIt(part.sourceUV0 instanceof Float32Array &&
    part.sourceUV0.length===shape.vertices*2 &&
    Array.from(part.sourceUV0).every(v=>Number.isFinite(v)&&Math.abs(v)<=1024),
    'strict source UV0 required');
  const png=part.sourceBaseColorPng;
  requireIt(png?.kind===HGPT_EMBEDDED_PNG_KIND &&
    png.bytes instanceof Uint8Array && png.bytes.length>=57 &&
    png.bytes.length<=8*1024*1024 &&
    Number.isSafeInteger(png.width)&&Number.isSafeInteger(png.height)&&
    png.width>0&&png.height>0&&png.width*png.height<=4194304 &&
    png.sampler?.minFilter===9729&&png.sampler?.magFilter===9729 &&
    png.sampler?.wrapS===33071&&png.sampler?.wrapT===33071,
    'embedded source PNG + bounded sampler required');
  requireIt(Array.isArray(part.materialColor)&&part.materialColor.length===3 &&
    part.materialColor.every(v=>Number.isFinite(v)&&v>=0&&v<=1),
    'opaque source material tint required');
  return {mesh,shape,uv:part.sourceUV0.slice(),normal:part.sourceNormals.slice(),
    png:png.bytes.slice(),width:png.width,height:png.height,tint:[...part.materialColor]};
}
export const G2D_VERTEX=[
  '#version 300 es','precision highp float;','precision highp sampler2D;',
  'layout(location=0) in vec3 aPosition;',
  'layout(location=1) in uvec4 aJoints;',
  'layout(location=2) in vec4 aWeights;',
  'layout(location=3) in vec2 aUV;',
  'layout(location=4) in vec3 aNormal;',
  'uniform mat4 uVP;','uniform sampler2D uPalette;',
  'out vec2 vUV;','out vec3 vWorldPosition;','out vec3 vWorldNormal;',
  'mat4 bone(uint j){int x=int(j)*4;return mat4(',
  'texelFetch(uPalette,ivec2(x,0),0),',
  'texelFetch(uPalette,ivec2(x+1,0),0),',
  'texelFetch(uPalette,ivec2(x+2,0),0),',
  'texelFetch(uPalette,ivec2(x+3,0),0));}',
  'void main(){vec4 p=vec4(0.0);vec3 n=vec3(0.0);',
  'vec4 rest=vec4(aPosition,1.0);',
  'p+=bone(aJoints.x)*rest*aWeights.x;',
  'p+=bone(aJoints.y)*rest*aWeights.y;',
  'p+=bone(aJoints.z)*rest*aWeights.z;',
  'p+=bone(aJoints.w)*rest*aWeights.w;',
  'n+=mat3(bone(aJoints.x))*aNormal*aWeights.x;',
  'n+=mat3(bone(aJoints.y))*aNormal*aWeights.y;',
  'n+=mat3(bone(aJoints.z))*aNormal*aWeights.z;',
  'n+=mat3(bone(aJoints.w))*aNormal*aWeights.w;',
  'vWorldPosition=p.xyz;vWorldNormal=normalize(n);vUV=aUV;',
  'gl_Position=uVP*p;}'
].join('\n');
export const G2D_FRAGMENT=[
  '#version 300 es','precision highp float;',
  'in vec2 vUV;','in vec3 vWorldNormal;',
  'uniform sampler2D uColor;','uniform vec3 uTint;',
  'out vec4 outColor;',
  'void main(){float light=0.30+0.70*max(dot(normalize(vWorldNormal),',
  'normalize(vec3(0.32,0.50,0.81))),0.0);',
  'outColor=vec4(texture(uColor,vUV).rgb*uTint*light,1.0);}'
].join('\n');
