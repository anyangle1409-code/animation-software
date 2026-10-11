import {G2D_VERTEX,G2D_FRAGMENT} from './firstPartyG2dShader.mjs';
export function compileG2dProgram(gl){
 const shaders=[G2D_VERTEX,G2D_FRAGMENT].map((source,i)=>{
  const s=gl.createShader(i?gl.FRAGMENT_SHADER:gl.VERTEX_SHADER);
  gl.shaderSource(s,source);gl.compileShader(s);
  if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));
  return s;
 });
 const p=gl.createProgram();
 for(const s of shaders)gl.attachShader(p,s);
 gl.transformFeedbackVaryings(p,['vWorldPosition','vWorldNormal'],gl.SEPARATE_ATTRIBS);
 gl.linkProgram(p);
 for(const s of shaders)gl.deleteShader(s);
 if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));
 return p;
}
