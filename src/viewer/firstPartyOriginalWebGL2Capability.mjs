/**
 * G4w: read-only, original-private-asset-free WebGL2 device capability probe.
 * Only asks the browser for an isolated temporary context; never reads, uploads,
 * draws, or authenticates a private ORIGINAL_v1 model.
 * A successful probe is NOT a verified full-body GPU rendering result.
 */
export const HGPT_ORIGINAL_WEBGL2_PROBE_KIND=
  'hgpt-original-webgl2-device-capability-only-v1';
const requiredJointPaletteTexels=67*4;
const fail=message=>({supported:false,reason:message});
export function probeOriginalFullBodyWebGL2({
  makeCanvas,
}={}){
  if(typeof makeCanvas!=='function')
    throw new TypeError('Explicit local canvas factory required; no remote probing');
  let canvas;
  try {
    canvas=makeCanvas();
    if(!canvas||typeof canvas.getContext!=='function')
      return Object.freeze({...fail('NO_LOCAL_CANVAS'),
        kind:HGPT_ORIGINAL_WEBGL2_PROBE_KIND,modelDrawn:false});
    // Own ephemeral canvas, never disturb another live renderer/session.
    const gl=canvas.getContext('webgl2',
      {alpha:false,depth:true,antialias:true});
    if(!gl)
      return Object.freeze({...fail('WEBGL2_CONTEXT_UNAVAILABLE'),
        kind:HGPT_ORIGINAL_WEBGL2_PROBE_KIND,modelDrawn:false});
    try{
      const max=gl.getParameter(gl.MAX_TEXTURE_SIZE);
      const vertices=gl.getParameter(gl.MAX_VERTEX_ATTRIBS);
      if(!Number.isInteger(max)||max<requiredJointPaletteTexels)
        return Object.freeze({...fail('JOINT_PALETTE_TEXTURE_TOO_SMALL'),
          kind:HGPT_ORIGINAL_WEBGL2_PROBE_KIND,modelDrawn:false});
      // Five attributes in the native source vertex shader: POSITION,
      // JOINTS_0, WEIGHTS_0, UV0 padding and NORMAL.
      if(!Number.isInteger(vertices)||vertices<5)
        return Object.freeze({...fail('NATIVE_VERTEX_ATTRIBUTES_INSUFFICIENT'),
          kind:HGPT_ORIGINAL_WEBGL2_PROBE_KIND,modelDrawn:false});
      return Object.freeze({
        kind:HGPT_ORIGINAL_WEBGL2_PROBE_KIND,
        supported:true,reason:'BASIC_WEBGL2_CAPABILITIES_PRESENT',
        paletteTexelsRequired:requiredJointPaletteTexels,
        maxTextureSize:max,maxVertexAttribs:vertices,
        sourceModelSHA256Verified:false,originalGpuDrawVerified:false,
        modelDrawn:false,productionReady:false,
      });
    }finally{
      // The browser can choose not to support this extension; no new
      // dependencies, and no private GLB or live viewer is affected.
      gl.getExtension?.('WEBGL_lose_context')?.loseContext?.();
    }
  }catch{
    return Object.freeze({...fail('WEBGL2_PROBE_FAILED'),
      kind:HGPT_ORIGINAL_WEBGL2_PROBE_KIND,modelDrawn:false});
  }
}
