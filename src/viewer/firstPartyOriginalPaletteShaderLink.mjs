/**
 * G4z: isolated WebGL2 vertex texture sampler shader compile/link preflight.
 * This checks the actual GLSL capability class used for original joint palettes,
 * but does not render, bind, or load the private ORIGINAL_v1 human asset.
 */
export function probeOriginalPaletteShaderLink({makeCanvas}={}){
  if(typeof makeCanvas!=='function')throw new TypeError('Local canvas factory required');
  let gl=null,vert=null,frag=null,program=null;
  const result=(reason,linked=false)=>Object.freeze({
    linked,reason,originalHumanGpuDrawVerified:false,
    sourceModelSHA256Verified:false,productionReady:false
  });
  try{
    gl=makeCanvas()?.getContext?.('webgl2',{alpha:false,depth:true,antialias:true});
    if(!gl)return result('WEBGL2_UNAVAILABLE');
    const shader=(kind,body)=>{
      const s=gl.createShader(kind);
      if(!s)return null;
      gl.shaderSource(s,body);gl.compileShader(s);return s;
    };
    vert=shader(gl.VERTEX_SHADER,`#version 300 es
precision highp float;
precision highp sampler2D;
uniform highp sampler2D uJointPalette;
layout(location=0) in vec3 aPosition;
void main(){
  mat4 skin = mat4(
    texelFetch(uJointPalette,ivec2(0,0),0),
    texelFetch(uJointPalette,ivec2(1,0),0),
    texelFetch(uJointPalette,ivec2(2,0),0),
    texelFetch(uJointPalette,ivec2(3,0),0));
  gl_Position = skin * vec4(aPosition,1.0);
}`);
    frag=shader(gl.FRAGMENT_SHADER,`#version 300 es
precision mediump float;
out vec4 fragColor;
void main(){ fragColor=vec4(1.0); }`);
    if(!vert||!frag||!gl.getShaderParameter(vert,gl.COMPILE_STATUS)||
       !gl.getShaderParameter(frag,gl.COMPILE_STATUS))
      return result('PALETTE_SHADER_COMPILE_FAILED');
    program=gl.createProgram();
    if(!program)return result('PALETTE_PROGRAM_UNAVAILABLE');
    gl.attachShader(program,vert);gl.attachShader(program,frag);
    gl.linkProgram(program);
    if(!gl.getProgramParameter(program,gl.LINK_STATUS)||
       gl.getError()!==gl.NO_ERROR)
      return result('PALETTE_SHADER_LINK_FAILED');
    return result('PALETTE_SHADER_LINK_SUCCEEDED',true);
  }catch{return result('PALETTE_SHADER_PROBE_FAILED')}
  finally{
    try{if(program)gl.deleteProgram(program)}catch{}
    try{if(vert)gl.deleteShader(vert)}catch{}
    try{if(frag)gl.deleteShader(frag)}catch{}
    try{gl?.getExtension?.('WEBGL_lose_context')?.loseContext?.()}catch{}
  }
}
