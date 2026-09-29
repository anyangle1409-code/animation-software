import type { HgMat4 } from './linearMath';

export interface HgTriangleDraw {
  readonly positions: Float32Array;
  readonly matrix: HgMat4;
  readonly colour: readonly [number, number, number, number];
}

const VERTEX_SHADER = `#version 300 es
precision highp float;
layout(location = 0) in vec3 a_position;
uniform mat4 u_matrix;
void main() {
  gl_Position = u_matrix * vec4(a_position, 1.0);
}`;

const FRAGMENT_SHADER = `#version 300 es
precision highp float;
uniform vec4 u_colour;
out vec4 outColour;
void main() {
  outColour = u_colour;
}`;

const shader = (
  gl: WebGL2RenderingContext,
  type: number,
  source: string,
): WebGLShader => {
  const result = gl.createShader(type);
  if (!result) throw new Error('WebGL shader allocation failed');
  gl.shaderSource(result, source);
  gl.compileShader(result);
  if (!gl.getShaderParameter(result, gl.COMPILE_STATUS)) {
    const message = gl.getShaderInfoLog(result) || 'unknown shader error';
    gl.deleteShader(result);
    throw new Error('WebGL shader compile failed: ' + message);
  }
  return result;
};

export class HgTrianglePipeline {
  private readonly program: WebGLProgram;
  private readonly buffer: WebGLBuffer;
  private readonly matrixLocation: WebGLUniformLocation;
  private readonly colourLocation: WebGLUniformLocation;
  private disposed = false;

  constructor(private readonly gl: WebGL2RenderingContext) {
    const vertex = shader(gl, gl.VERTEX_SHADER, VERTEX_SHADER);
    const fragment = shader(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER);
    const program = gl.createProgram();
    if (!program) throw new Error('WebGL program allocation failed');

    try {
      gl.attachShader(program, vertex);
      gl.attachShader(program, fragment);
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        throw new Error(
          'WebGL program link failed: ' +
          (gl.getProgramInfoLog(program) || 'unknown link error'),
        );
      }
    } finally {
      gl.deleteShader(vertex);
      gl.deleteShader(fragment);
    }

    const buffer = gl.createBuffer();
    if (!buffer) {
      gl.deleteProgram(program);
      throw new Error('WebGL vertex-buffer allocation failed');
    }
    const matrixLocation = gl.getUniformLocation(program, 'u_matrix');
    const colourLocation = gl.getUniformLocation(program, 'u_colour');
    if (!matrixLocation || !colourLocation) {
      gl.deleteBuffer(buffer);
      gl.deleteProgram(program);
      throw new Error('WebGL triangle uniforms are unavailable');
    }

    this.program = program;
    this.buffer = buffer;
    this.matrixLocation = matrixLocation;
    this.colourLocation = colourLocation;
  }

  draw(draw: HgTriangleDraw): void {
    if (this.disposed) throw new Error('Triangle pipeline is disposed');
    if (draw.positions.length % 9 !== 0) {
      throw new Error('Triangle positions must contain complete XYZ triangles');
    }

    const gl = this.gl;
    gl.useProgram(this.program);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.buffer);
    gl.bufferData(gl.ARRAY_BUFFER, draw.positions, gl.STREAM_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
    gl.uniformMatrix4fv(
      this.matrixLocation,
      false,
      new Float32Array(draw.matrix.elements),
    );
    gl.uniform4fv(this.colourLocation, new Float32Array(draw.colour));
    gl.drawArrays(gl.TRIANGLES, 0, draw.positions.length / 3);
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.gl.deleteBuffer(this.buffer);
    this.gl.deleteProgram(this.program);
  }
}
