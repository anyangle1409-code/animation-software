/**
 * Native first-party WebGL2 UV0 diagnostic interpolation shader.
 * This verifies source GLB TEXCOORD_0 reaches the actual GPU fragment, not
 * texture loading, real image assets, human skin or production PBR shading.
 * No third-party libraries or runtime imports.
 */
import {nativeLookAt,nativePerspective,multiplyNativeMat4}
  from './firstPartyWebGL2SkeletonPreview.mjs';
export const HGPT_UV0_GPU_KIND='hgpt-native-webgl2-uv0-diagnostic-v1';
const finite=a=>{if(!Array.from(a).every(Number.isFinite))
  throw new RangeError('Native UV0 WebGL2 nonfinite values');};
const shader=(gl,type,source)=>{
  const sh=gl.createShader(type);
  if(!sh)throw new Error('UV0 GPU shader unavailable');
  gl.shaderSource(sh,source);gl.compileShader(sh);
  if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS)){
    const err=gl.getShaderInfoLog(sh)||'unknown shader error';
    gl.deleteShader(sh);throw new Error('UV0 GPU shader compile failure: '+err);
  }
  return sh;
};
function program(gl){
  const vs=shader(gl,gl.VERTEX_SHADER,
    '#version 300 es\nprecision highp float;\nlayout(location=0) in vec3 aPosition;\nlayout(location=1) in vec2 aUV0;\nuniform mat4 uVP;\nout vec2 vUV0;\nvoid main(){gl_Position=uVP*vec4(aPosition,1.0);vUV0=aUV0;}');
  const fs=shader(gl,gl.FRAGMENT_SHADER,
    '#version 300 es\nprecision highp float;\nin vec2 vUV0;\nout vec4 outColor;\nvoid main(){outColor=vec4(clamp(vUV0,vec2(0.0),vec2(1.0)),0.14,1.0);}');
  const p=gl.createProgram();
  if(!p){gl.deleteShader(vs);gl.deleteShader(fs);throw new Error('UV0 program unavailable');}
  gl.attachShader(p,vs);gl.attachShader(p,fs);gl.linkProgram(p);
  gl.deleteShader(vs);gl.deleteShader(fs);
  if(!gl.getProgramParameter(p,gl.LINK_STATUS)){
    const why=gl.getProgramInfoLog(p)||'unknown linker error';
    gl.deleteProgram(p);throw new Error('UV0 program link failure: '+why);
  }
  return p;
}
function validatePart(part){
  if(!part || !(part.positions instanceof Float32Array) ||
      !(part.uv0 instanceof Float32Array) ||
      !(part.indices instanceof Uint16Array || part.indices instanceof Uint32Array) ||
      part.positions.length<9||part.positions.length%3||
      part.uv0.length!==part.positions.length/3*2||
      part.indices.length<3||part.indices.length%3)
    throw new RangeError('UV0 posed part requires typed POSITION, TEXCOORD_0, indexed TRIANGLES');
  finite(part.positions);finite(part.uv0);
  for(const u of part.uv0)if(Math.abs(u)>1024)
    throw new RangeError('UV0 exceeded diagnostic source coordinate bounds');
  for(const i of part.indices)if(i>=part.positions.length/3)
    throw new RangeError('UV0 indexed triangle exceeds vertex buffer');
}
export function createNativeUV0WebGL2(canvas){
  const gl=canvas.getContext('webgl2',{alpha:false,depth:true,antialias:true});
  if(!gl)throw new Error('Native UV0 requires WebGL2; third-party fallback forbidden');
  let prog=null,vao=null,positionBuffer=null,uvBuffer=null,elemBuffer=null,uVP=null;
  let frames=0,draws=0,w=1,h=1,disposed=false,lost=false;
  const prepare=()=>{
    prog=program(gl);
    vao=gl.createVertexArray();
    positionBuffer=gl.createBuffer();uvBuffer=gl.createBuffer();elemBuffer=gl.createBuffer();
    if(!vao||!positionBuffer||!uvBuffer||!elemBuffer)
      throw new Error('Native UV0 GPU buffers unavailable');
    uVP=gl.getUniformLocation(prog,'uVP');
    if(uVP===null)throw new Error('Native UV0 view uniform missing');
    gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER,positionBuffer);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0,3,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ARRAY_BUFFER,uvBuffer);
    gl.enableVertexAttribArray(1);
    gl.vertexAttribPointer(1,2,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,elemBuffer);
    gl.bindVertexArray(null);gl.enable(gl.DEPTH_TEST);
  };
  const onLost=e=>{e.preventDefault();lost=true;};
  const onRestored=()=>{if(disposed)return;lost=false;prepare();gl.viewport(0,0,w,h);};
  canvas.addEventListener('webglcontextlost',onLost);
  canvas.addEventListener('webglcontextrestored',onRestored);
  try{prepare();}catch(e){
    canvas.removeEventListener('webglcontextlost',onLost);
    canvas.removeEventListener('webglcontextrestored',onRestored);
    throw e;
  }
  return {
    get kind(){return HGPT_UV0_GPU_KIND;},
    get frameCount(){return frames;},
    get drawCallCount(){return draws;},
    get contextLost(){return lost;},
    setSize(width,height,dpr=1){
      if(disposed)throw new Error('UV0 renderer disposed');
      finite([width,height,dpr]);
      if(width<=0||height<=0||dpr<=0)throw new RangeError('UV0 viewport dimensions invalid');
      w=Math.max(1,Math.floor(width*dpr));h=Math.max(1,Math.floor(height*dpr));
      canvas.width=w;canvas.height=h;
      if(!lost)gl.viewport(0,0,w,h);
    },
    renderBatches(parts,{eye=[1,0.5,6.2],target=[1.25,.5,0]}={}){
      if(disposed)throw new Error('UV0 renderer disposed');
      if(lost)return false;
      if(!Array.isArray(parts)||parts.length<1||parts.length>8)
        throw new RangeError('Native UV0 batch requires 1..8 original mesh parts');
      let vertices=0;
      for(const part of parts){
        validatePart(part);
        vertices+=part.positions.length/3;
        if(vertices>250000)throw new RangeError('Native UV0 batch vertex limit exceeded');
      }
      finite([...eye,...target]);
      const vp=multiplyNativeMat4(
        nativePerspective(38*Math.PI/180,w/h,.05,100),nativeLookAt(eye,target));
      // Atomic source-check before GPU clear/draw; single shared depth frame.
      gl.viewport(0,0,w,h);
      gl.clearColor(.04,.05,.08,1);
      gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      gl.useProgram(prog);gl.uniformMatrix4fv(uVP,false,vp);
      gl.bindVertexArray(vao);
      for(const part of parts){
        gl.bindBuffer(gl.ARRAY_BUFFER,positionBuffer);
        gl.bufferData(gl.ARRAY_BUFFER,part.positions,gl.DYNAMIC_DRAW);
        gl.bindBuffer(gl.ARRAY_BUFFER,uvBuffer);
        gl.bufferData(gl.ARRAY_BUFFER,part.uv0,gl.DYNAMIC_DRAW);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,elemBuffer);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,part.indices,gl.DYNAMIC_DRAW);
        gl.drawElements(gl.TRIANGLES,part.indices.length,
          part.indices instanceof Uint32Array?gl.UNSIGNED_INT:gl.UNSIGNED_SHORT,0);
        draws++;
      }
      gl.bindVertexArray(null);frames++;return true;
    },
    dispose(){
      if(disposed)return;disposed=true;
      canvas.removeEventListener('webglcontextlost',onLost);
      canvas.removeEventListener('webglcontextrestored',onRestored);
      if(!lost){
        gl.deleteBuffer(positionBuffer);gl.deleteBuffer(uvBuffer);gl.deleteBuffer(elemBuffer);
        gl.deleteVertexArray(vao);gl.deleteProgram(prog);
      }
    },
  };
}
