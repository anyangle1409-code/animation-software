/**
 * G2d source GLB PNG/UV/material + GPU four-weight moving normal/position.
 * Explicit synthetic software gate only; never loads external assets.
 */
import {checkG2dSource,G2D_KIND} from './firstPartyG2dShader.mjs';
import {compileG2dProgram} from './firstPartyG2dProgram.mjs';
import {createG2dDraw} from './firstPartyG2dDraw.mjs';
const demand=(v,s)=>{if(!v)throw RangeError('G2d: '+s);};
function gpuResources(gl){
  const program=compileG2dProgram(gl);
  const vao=gl.createVertexArray(),palette=gl.createTexture();
  const buffers=Array.from({length:6},()=>gl.createBuffer());
  if(!vao||!palette||buffers.some(x=>!x))throw Error('G2d GPU buffers');
  gl.bindVertexArray(vao);
  for(const [i,n] of [[0,3],[1,4],[2,4],[3,2],[4,3]]){
    gl.bindBuffer(gl.ARRAY_BUFFER,buffers[i]);gl.enableVertexAttribArray(i);
    if(i===1)gl.vertexAttribIPointer(i,n,gl.UNSIGNED_SHORT,0,0);
    else gl.vertexAttribPointer(i,n,gl.FLOAT,false,0,0);
  }
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,buffers[5]);gl.bindVertexArray(null);
  const loc=Object.fromEntries(['uVP','uPalette','uColor','uTint'].map(
    name=>[name,gl.getUniformLocation(program,name)]));
  if(Object.values(loc).some(x=>x===null))throw Error('G2d uniform');
  gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,palette);
  for(const [key,value] of [[gl.TEXTURE_MIN_FILTER,gl.NEAREST],
    [gl.TEXTURE_MAG_FILTER,gl.NEAREST],[gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE],
    [gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE]])
    gl.texParameteri(gl.TEXTURE_2D,key,value);
  gl.enable(gl.DEPTH_TEST);
  return {program,vao,palette,buffers,loc,dispose(){
    for(const b of buffers)gl.deleteBuffer(b);
    gl.deleteVertexArray(vao);gl.deleteTexture(palette);gl.deleteProgram(program);
  }};
}
export function createNativeMovingTexturedSkinWebGL2(canvas){
  demand(canvas&&typeof canvas.getContext==='function','canvas required');
  const gl=canvas.getContext('webgl2',{
    alpha:false,depth:true,antialias:false,preserveDrawingBuffer:true
  });
  if(!gl)throw Error('G2d WebGL2 required; no vendor fallback');
  let resources=gpuResources(gl),draw=createG2dDraw(gl,resources);
  let parts=[],textures=[],w=1,h=1,frames=0,draws=0,captures=0;
  let disposed=false,lost=false,busy=false;
  const clear=()=>{
    if(!lost)for(const tex of textures)gl.deleteTexture(tex);
    textures=[];parts=[];
  };
  const onLost=e=>{e.preventDefault();lost=true;parts=[];textures=[];};
  const onRestored=()=>{
    if(disposed)return;
    lost=false;resources=gpuResources(gl);draw=createG2dDraw(gl,resources);
    gl.viewport(0,0,w,h);
  };
  canvas.addEventListener('webglcontextlost',onLost);
  canvas.addEventListener('webglcontextrestored',onRestored);
  return {
    get kind(){return G2D_KIND;},get frames(){return frames;},
    get draws(){return draws;},get captures(){return captures;},
    get contextLost(){return lost;},
    setSize(width,height,dpr=1){
      if(disposed)throw Error('G2d disposed');
      demand([width,height,dpr].every(Number.isFinite)&&
        width>0&&height>0&&dpr>0,'positive viewport required');
      w=Math.max(1,Math.floor(width*dpr));h=Math.max(1,Math.floor(height*dpr));
      canvas.width=w;canvas.height=h;if(!lost)gl.viewport(0,0,w,h);
    },
    async setSourceBatches(batches){
      if(disposed||lost||busy)throw Error('G2d source upload unavailable');
      demand(Array.isArray(batches)&&batches.length>=1&&batches.length<=8,
        '1..8 source batches');
      const checked=batches.map(checkG2dSource);
      demand(checked.reduce((n,x)=>n+x.shape.vertices,0)<=250000,
        'aggregate source vertex budget');
      demand(typeof createImageBitmap==='function'&&typeof Blob==='function',
        'browser ImageBitmap required');
      busy=true;const staged=[];
      try{
        for(const source of checked){
          const bitmap=await createImageBitmap(new Blob([source.png],{
            type:'image/png'}),{imageOrientation:'flipY',
            premultiplyAlpha:'none',colorSpaceConversion:'none'});
          try{
            demand(bitmap.width===source.width&&bitmap.height===source.height,
              'PNG dimensions disagree with verified source');
            const tex=gl.createTexture();if(!tex)throw Error('G2d GPU texture');
            staged.push(tex);
            gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,tex);
            gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,0);
            gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,0);
            gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,gl.RGBA,gl.UNSIGNED_BYTE,bitmap);
            for(const [key,value] of [[gl.TEXTURE_MIN_FILTER,gl.LINEAR],
              [gl.TEXTURE_MAG_FILTER,gl.LINEAR],
              [gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE],
              [gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE]])
              gl.texParameteri(gl.TEXTURE_2D,key,value);
            if(gl.getError()!==gl.NO_ERROR)throw Error('G2d GPU PNG upload');
          }finally{bitmap.close();}
        }
        if(disposed||lost)throw Error('G2d context lost during PNG decode');
        clear();parts=checked;textures=staged;
        return {textures:textures.length,
          vertices:checked.reduce((n,x)=>n+x.shape.vertices,0)};
      }catch(e){
        if(!lost)for(const tex of staged)gl.deleteTexture(tex);
        throw e;
      }finally{busy=false;}
    },
    renderBatches(worlds,{eye=[1.1,.5,4.5],target=[1.1,.5,0]}={}){
      if(disposed||busy)throw Error('G2d renderer unavailable');
      if(lost)return false;
      demand(Array.isArray(worlds)&&parts.length>0&&
        worlds.length===parts.length,'one posed world palette per batch');
      demand(Array.isArray(eye)&&eye.length===3&&
        Array.isArray(target)&&target.length===3,'camera shape');
      draw.draw(parts,worlds,textures,w,h,eye,target);
      frames++;draws+=parts.length;return true;
    },
    captureIndexedGpuStreams(index,world){
      if(disposed||lost||busy)throw Error('G2d capture unavailable');
      demand(Number.isSafeInteger(index)&&index>=0&&index<parts.length,
        'capture source batch index');
      const result=draw.capture(parts[index],world);
      captures+=parts[index].mesh.indices.length/3;
      return result;
    },
    dispose(){
      if(disposed)return;disposed=true;
      canvas.removeEventListener('webglcontextlost',onLost);
      canvas.removeEventListener('webglcontextrestored',onRestored);
      clear();if(!lost)resources.dispose();
    }
  };
}
