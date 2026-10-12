/**
 * G4y: opt-in real RGBA32F joint-palette upload test on a disposable WebGL2
 * canvas. No private GLB, vertex shader, drawing or production claim.
 */
import {probeOriginalFullBodyWebGL2} from './firstPartyOriginalWebGL2Capability.mjs';

export const ORIGINAL_PALETTE_TEXELS=268;
export function probeOriginalPaletteFloatUpload({makeCanvas}={}){
  if(typeof makeCanvas!=='function')
    throw new TypeError('A caller-owned fresh canvas factory is required');
  // The G4w check uses a separate disposable context; do not reuse its
  // voluntarily lost context for this actual allocation/upload probe.
  const baseline=probeOriginalFullBodyWebGL2({makeCanvas});
  if(!baseline.supported)
    return Object.freeze({ready:false,reason:baseline.reason,
      gpuUploadProved:false,originalHumanDrawProved:false});
  let gl,texture;
  try{
    const canvas=makeCanvas();
    gl=canvas?.getContext?.('webgl2',
      {alpha:false,depth:true,antialias:true});
    if(!gl)throw new Error('CONTEXT_UNAVAILABLE');
    texture=gl.createTexture();
    if(!texture)throw new Error('TEXTURE_ALLOCATION_UNAVAILABLE');
    gl.bindTexture(gl.TEXTURE_2D,texture);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    const palette=new Float32Array(ORIGINAL_PALETTE_TEXELS*4);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA32F,ORIGINAL_PALETTE_TEXELS,
      1,0,gl.RGBA,gl.FLOAT,palette);
    if(gl.getError()!==gl.NO_ERROR)
      return Object.freeze({ready:false,reason:'RGBA32F_PALETTE_UPLOAD_FAILED',
        gpuUploadProved:false,originalHumanDrawProved:false});
    return Object.freeze({ready:true,reason:'RGBA32F_PALETTE_UPLOAD_SUCCEEDED',
      gpuUploadProved:true,originalHumanDrawProved:false,
      productionReady:false,modelRead:false});
  }catch{
    return Object.freeze({ready:false,reason:'PALETTE_UPLOAD_PROBE_FAILED',
      gpuUploadProved:false,originalHumanDrawProved:false});
  }finally{
    try{if(texture)gl.deleteTexture(texture)}catch{}
    try{gl?.getExtension?.('WEBGL_lose_context')?.loseContext?.()}catch{}
  }
}
