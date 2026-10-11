/** G2d indexed GPU draw and same-shader position/normal transform feedback. */
import {nativeLookAt,nativePerspective,multiplyNativeMat4}
  from './firstPartyWebGL2SkeletonPreview.mjs';
import {buildNativeJointSkinPalette} from './firstPartyGpuPaletteSkinning.mjs';
export function createG2dDraw(gl,{program,vao,palette,buffers,loc}){
  function view(w,h,eye,target){
    if(![...eye,...target].every(Number.isFinite))throw RangeError('G2d camera');
    gl.useProgram(program);
    gl.uniformMatrix4fv(loc.uVP,false,multiplyNativeMat4(
      nativePerspective(38*Math.PI/180,w/h,.05,100),nativeLookAt(eye,target)));
    gl.uniform1i(loc.uColor,1);
  }
  function upload(part,world){
    const matrix=buildNativeJointSkinPalette(part.mesh,world);
    if(matrix.length/4>gl.getParameter(gl.MAX_TEXTURE_SIZE))
      throw RangeError('G2d palette exceeds GPU width');
    gl.bindVertexArray(vao);
    for(const [b,data,target] of [
      [buffers[0],part.mesh.positions,gl.ARRAY_BUFFER],
      [buffers[1],part.mesh.jointIndices,gl.ARRAY_BUFFER],
      [buffers[2],part.mesh.weights,gl.ARRAY_BUFFER],
      [buffers[3],part.uv,gl.ARRAY_BUFFER],
      [buffers[4],part.normal,gl.ARRAY_BUFFER],
      [buffers[5],part.mesh.indices,gl.ELEMENT_ARRAY_BUFFER]]){
      gl.bindBuffer(target,b);gl.bufferData(target,data,gl.DYNAMIC_DRAW);
    }
    gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,palette);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA32F,matrix.length/4,1,0,
      gl.RGBA,gl.FLOAT,matrix);
    gl.uniform1i(loc.uPalette,0);
  }
  return {
    draw(parts,worlds,textures,w,h,eye,target){
      worlds.forEach((world,i)=>buildNativeJointSkinPalette(parts[i].mesh,world));
      view(w,h,eye,target);gl.viewport(0,0,w,h);
      gl.clearColor(.04,.05,.08,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      for(let i=0;i<parts.length;i++){
        const part=parts[i];upload(part,worlds[i]);
        gl.uniform3fv(loc.uTint,new Float32Array(part.tint));
        gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,textures[i]);
        gl.drawElements(gl.TRIANGLES,part.mesh.indices.length,
          part.mesh.indices instanceof Uint32Array?gl.UNSIGNED_INT:gl.UNSIGNED_SHORT,0);
      }
      gl.bindVertexArray(null);
      if(gl.getError()!==gl.NO_ERROR)throw Error('G2d indexed GPU draw error');
    },
    capture(part,world){
      const count=part.mesh.indices.length;
      if(count>8192)throw RangeError('G2d feedback capped at 8192 indices');
      const out=[new Float32Array(count*3),new Float32Array(count*3)];
      const feedback=[gl.createBuffer(),gl.createBuffer()];
      if(feedback.some(x=>!x))throw Error('G2d feedback unavailable');
      const expand=(data,stride)=>{
        const result=new data.constructor(count*stride);
        for(let i=0;i<count;i++)result.set(data.subarray(
          part.mesh.indices[i]*stride,part.mesh.indices[i]*stride+stride),i*stride);
        return result;
      };
      try{
        view(1,1,[0,0,4],[0,0,0]);upload(part,world);
        for(const [b,data,stride] of [[buffers[0],part.mesh.positions,3],
          [buffers[1],part.mesh.jointIndices,4],[buffers[2],part.mesh.weights,4],
          [buffers[3],part.uv,2],[buffers[4],part.normal,3]]){
          gl.bindBuffer(gl.ARRAY_BUFFER,b);
          gl.bufferData(gl.ARRAY_BUFFER,expand(data,stride),gl.DYNAMIC_DRAW);
        }
        for(let i=0;i<2;i++){
          gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER,feedback[i]);
          gl.bufferData(gl.TRANSFORM_FEEDBACK_BUFFER,out[i].byteLength,gl.STREAM_READ);
          gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER,i,feedback[i]);
        }
        if(gl.getError()!==gl.NO_ERROR)throw Error('G2d feedback setup error');
        gl.enable(gl.RASTERIZER_DISCARD);
        gl.beginTransformFeedback(gl.TRIANGLES);
        gl.drawArrays(gl.TRIANGLES,0,count);
        gl.endTransformFeedback();gl.disable(gl.RASTERIZER_DISCARD);
        if(gl.getError()!==gl.NO_ERROR)throw Error('G2d feedback draw error');
        for(let i=0;i<2;i++){
          gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER,feedback[i]);
          gl.getBufferSubData(gl.TRANSFORM_FEEDBACK_BUFFER,0,out[i]);
        }
        if(gl.getError()!==gl.NO_ERROR||
          out.some(a=>!Array.from(a).every(Number.isFinite)))
          throw Error('G2d feedback readback invalid');
        return {positions:out[0],normals:out[1]};
      }finally{
        gl.disable(gl.RASTERIZER_DISCARD);
        gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER,0,null);
        gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER,1,null);
        gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER,null);
        gl.bindVertexArray(null);
        for(const b of feedback)if(b)gl.deleteBuffer(b);
      }
    }
  };
}
