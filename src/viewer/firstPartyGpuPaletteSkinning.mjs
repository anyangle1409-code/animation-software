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
import {HGPT_EMBEDDED_PNG_KIND} from './firstPartyEmbeddedPngSource.mjs';
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
function checkedPart(part,requireSourceNormals=false){
  if(!part || typeof part!=='object' || !part.mesh)
    throw new RangeError('GPU mesh + pose + UV0 needed');
  const shape=validateNativeSkinnedMesh(part.mesh);
  if(!(part.uv0 instanceof Float32Array)||
    part.uv0.length!==shape.vertices*2)
    throw new RangeError('GPU UV0 vertex count mismatch');
  finite(part.uv0);
  for(const uv of part.uv0)if(Math.abs(uv)>1024)
    throw new RangeError('GPU UV0 coordinate magnitude exceeded');
  if(requireSourceNormals && !(part.sourceNormals instanceof Float32Array))
    throw new RangeError('GPU normal-preview requires explicit original source NORMAL');
  if(part.sourceNormals!==undefined){
    if(!(part.sourceNormals instanceof Float32Array)||
      part.sourceNormals.length!==shape.vertices*3)
      throw new RangeError('GPU source NORMAL typed vertex count mismatch');
    for(let k=0;k<part.sourceNormals.length;k+=3){
      const len=Math.hypot(part.sourceNormals[k],part.sourceNormals[k+1],
        part.sourceNormals[k+2]);
      if(!Number.isFinite(len)||len<.998||len>1.002)
        throw new RangeError('GPU source NORMAL must be finite and near unit length');
    }
  }
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
    '#version 300 es\nprecision highp float;\nprecision highp sampler2D;\nlayout(location=0) in vec3 aPos;\nlayout(location=1) in uvec4 aJoints;\nlayout(location=2) in vec4 aWeights;\nlayout(location=3) in vec2 aUV0;\nlayout(location=4) in vec3 aNormal;\nuniform mat4 uVP;\nuniform sampler2D uMatrixPalette;\nout vec2 vUV0;\nout vec3 vSkinnedWorld;\nout vec3 vSkinnedNormal;\nmat4 bone(uint j){int x=int(j)*4;return mat4(texelFetch(uMatrixPalette,ivec2(x+0,0),0),texelFetch(uMatrixPalette,ivec2(x+1,0),0),texelFetch(uMatrixPalette,ivec2(x+2,0),0),texelFetch(uMatrixPalette,ivec2(x+3,0),0));}\nvoid main(){vec4 p=vec4(0.0);vec4 rest=vec4(aPos,1.0);p+=(bone(aJoints.x)*rest)*aWeights.x;p+=(bone(aJoints.y)*rest)*aWeights.y;p+=(bone(aJoints.z)*rest)*aWeights.z;p+=(bone(aJoints.w)*rest)*aWeights.w;vec3 n=vec3(0.0);n+=(mat3(bone(aJoints.x))*aNormal)*aWeights.x;n+=(mat3(bone(aJoints.y))*aNormal)*aWeights.y;n+=(mat3(bone(aJoints.z))*aNormal)*aWeights.z;n+=(mat3(bone(aJoints.w))*aNormal)*aWeights.w;vSkinnedWorld=p.xyz;vSkinnedNormal=normalize(n);vUV0=aUV0;gl_Position=uVP*p;}');
  const frag=shader(gl,gl.FRAGMENT_SHADER,
    '#version 300 es\nprecision highp float;\nin vec2 vUV0;\nin vec3 vSkinnedNormal;\nuniform int uNormalPreview;\nuniform int uTexturePreview;\nuniform sampler2D uSourceColor;\nuniform vec3 uSourceTint;\nuniform int uColorManaged;\nout vec4 outColor;\nvec3 toSRGB(vec3 v){vec3 c=clamp(v,vec3(0.0),vec3(1.0));vec3 a=12.92*c;vec3 b=1.055*pow(c,vec3(1.0/2.4))-0.055;return mix(b,a,lessThanEqual(c,vec3(0.0031308)));}\nvoid main(){if(uNormalPreview==1){float diffuse=max(dot(normalize(vSkinnedNormal),normalize(vec3(0.32,0.50,0.81))),0.0);outColor=vec4(vec3(0.12+0.78*diffuse),1.0);}else if(uTexturePreview==1){vec3 linearOrEncoded=texture(uSourceColor,vUV0).rgb*uSourceTint;outColor=vec4(uColorManaged==1?toSRGB(linearOrEncoded):linearOrEncoded,1.0);}else{outColor=vec4(clamp(vUV0,vec2(0.0),vec2(1.0)),0.14,1.0);}}');
  const p=gl.createProgram();
  if(!p){gl.deleteShader(vert);gl.deleteShader(frag);
    throw new Error('Native GPU skin link program unavailable');}
  gl.attachShader(p,vert);gl.attachShader(p,frag);
  // GPU parity probe captures the EXACT vertex-skinned position from shader.
  gl.transformFeedbackVaryings(p,['vSkinnedWorld','vSkinnedNormal'],gl.SEPARATE_ATTRIBS);
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
    normalBuffer=null,indices=null,paletteTexture=null,viewLoc=null,
    samplerLoc=null,normalPreviewLoc=null,texturePreviewLoc=null,
    sourceColorLoc=null,sourceTintLoc=null,colorManagedLoc=null;
  let width=1,height=1,lost=false,disposed=false,frames=0,draws=0,captures=0;
  // Opt-in project-owned PNG source preview bound to exact GLB mesh/UV
  // objects. Only source bytes are decoded; animated world matrices remain
  // supplied explicitly by the separate rig/pose handoff (PRs #59/#60).
  let sourcePngParts=[],sourceTextures=[],sourcePngColorSpace=null;
  const setup=()=>{
    prog=compiledProgram(gl);
    vao=gl.createVertexArray();
    rest=gl.createBuffer();joints=gl.createBuffer();weights=gl.createBuffer();
    uvBuffer=gl.createBuffer();normalBuffer=gl.createBuffer();
    indices=gl.createBuffer();
    paletteTexture=gl.createTexture();
    if(!vao||!rest||!joints||!weights||!uvBuffer||!normalBuffer||!indices||!paletteTexture)
      throw new Error('Native GPU skin vertex buffers or palette texture unavailable');
    viewLoc=gl.getUniformLocation(prog,'uVP');
    samplerLoc=gl.getUniformLocation(prog,'uMatrixPalette');
    normalPreviewLoc=gl.getUniformLocation(prog,'uNormalPreview');
    texturePreviewLoc=gl.getUniformLocation(prog,'uTexturePreview');
    sourceColorLoc=gl.getUniformLocation(prog,'uSourceColor');
    sourceTintLoc=gl.getUniformLocation(prog,'uSourceTint');
    colorManagedLoc=gl.getUniformLocation(prog,'uColorManaged');
    if(viewLoc===null||samplerLoc===null||normalPreviewLoc===null||
      texturePreviewLoc===null||sourceColorLoc===null||sourceTintLoc===null||
      colorManagedLoc===null)
      throw new Error('Native GPU skin/PNG shader uniform missing');
    gl.bindVertexArray(vao);
    for(const [idx,buffer,items,isInt] of [
      [0,rest,3,false],[1,joints,4,true],[2,weights,4,false],
      [3,uvBuffer,2,false],[4,normalBuffer,3,false]
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
  const discardSourcePng=()=>{
    if(!lost)for(const tex of sourceTextures)gl.deleteTexture(tex);
    sourceTextures=[];sourcePngParts=[];sourcePngColorSpace=null;
  };
  const onLost=e=>{e.preventDefault();lost=true;sourceTextures=[];sourcePngParts=[];sourcePngColorSpace=null;};
  const onRestored=()=>{if(disposed)return;lost=false;setup();gl.viewport(0,0,width,height);};
  canvas.addEventListener('webglcontextlost',onLost);
  canvas.addEventListener('webglcontextrestored',onRestored);
  try{setup();}catch(e){
    canvas.removeEventListener('webglcontextlost',onLost);
    canvas.removeEventListener('webglcontextrestored',onRestored);
    throw e;
  }
  // Project-owned placeholder for legacy unlit G2 display only. In
  // diagnostic normalPreview mode original source NORMAL is REQUIRED.
  const incomingNormals=part=>{
    if(part.sourceNormals!==undefined)return part.sourceNormals;
    const count=part.mesh.positions.length/3;
    const placeholder=new Float32Array(count*3);
    for(let i=0;i<count;i++)placeholder[i*3+2]=1;
    return placeholder;
  };
  const upload=(part,palette)=>{
    const m=part.mesh;
    gl.bindVertexArray(vao);
    for(const [buffer,data,target] of [
      [rest,m.positions,gl.ARRAY_BUFFER],
      [joints,m.jointIndices,gl.ARRAY_BUFFER],
      [weights,m.weights,gl.ARRAY_BUFFER],
      [uvBuffer,part.uv0,gl.ARRAY_BUFFER],
      [normalBuffer,incomingNormals(part),gl.ARRAY_BUFFER],
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
  const captureStreams=(part,requireNormals)=>{
    if(disposed||lost)throw new Error('GPU capture renderer unavailable');
    const {shape,palette}=checkedPart(part,requireNormals);
    const count=part.mesh.indices.length;
    if(count>8192)throw new RangeError('GPU diagnostic capture limited to 8192 indices');
    if(shape.bones*4>gl.getParameter(gl.MAX_TEXTURE_SIZE))
      throw new RangeError('GPU palette texture size unsupported');
    const posOut=gl.createBuffer(),normOut=gl.createBuffer();
    if(!posOut||!normOut)throw new Error('GPU transform feedback buffers unavailable');
    const positions=new Float32Array(count*3);
    const normals=new Float32Array(count*3);
    // Transform feedback only: use drawArrays with deindexed SOURCE attributes
    // to satisfy WebGL2 restrictions. Indexed production drawElements unchanged.
    // This copies source REST inputs, never skins vertices on CPU.
    const expand=(input,width)=>{
      const result=new input.constructor(count*width);
      for(let i=0;i<count;i++)
        result.set(input.subarray(part.mesh.indices[i]*width,
          part.mesh.indices[i]*width+width),i*width);
      return result;
    };
    try{
      setVP([0,0,4],[0,0,0]);
      gl.uniform1i(normalPreviewLoc,0);
      upload(part,palette);
      for(const [buffer,expanded] of [
        [rest,expand(part.mesh.positions,3)],
        [joints,expand(part.mesh.jointIndices,4)],
        [weights,expand(part.mesh.weights,4)],
        [uvBuffer,expand(part.uv0,2)],
        [normalBuffer,expand(incomingNormals(part),3)]
      ]){
        gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
        gl.bufferData(gl.ARRAY_BUFFER,expanded,gl.DYNAMIC_DRAW);
      }
      for(const [slot,buffer,values] of [[0,posOut,positions],[1,normOut,normals]]){
        gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER,buffer);
        gl.bufferData(gl.TRANSFORM_FEEDBACK_BUFFER,values.byteLength,gl.STREAM_READ);
        gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER,slot,buffer);
      }
      if(gl.getError()!==gl.NO_ERROR)
        throw new Error('GPU normal transform feedback setup produced WebGL error');
      gl.enable(gl.RASTERIZER_DISCARD);
      gl.beginTransformFeedback(gl.TRIANGLES);
      gl.drawArrays(gl.TRIANGLES,0,count);
      gl.endTransformFeedback();
      gl.disable(gl.RASTERIZER_DISCARD);
      if(gl.getError()!==gl.NO_ERROR)
        throw new Error('GPU normal transform feedback produced WebGL error');
      for(const [buffer,destination] of [[posOut,positions],[normOut,normals]]){
        gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER,buffer);
        gl.getBufferSubData(gl.TRANSFORM_FEEDBACK_BUFFER,0,destination);
      }
      if(gl.getError()!==gl.NO_ERROR)
        throw new Error('GPU normal capture getBufferSubData failed');
      finite(positions);finite(normals);
      captures+=count/3;
    }finally{
      gl.disable(gl.RASTERIZER_DISCARD);
      gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER,0,null);
      gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER,1,null);
      gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER,null);
      gl.bindVertexArray(null);
      gl.deleteBuffer(posOut);gl.deleteBuffer(normOut);
    }
    return {positions,normals};
  };
  return {
    get kind(){return HGPT_NATIVE_GPU_SKIN_KIND;},
    get frameCount(){return frames;},
    get drawCallCount(){return draws;},
    get capturedTriangleCount(){return captures;},
    get contextLost(){return lost;},
    /**
     * Prepare material PNG textures strictly from G1e-validated source GLB
     * parts; caller must later render the EXACT source mesh/UV references.
     * Local browser decoding and GPU upload only. No URL or Three.js.
     */
    async setSourcePngBatches(originalParts,{colorSpace='legacy-rgba8'}={}){
      if(!['legacy-rgba8','gltf-srgb'].includes(colorSpace))
        throw new RangeError('GLB baseColor source colour space must be explicit supported mode');
      if(disposed||lost)throw new Error('GPU texture/skin context unavailable');
      if(!Array.isArray(originalParts)||originalParts.length<1||
         originalParts.length>8)
        throw new RangeError('GPU source PNG expects 1..8 exact GLB parts');
      const parts=originalParts.map(p=>{
        const source=p?.sourceBaseColorPng;
        if(!p?.parsed?.mesh || !(p.sourceUV0 instanceof Float32Array) ||
           !source || source.kind!==HGPT_EMBEDDED_PNG_KIND ||
           !(source.bytes instanceof Uint8Array) ||
           source.bytes.length<57 || source.bytes.length>8*1024*1024 ||
           !Number.isSafeInteger(source.width)||!Number.isSafeInteger(source.height)||
           source.width<=0||source.height<=0||
           source.width*source.height>4194304||
           source.sampler?.minFilter!==9729||source.sampler.magFilter!==9729||
           source.sampler.wrapS!==33071||source.sampler.wrapT!==33071||
           !Array.isArray(p.materialColor)||p.materialColor.length!==3||
           !p.materialColor.every(x=>Number.isFinite(x)&&x>=0&&x<=1))
          throw new RangeError('GPU PNG requires validated source GLB texture/material');
        const valid=validateNativeSkinnedMesh(p.parsed.mesh);
        if(p.sourceUV0.length!==valid.vertices*2)
          throw new RangeError('GPU PNG source UV count mismatches source mesh');
        return p;
      });
      if(typeof createImageBitmap!=='function'||typeof Blob!=='function')
        throw new Error('Browser ImageBitmap missing; no vendor decoder fallback');
      const staged=[];
      try{
        for(const part of parts){
          const png=part.sourceBaseColorPng;
          const bitmap=await createImageBitmap(
            new Blob([png.bytes.slice()],{type:'image/png'}),
            {imageOrientation:'flipY',premultiplyAlpha:'none',
             colorSpaceConversion:'none'});
          try{
            if(bitmap.width!==png.width||bitmap.height!==png.height)
              throw new RangeError('Decoded source PNG dimensions mismatch');
            const tex=gl.createTexture();
            if(!tex)throw new Error('Native GPU source PNG texture unavailable');
            staged.push(tex);
            gl.activeTexture(gl.TEXTURE1);
            gl.bindTexture(gl.TEXTURE_2D,tex);
            gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,0);
            gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,0);
            gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL,gl.NONE);
            gl.texImage2D(gl.TEXTURE_2D,0,
              colorSpace==='gltf-srgb'?gl.SRGB8_ALPHA8:gl.RGBA8,gl.RGBA,
              gl.UNSIGNED_BYTE,bitmap);
            gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);
            gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
            gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
            gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
            if(gl.getError()!==gl.NO_ERROR)
              throw new Error('Native GPU source PNG texImage2D failed');
          }finally{bitmap.close()}
        }
      }catch(e){
        if(!lost)for(const tex of staged)gl.deleteTexture(tex);
        throw e;
      }
      if(disposed||lost){
        if(!lost)for(const tex of staged)gl.deleteTexture(tex);
        throw new Error('GPU PNG context became unavailable while decoding');
      }
      discardSourcePng();
      sourceTextures=staged;
      sourcePngParts=parts;
      sourcePngColorSpace=colorSpace;
      return {textures:staged.length,colorSpace,
        sourcePixels:parts.reduce((n,p)=>n+
          p.sourceBaseColorPng.width*p.sourceBaseColorPng.height,0)};
    },
    setSize(w,h,dpr=1){
      if(disposed)throw new Error('GPU palette renderer disposed');
      finite([w,h,dpr]);
      if(w<=0||h<=0||dpr<=0)throw new RangeError('GPU palette viewport invalid');
      width=Math.max(1,Math.floor(w*dpr));height=Math.max(1,Math.floor(h*dpr));
      canvas.width=width;canvas.height=height;
      if(!lost)gl.viewport(0,0,width,height);
    },
    renderBatches(parts,{eye=[1,0.5,6.2],target=[1.25,.5,0],normalPreview=false,texturePreview=false,colorManagedTexturePreview=false}={}){
      if(disposed)throw new Error('GPU palette renderer disposed');
      if(lost)return false;
      if(!Array.isArray(parts)||parts.length<1||parts.length>8)
        throw new RangeError('GPU skin batch requires 1..8 parts');
      // Validate all meshes + palettes before any GPU call, fail closed.
      if(typeof normalPreview!=='boolean'||typeof texturePreview!=='boolean'||
         typeof colorManagedTexturePreview!=='boolean')
        throw new RangeError('GPU normal and texture modes must be boolean');
      if(normalPreview&&texturePreview)
        throw new RangeError('GPU normal vs texture preview requires one mode');
      if(colorManagedTexturePreview&&!texturePreview)
        throw new RangeError('Colour-managed source requires texture preview enabled');
      if(texturePreview){
        if(sourceTextures.length!==parts.length||
           sourcePngParts.length!==parts.length)
          throw new RangeError('GPU texture preview requires uploaded exact GLB parts');
        if(sourcePngColorSpace!==(colorManagedTexturePreview?'gltf-srgb':'legacy-rgba8'))
          throw new RangeError('Source PNG GPU internal color space must match shader color mode');
        for(let i=0;i<parts.length;i++){
          if(parts[i].mesh!==sourcePngParts[i].parsed.mesh ||
             parts[i].uv0!==sourcePngParts[i].sourceUV0)
            throw new RangeError('GPU textured moving mesh must keep original source GLB mesh/UV');
        }
      }
      const prepared=parts.map(p=>checkedPart(p,normalPreview));
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
      gl.uniform1i(normalPreviewLoc,normalPreview?1:0);
      gl.uniform1i(texturePreviewLoc,texturePreview?1:0);
      gl.uniform1i(colorManagedLoc,colorManagedTexturePreview?1:0);
      gl.uniform1i(sourceColorLoc,1);
      for(let i=0;i<parts.length;i++){
        if(texturePreview){
          gl.uniform3fv(sourceTintLoc,
            new Float32Array(sourcePngParts[i].materialColor));
          gl.activeTexture(gl.TEXTURE1);
          gl.bindTexture(gl.TEXTURE_2D,sourceTextures[i]);
        }
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
      return captureStreams(part,false).positions;
    },
    /**
     * Diagnostic only: true GPU shader output for source NORMAL with four
     * weighted bone direction matrices, independent of CPU normal reference.
     */
    captureIndexedSkinnedNormals(part){
      return captureStreams(part,true).normals;
    },
    dispose(){
      if(disposed)return;disposed=true;
      canvas.removeEventListener('webglcontextlost',onLost);
      canvas.removeEventListener('webglcontextrestored',onRestored);
      discardSourcePng();
      if(!lost){
        for(const b of [rest,joints,weights,uvBuffer,normalBuffer,indices])gl.deleteBuffer(b);
        gl.deleteVertexArray(vao);gl.deleteTexture(paletteTexture);gl.deleteProgram(prog);
      }
    }
  };
}
