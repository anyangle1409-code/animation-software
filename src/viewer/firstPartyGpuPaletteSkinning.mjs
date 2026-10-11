/**
 * Home Gym PT G2 — actual first-party WebGL2 4-influence vertex-skinning.
 *
 * Texture-packed RGBA32F affine matrices (4 texels per column-major mat4)
 * avoid platform-dependent vertex-uniform array bone ceilings. The CPU
 * computes ONE joint-palette mat4 per bone, NOT a pose per vertex.
 *
 * Diagnostic UV0 fragment only: no original human mesh or real skin normal /
 * PBR shading, texture asset fetch, Third/React modules or anatomical claims.
 */
import {nativeLookAt,nativePerspective,multiplyNativeMat4}
  from './firstPartyWebGL2SkeletonPreview.mjs';
import {validateNativeSkinnedMesh} from './firstPartyIndexedSkinnedMesh.mjs';
export const HGPT_NATIVE_GPU_SKIN_KIND='hgpt-native-webgl2-rgba32f-4weight-gpu-lbs-v1';
const finite=values=>{if(!Array.from(values).every(Number.isFinite))
  throw new RangeError('GPU palette nonfinite input');};
function rigid(matrix){
  if(matrix.length!==16)throw new RangeError('GPU palette requires 16-number joint transform');
  finite(matrix);
  if(Math.abs(matrix[3])+Math.abs(matrix[7])+Math.abs(matrix[11])+
     Math.abs(matrix[15]-1)>1e-4)
    throw new RangeError('GPU palette pose must be affine');
  const axes=[[matrix[0],matrix[1],matrix[2]],
    [matrix[4],matrix[5],matrix[6]],
    [matrix[8],matrix[9],matrix[10]]];
  for(let i=0;i<3;i++){
    if(Math.abs(Math.hypot(...axes[i])-1)>1e-3)
      throw new RangeError('GPU palette pose scaling unsupported');
    for(let j=0;j<i;j++){
      const dot=axes[i].reduce((s,x,k)=>s+x*axes[j][k],0);
      if(Math.abs(dot)>1e-3)throw new RangeError('GPU palette pose shear unsupported');
    }
  }
  const [x,y,z]=axes;
  const det=x[0]*(y[1]*z[2]-y[2]*z[1])
    -x[1]*(y[0]*z[2]-y[2]*z[0])
    +x[2]*(y[0]*z[1]-y[1]*z[0]);
  if(Math.abs(det-1)>2e-3)throw new RangeError('GPU palette pose reflection unsupported');
}
export function buildNativeJointSkinPalette(mesh,posedWorld){
  const validated=validateNativeSkinnedMesh(mesh);
  if(!(posedWorld instanceof Float32Array)||
    posedWorld.length!==validated.bones*16)
    throw new RangeError('GPU palette requires complete Float32Array joint world matrices');
  const packed=new Float32Array(posedWorld.length);
  for(let i=0;i<validated.bones;i++){
    const world=posedWorld.subarray(i*16,i*16+16);
    rigid(world);
    const bind=mesh.inverseBindMatrices.subarray(i*16,i*16+16);
    const transform=multiplyNativeMat4(world,bind);
    finite(transform);
    packed.set(transform,i*16);
  }
  return packed;
}
function checkedPart(part){
  if(!part || typeof part!=='object' || !part.mesh)
    throw new RangeError('GPU mesh + pose + UV0 needed');
  const shape=validateNativeSkinnedMesh(part.mesh);
  if(!(part.uv0 instanceof Float32Array)||
    part.uv0.length!==shape.vertices*2)
    throw new RangeError('GPU UV0 vertex count mismatch');
  finite(part.uv0);
  for(const uv of part.uv0)if(Math.abs(uv)>1024)
    throw new RangeError('GPU UV0 coordinate magnitude exceeded');
  return {shape,palette:buildNativeJointSkinPalette(part.mesh,part.posedWorld)};
}
function shader(gl,type,src){
  const item=gl.createShader(type);
  if(!item)throw new Error('GPU skin shader unavailable');
  gl.shaderSource(item,src);gl.compileShader(item);
  if(!gl.getShaderParameter(item,gl.COMPILE_STATUS)){
    const error=gl.getShaderInfoLog(item)||'unknown';
    gl.deleteShader(item);throw new Error('Native GPU skin shader compile: '+error);
  }
  return item;
}
function compiledProgram(gl){
  const vert=shader(gl,gl.VERTEX_SHADER,
    '#version 300 es\nprecision highp float;\nprecision highp sampler2D;\nlayout(location=0) in vec3 aPos;\nlayout(location=1) in uvec4 aJoints;\nlayout(location=2) in vec4 aWeights;\nlayout(location=3) in vec2 aUV0;\nuniform mat4 uVP;\nuniform sampler2D uMatrixPalette;\nout vec2 vUV0;\nout vec3 vSkinnedWorld;\nmat4 bone(uint j){int x=int(j)*4;return mat4(texelFetch(uMatrixPalette,ivec2(x+0,0),0),texelFetch(uMatrixPalette,ivec2(x+1,0),0),texelFetch(uMatrixPalette,ivec2(x+2,0),0),texelFetch(uMatrixPalette,ivec2(x+3,0),0));}\nvoid main(){vec4 p=vec4(0.0);vec4 rest=vec4(aPos,1.0);p+=(bone(aJoints.x)*rest)*aWeights.x;p+=(bone(aJoints.y)*rest)*aWeights.y;p+=(bone(aJoints.z)*rest)*aWeights.z;p+=(bone(aJoints.w)*rest)*aWeights.w;vSkinnedWorld=p.xyz;vUV0=aUV0;gl_Position=uVP*p;}');
  const frag=shader(gl,gl.FRAGMENT_SHADER,
    '#version 300 es\nprecision highp float;\nin vec2 vUV0;\nout vec4 outColor;\nvoid main(){outColor=vec4(clamp(vUV0,vec2(0.0),vec2(1.0)),0.14,1.0);}');
  const p=gl.createProgram();
  if(!p){gl.deleteShader(vert);gl.deleteShader(frag);
    throw new Error('Native GPU skin link program unavailable');}
  gl.attachShader(p,vert);gl.attachShader(p,frag);
  // GPU parity probe captures the EXACT vertex-skinned position from shader.
  gl.transformFeedbackVaryings(p,['vSkinnedWorld'],gl.SEPARATE_ATTRIBS);
  gl.linkProgram(p);
  gl.deleteShader(vert);gl.deleteShader(frag);
  if(!gl.getProgramParameter(p,gl.LINK_STATUS)){
    const error=gl.getProgramInfoLog(p)||'unknown';
    gl.deleteProgram(p);throw new Error('Native GPU skin shader link: '+error);
  }
  return p;
}
export function createNativePaletteSkinnedWebGL2(canvas){
  const gl=canvas.getContext('webgl2',{alpha:false,depth:true,antialias:true});
  if(!gl)throw new Error('Native GPU joint palette requires WebGL2, no vendor fallback');
  let prog=null,vao=null,rest=null,joints=null,weights=null,uvBuffer=null,
    indices=null,paletteTexture=null,viewLoc=null,samplerLoc=null;
  let width=1,height=1,lost=false,disposed=false,frames=0,draws=0,captures=0;
  const setup=()=>{
    prog=compiledProgram(gl);
    vao=gl.createVertexArray();
    rest=gl.createBuffer();joints=gl.createBuffer();weights=gl.createBuffer();
    uvBuffer=gl.createBuffer();indices=gl.createBuffer();
    paletteTexture=gl.createTexture();
    if(!vao||!rest||!joints||!weights||!uvBuffer||!indices||!paletteTexture)
      throw new Error('Native GPU skin vertex buffers or palette texture unavailable');
    viewLoc=gl.getUniformLocation(prog,'uVP');
    samplerLoc=gl.getUniformLocation(prog,'uMatrixPalette');
    if(viewLoc===null||samplerLoc===null)throw new Error('Native GPU skin uniform missing');
    gl.bindVertexArray(vao);
    for(const [idx,buffer,items,isInt] of [
      [0,rest,3,false],[1,joints,4,true],[2,weights,4,false],
      [3,uvBuffer,2,false]
    ]){
      gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
      gl.enableVertexAttribArray(idx);
      if(isInt)gl.vertexAttribIPointer(idx,items,gl.UNSIGNED_SHORT,0,0);
      else gl.vertexAttribPointer(idx,items,gl.FLOAT,false,0,0);
    }
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,indices);
    gl.bindVertexArray(null);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D,paletteTexture);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    gl.enable(gl.DEPTH_TEST);
  };
  const onLost=e=>{e.preventDefault();lost=true;};
  const onRestored=()=>{if(disposed)return;lost=false;setup();gl.viewport(0,0,width,height);};
  canvas.addEventListener('webglcontextlost',onLost);
  canvas.addEventListener('webglcontextrestored',onRestored);
  try{setup();}catch(e){
    canvas.removeEventListener('webglcontextlost',onLost);
    canvas.removeEventListener('webglcontextrestored',onRestored);
    throw e;
  }
  const upload=(part,palette)=>{
    const m=part.mesh;
    gl.bindVertexArray(vao);
    for(const [buffer,data,target] of [
      [rest,m.positions,gl.ARRAY_BUFFER],
      [joints,m.jointIndices,gl.ARRAY_BUFFER],
      [weights,m.weights,gl.ARRAY_BUFFER],
      [uvBuffer,part.uv0,gl.ARRAY_BUFFER],
      [indices,m.indices,gl.ELEMENT_ARRAY_BUFFER],
    ]){
      gl.bindBuffer(target,buffer);gl.bufferData(target,data,gl.DYNAMIC_DRAW);
    }
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D,paletteTexture);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA32F,palette.length/4,1,0,
      gl.RGBA,gl.FLOAT,palette);
    gl.uniform1i(samplerLoc,0);
  };
  const setVP=(eye,target)=>{
    finite([...eye,...target]);
    const vp=multiplyNativeMat4(
      nativePerspective(38*Math.PI/180,width/height,.05,100),
      nativeLookAt(eye,target));
    gl.useProgram(prog);
    gl.uniformMatrix4fv(viewLoc,false,vp);
  };
  const type=m=>m.indices instanceof Uint32Array?gl.UNSIGNED_INT:gl.UNSIGNED_SHORT;
  return {
    get kind(){return HGPT_NATIVE_GPU_SKIN_KIND;},
    get frameCount(){return frames;},
    get drawCallCount(){return draws;},
    get capturedTriangleCount(){return captures;},
    get contextLost(){return lost;},
    setSize(w,h,dpr=1){
      if(disposed)throw new Error('GPU palette renderer disposed');
      finite([w,h,dpr]);
      if(w<=0||h<=0||dpr<=0)throw new RangeError('GPU palette viewport invalid');
      width=Math.max(1,Math.floor(w*dpr));height=Math.max(1,Math.floor(h*dpr));
      canvas.width=width;canvas.height=height;
      if(!lost)gl.viewport(0,0,width,height);
    },
    renderBatches(parts,{eye=[1,0.5,6.2],target=[1.25,.5,0]}={}){
      if(disposed)throw new Error('GPU palette renderer disposed');
      if(lost)return false;
      if(!Array.isArray(parts)||parts.length<1||parts.length>8)
        throw new RangeError('GPU skin batch requires 1..8 parts');
      // Validate all meshes + palettes before any GPU call, fail closed.
      const prepared=parts.map(checkedPart);
      let total=0;
      for(const {shape} of prepared){
        total+=shape.vertices;
        if(total>250000)throw new RangeError('GPU skin aggregate vertex limit');
        if(shape.bones*4>gl.getParameter(gl.MAX_TEXTURE_SIZE))
          throw new RangeError('GPU matrix palette texture exceeds native GPU limit');
      }
      finite([...eye,...target]);
      gl.viewport(0,0,width,height);gl.clearColor(.04,.05,.08,1);
      gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      setVP(eye,target);
      for(let i=0;i<parts.length;i++){
        upload(parts[i],prepared[i].palette);
        gl.drawElements(gl.TRIANGLES,parts[i].mesh.indices.length,
          type(parts[i].mesh),0);
        draws++;
      }
      gl.bindVertexArray(null);
      frames++;return true;
    },
    /**
     * GPU transform-feedback readback for formal parity testing only.
     * Captures each indexed primitive's actual vertex shader output in
     * triangle order. No CPU per-vertex skinning, no guessed shader results.
     */
    captureIndexedSkinnedPositions(part){
      if(disposed||lost)throw new Error('GPU capture renderer unavailable');
      const {shape,palette}=checkedPart(part);
      const count=part.mesh.indices.length;
      if(count>8192)throw new RangeError('GPU diagnostic capture limited to 8192 triangle indices');
      if(shape.bones*4>gl.getParameter(gl.MAX_TEXTURE_SIZE))
        throw new RangeError('GPU palette texture size unsupported');
      const buffer=gl.createBuffer();
      if(!buffer)throw new Error('GPU transform feedback buffer unavailable');
      const actual=new Float32Array(count*3);
      // Transform-feedback test only: expand original indexed vertices into
      // source triangle order. Actual RENDERING always remains indexed GPU
      // drawElements; verification uses legal drawArrays TRIANGLES because
      // indexed draws during active transform feedback can be rejected by
      // WebGL2 implementations. Expansion does NOT skin vertices on CPU.
      const expand=(input,width)=>{
        const out=new input.constructor(count*width);
        for(let i=0;i<count;i++){
          const source=part.mesh.indices[i]*width;
          out.set(input.subarray(source,source+width),i*width);
        }
        return out;
      };
      try{
        setVP([0,0,4],[0,0,0]);
        upload(part,palette);
        for(const [gpuBuffer,expanded] of [
          [rest,expand(part.mesh.positions,3)],
          [joints,expand(part.mesh.jointIndices,4)],
          [weights,expand(part.mesh.weights,4)],
          [uvBuffer,expand(part.uv0,2)],
        ]){
          gl.bindBuffer(gl.ARRAY_BUFFER,gpuBuffer);
          gl.bufferData(gl.ARRAY_BUFFER,expanded,gl.DYNAMIC_DRAW);
        }
        gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER,buffer);
        gl.bufferData(gl.TRANSFORM_FEEDBACK_BUFFER,actual.byteLength,gl.STREAM_READ);
        gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER,0,buffer);
        if(gl.getError()!==gl.NO_ERROR)
          throw new Error('GPU transform feedback setup produced WebGL error');
        gl.enable(gl.RASTERIZER_DISCARD);
        gl.beginTransformFeedback(gl.TRIANGLES);
        gl.drawArrays(gl.TRIANGLES,0,count);
        gl.endTransformFeedback();
        gl.disable(gl.RASTERIZER_DISCARD);
        const drawError=gl.getError();
        if(drawError!==gl.NO_ERROR)
          throw new Error('GPU triangle transform feedback draw failed with GL error '+drawError);
        gl.getBufferSubData(gl.TRANSFORM_FEEDBACK_BUFFER,0,actual);
        const readError=gl.getError();
        if(readError!==gl.NO_ERROR)
          throw new Error('GPU captured vertex readback failed with GL error '+readError);
        finite(actual);
        captures+=count/3;
      }finally{
        gl.disable(gl.RASTERIZER_DISCARD);
        gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER,0,null);
        gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER,null);
        gl.bindVertexArray(null);
        gl.deleteBuffer(buffer);
      }
      return actual;
    },
    dispose(){
      if(disposed)return;disposed=true;
      canvas.removeEventListener('webglcontextlost',onLost);
      canvas.removeEventListener('webglcontextrestored',onRestored);
      if(!lost){
        for(const b of [rest,joints,weights,uvBuffer,indices])gl.deleteBuffer(b);
        gl.deleteVertexArray(vao);gl.deleteTexture(paletteTexture);gl.deleteProgram(prog);
      }
    }
  };
}
