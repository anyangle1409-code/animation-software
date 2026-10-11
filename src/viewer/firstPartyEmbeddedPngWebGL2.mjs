/**
 * G1f: actual original-browser WebGL2 upload + source PNG base-colour sampling.
 * Input must come from the G1e strictly validated embedded PNG/UV0 GLB adapter.
 * No HTTP image fetch, imported image libraries, PBR, anatomical claims or
 * glTF animation loader. Unskinned / externally-authored posed vertex preview
 * only; GPU vertex-joint LBS integration is a distinct task.
 */
import {nativeLookAt,nativePerspective,multiplyNativeMat4}
  from './firstPartyWebGL2SkeletonPreview.mjs';
import {HGPT_EMBEDDED_PNG_KIND} from './firstPartyEmbeddedPngSource.mjs';
export const HGPT_TEXTURE_GPU_KIND='hgpt-webgl2-source-embedded-png-preview-v1';
const fail=s=>{throw new RangeError('Native PNG texture rejected: '+s);};
const requireThat=(v,m)=>{if(!v)fail(m);};
const finite=v=>Array.from(v).every(Number.isFinite);
function shader(gl,type,body){
  const s=gl.createShader(type);
  if(!s)throw new Error('Native PNG shader unavailable');
  gl.shaderSource(s,body);gl.compileShader(s);
  if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)){
    const e=gl.getShaderInfoLog(s)||'unknown PNG shader compile failure';
    gl.deleteShader(s);throw new Error(e);
  }
  return s;
}
function linked(gl){
  const vertex=shader(gl,gl.VERTEX_SHADER,
    '#version 300 es\nprecision highp float;\nlayout(location=0) in vec3 aPosition;\nlayout(location=1) in vec2 aUV;\nuniform mat4 uVP;\nout vec2 vUV;\nvoid main(){gl_Position=uVP*vec4(aPosition,1.0);vUV=aUV;}');
  const fragment=shader(gl,gl.FRAGMENT_SHADER,
    '#version 300 es\nprecision highp float;\nin vec2 vUV;\nuniform sampler2D uColor;\nuniform vec3 uTint;\nout vec4 outColor;\nvoid main(){outColor=vec4(texture(uColor,vUV).rgb*uTint,1.0);}');
  const p=gl.createProgram();if(!p)throw new Error('Native PNG program unavailable');
  gl.attachShader(p,vertex);gl.attachShader(p,fragment);gl.linkProgram(p);
  gl.deleteShader(vertex);gl.deleteShader(fragment);
  if(!gl.getProgramParameter(p,gl.LINK_STATUS)){
    const e=gl.getProgramInfoLog(p)||'native texture link failure';
    gl.deleteProgram(p);throw new Error(e);
  }
  return p;
}
function partSource(part){
  const parsed=part?.parsed;
  const mesh=parsed?.mesh;
  const png=part?.sourceBaseColorPng;
  requireThat(mesh && mesh.positions instanceof Float32Array &&
    (mesh.indices instanceof Uint16Array || mesh.indices instanceof Uint32Array) &&
    part.sourceUV0 instanceof Float32Array &&
    part.sourceUV0.length===mesh.positions.length/3*2 &&
    png?.kind===HGPT_EMBEDDED_PNG_KIND &&
    png.bytes instanceof Uint8Array&&png.bytes.length>=57&&
    png.bytes.length<=8*1024*1024 &&
    Number.isSafeInteger(png.width)&&Number.isSafeInteger(png.height)&&
    png.width>0&&png.height>0&&png.width*png.height<=4194304&&
    png.sampler?.magFilter===9729&&png.sampler.minFilter===9729&&
    png.sampler.wrapS===33071&&png.sampler.wrapT===33071,
    'source G1e GLB PNG and UV0 required');
  requireThat(Array.isArray(part.materialColor)&&part.materialColor.length===3&&
    part.materialColor.every(v=>Number.isFinite(v)&&v>=0&&v<=1),
    'bounded original material tint required');
  requireThat(mesh.positions.length>=9&&mesh.positions.length%3===0 &&
    mesh.indices.length>=3&&mesh.indices.length%3===0 &&
    finite(mesh.positions)&&finite(part.sourceUV0)&&
    Array.from(mesh.indices).every(i=>i<mesh.positions.length/3),
    'source triangles/UV0 must be valid');
  return {mesh,png,uv:part.sourceUV0,tint:[...part.materialColor]};
}
export function createNativeEmbeddedPngWebGL2(canvas){
  requireThat(canvas&&typeof canvas.getContext==='function','HTML canvas required');
  const gl=canvas.getContext('webgl2',{alpha:false,depth:true,antialias:false,preserveDrawingBuffer:true});
  if(!gl)throw new Error('WebGL2 unavailable; no Three.js texture fallback');
  let program=null,vao=null,position=null,uv=null,indices=null,vpLoc=null,tintLoc=null,texLoc=null;
  let textures=[],batches=[],frames=0,draws=0,w=1,h=1,lost=false,disposed=false;
  const deleteTextures=()=>{
    if(!lost)for(const item of textures)gl.deleteTexture(item);
    textures=[];batches=[];
  };
  const prepare=()=>{
    program=linked(gl);
    vao=gl.createVertexArray();
    position=gl.createBuffer();uv=gl.createBuffer();indices=gl.createBuffer();
    if(!vao||!position||!uv||!indices)throw new Error('Native PNG GPU buffers unavailable');
    gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER,position);
    gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,3,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ARRAY_BUFFER,uv);
    gl.enableVertexAttribArray(1);gl.vertexAttribPointer(1,2,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,indices);
    gl.bindVertexArray(null);
    vpLoc=gl.getUniformLocation(program,'uVP');
    tintLoc=gl.getUniformLocation(program,'uTint');
    texLoc=gl.getUniformLocation(program,'uColor');
    if(vpLoc===null||tintLoc===null||texLoc===null)
      throw new Error('Native PNG shader uniforms unavailable');
    gl.enable(gl.DEPTH_TEST);
  };
  const onLost=e=>{e.preventDefault();lost=true;textures=[];batches=[];};
  const onRestored=()=>{if(disposed)return;lost=false;prepare();gl.viewport(0,0,w,h);};
  canvas.addEventListener('webglcontextlost',onLost);
  canvas.addEventListener('webglcontextrestored',onRestored);
  try{prepare();}catch(e){
    canvas.removeEventListener('webglcontextlost',onLost);
    canvas.removeEventListener('webglcontextrestored',onRestored);throw e;
  }
  return {
    get kind(){return HGPT_TEXTURE_GPU_KIND;},
    get draws(){return draws;},
    get frames(){return frames;},
    get contextLost(){return lost;},
    setSize(width,height,dpr=1){
      if(disposed)throw new Error('Native PNG preview disposed');
      requireThat(finite([width,height,dpr])&&width>0&&height>0&&dpr>0,
        'finite positive viewport required');
      w=Math.max(1,Math.floor(width*dpr));h=Math.max(1,Math.floor(height*dpr));
      canvas.width=w;canvas.height=h;
      if(!lost)gl.viewport(0,0,w,h);
    },
    async setSourceBatches(sourceBatches){
      if(disposed||lost)throw new Error('Native PNG context unavailable');
      requireThat(Array.isArray(sourceBatches)&&sourceBatches.length>=1&&
        sourceBatches.length<=8,'1..8 G1e source batches required');
      const checked=sourceBatches.map(partSource);
      let vertices=0;
      for(const p of checked){
        vertices+=p.mesh.positions.length/3;
        requireThat(vertices<=250000,'source vertex count exceeds budget');
      }
      requireThat(typeof createImageBitmap==='function'&&typeof Blob==='function',
        'browser PNG ImageBitmap decoder required; no external fallback');
      // Decode source-owned bytes locally only, flip source glTF image from
      // top-left row order to WebGL texture bottom-left. Do not infer UV flip.
      const staged=[];
      try{
        for(const p of checked){
          const blob=new Blob([p.png.bytes.slice()],{type:'image/png'});
          const bitmap=await createImageBitmap(blob,{
            imageOrientation:'flipY',premultiplyAlpha:'none',
            colorSpaceConversion:'none',
          });
          try{
            requireThat(bitmap.width===p.png.width&&bitmap.height===p.png.height,
              'decoded PNG dimensions disagree with source header');
            const tex=gl.createTexture();
            if(!tex)throw new Error('Native PNG GPU texture unavailable');
            staged.push(tex);
            gl.bindTexture(gl.TEXTURE_2D,tex);
            gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,0);
            gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,0);
            // RGBA8 diagnostic: no sRGB/PBR conversion is claimed yet.
            gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,gl.RGBA,gl.UNSIGNED_BYTE,bitmap);
            gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);
            gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
            gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
            gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
            requireThat(gl.getError()===gl.NO_ERROR,'actual WebGL2 texture upload error');
          }finally{bitmap.close();}
        }
      }catch(e){
        for(const t of staged)gl.deleteTexture(t);
        throw e;
      }
      if(disposed||lost){
        if(!lost)for(const t of staged)gl.deleteTexture(t);
        throw new Error('Native PNG renderer became unavailable during async decode');
      }
      deleteTextures();
      textures=staged;batches=checked;
      return {textures:textures.length,
        pixels:checked.reduce((n,p)=>n+p.png.width*p.png.height,0)};
    },
    render({eye=[1.1,.5,5],target=[1.1,.5,0]}={}){
      if(disposed)throw new Error('Native PNG preview disposed');
      if(lost)return false;
      requireThat(batches.length&&textures.length===batches.length,
        'call setSourceBatches on strict G1e original image data');
      requireThat(finite([...eye,...target]),'finite camera required');
      const vp=multiplyNativeMat4(nativePerspective(38*Math.PI/180,w/h,.05,100),
        nativeLookAt(eye,target));
      gl.viewport(0,0,w,h);gl.clearColor(.04,.05,.08,1);
      gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      gl.useProgram(program);gl.uniformMatrix4fv(vpLoc,false,vp);
      gl.uniform1i(texLoc,0);gl.activeTexture(gl.TEXTURE0);
      gl.bindVertexArray(vao);
      for(let i=0;i<batches.length;i++){
        const part=batches[i];
        gl.uniform3fv(tintLoc,new Float32Array(part.tint));
        gl.bindTexture(gl.TEXTURE_2D,textures[i]);
        gl.bindBuffer(gl.ARRAY_BUFFER,position);
        gl.bufferData(gl.ARRAY_BUFFER,part.mesh.positions,gl.DYNAMIC_DRAW);
        gl.bindBuffer(gl.ARRAY_BUFFER,uv);
        gl.bufferData(gl.ARRAY_BUFFER,part.uv,gl.DYNAMIC_DRAW);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,indices);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,part.mesh.indices,gl.DYNAMIC_DRAW);
        gl.drawElements(gl.TRIANGLES,part.mesh.indices.length,
          part.mesh.indices instanceof Uint32Array?gl.UNSIGNED_INT:gl.UNSIGNED_SHORT,0);
        draws++;
      }
      gl.bindVertexArray(null);frames++;
      requireThat(gl.getError()===gl.NO_ERROR,'native PNG draw reported GPU error');
      return true;
    },
    dispose(){
      if(disposed)return;disposed=true;
      canvas.removeEventListener('webglcontextlost',onLost);
      canvas.removeEventListener('webglcontextrestored',onRestored);
      deleteTextures();
      if(!lost){
        for(const item of [position,uv,indices])gl.deleteBuffer(item);
        gl.deleteVertexArray(vao);gl.deleteProgram(program);
      }
    },
  };
}
