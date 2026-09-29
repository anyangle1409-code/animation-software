import type { HgMat4 } from './linearMath';
import { HgVec3 } from './linearMath';
import {
  primitiveTriangleNormals,
  primitiveTrianglePositions,
  type HgPrimitiveGeometryData,
} from './primitiveGeometry';

const VERTEX_SHADER = `#version 300 es
precision highp float;
layout(location = 0) in vec3 a_position;
layout(location = 1) in vec3 a_normal;
uniform mat4 u_clip;
uniform mat4 u_world;
out vec3 v_normal;
void main() {
  mat3 normalMatrix = transpose(inverse(mat3(u_world)));
  v_normal = normalMatrix * a_normal;
  gl_Position = u_clip * vec4(a_position, 1.0);
}`;

const FRAGMENT_SHADER = `#version 300 es
precision highp float;
in vec3 v_normal;
uniform vec4 u_colour;
uniform vec3 u_lightDirection;
uniform float u_ambient;
out vec4 outColour;
void main() {
  vec3 normal = normalize(v_normal);
  vec3 light = normalize(-u_lightDirection);
  float diffuse = max(dot(normal, light), 0.0);
  float intensity = clamp(u_ambient + (1.0 - u_ambient) * diffuse, 0.0, 1.0);
  outColour = vec4(u_colour.rgb * intensity, u_colour.a);
}`;

const compileShader = (
  gl: WebGL2RenderingContext,
  type: number,
  source: string,
): WebGLShader => {
  const shader = gl.createShader(type);
  if (!shader) throw new Error('WebGL shader allocation failed');
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const message = gl.getShaderInfoLog(shader) || 'unknown shader error';
    gl.deleteShader(shader);
    throw new Error('WebGL shader compile failed: ' + message);
  }
  return shader;
};

const uniform = (
  gl: WebGL2RenderingContext,
  program: WebGLProgram,
  name: string,
): WebGLUniformLocation => {
  const location = gl.getUniformLocation(program, name);
  if (!location) throw new Error('WebGL uniform is unavailable: ' + name);
  return location;
};

/**
 * Project-owned lit triangle pipeline for non-skinned meshes.
 *
 * It intentionally covers the minimum renderer state the studio needs before
 * textures and GPU skinning are migrated: viewport, clear, depth/culling,
 * indexed primitive expansion and deterministic directional lighting.
 */
export class HgLitTrianglePipeline {
  private readonly program: WebGLProgram;
  private readonly positionBuffer: WebGLBuffer;
  private readonly normalBuffer: WebGLBuffer;
  private readonly clipLocation: WebGLUniformLocation;
  private readonly worldLocation: WebGLUniformLocation;
  private readonly colourLocation: WebGLUniformLocation;
  private readonly lightLocation: WebGLUniformLocation;
  private readonly ambientLocation: WebGLUniformLocation;
  private readonly lightDirection = new HgVec3(-0.45, -1, -0.55).normalize();
  private ambient = 0.28;
  private disposed = false;

  constructor(private readonly gl: WebGL2RenderingContext) {
    const vertex = compileShader(gl, gl.VERTEX_SHADER, VERTEX_SHADER);
    const fragment = compileShader(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER);
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

    const positionBuffer = gl.createBuffer();
    const normalBuffer = gl.createBuffer();
    if (!positionBuffer || !normalBuffer) {
      if (positionBuffer) gl.deleteBuffer(positionBuffer);
      if (normalBuffer) gl.deleteBuffer(normalBuffer);
      gl.deleteProgram(program);
      throw new Error('WebGL lit-triangle buffer allocation failed');
    }

    this.program = program;
    this.positionBuffer = positionBuffer;
    this.normalBuffer = normalBuffer;
    this.clipLocation = uniform(gl, program, 'u_clip');
    this.worldLocation = uniform(gl, program, 'u_world');
    this.colourLocation = uniform(gl, program, 'u_colour');
    this.lightLocation = uniform(gl, program, 'u_lightDirection');
    this.ambientLocation = uniform(gl, program, 'u_ambient');

    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);
    gl.enable(gl.CULL_FACE);
    gl.cullFace(gl.BACK);
    gl.frontFace(gl.CCW);
  }

  setViewport(width: number, height: number, pixelRatio = 1): void {
    if (!(width > 0) || !(height > 0) || !(pixelRatio > 0)) {
      throw new Error('Lit renderer viewport dimensions must be positive');
    }
    this.gl.viewport(
      0,
      0,
      Math.max(1, Math.round(width * pixelRatio)),
      Math.max(1, Math.round(height * pixelRatio)),
    );
  }

  clear(colour: readonly [number, number, number, number]): void {
    if (this.disposed) throw new Error('Lit triangle pipeline is disposed');
    this.gl.clearColor(colour[0], colour[1], colour[2], colour[3]);
    this.gl.clear(this.gl.COLOR_BUFFER_BIT | this.gl.DEPTH_BUFFER_BIT);
  }

  setLightDirection(direction: { x: number; y: number; z: number }): void {
    this.lightDirection.set(direction.x, direction.y, direction.z);
    if (this.lightDirection.lengthSq() < 1e-12) {
      throw new Error('Lit renderer light direction cannot be zero');
    }
    this.lightDirection.normalize();
  }

  setAmbient(value: number): void {
    if (!Number.isFinite(value) || value < 0 || value > 1) {
      throw new Error('Lit renderer ambient light must be between 0 and 1');
    }
    this.ambient = value;
  }

  drawPrimitive(
    geometry: HgPrimitiveGeometryData,
    clipMatrix: HgMat4,
    worldMatrix: { readonly elements: ArrayLike<number> },
    colour: readonly [number, number, number, number],
  ): void {
    if (this.disposed) throw new Error('Lit triangle pipeline is disposed');
    const positions = primitiveTrianglePositions(geometry);
    const normals = primitiveTriangleNormals(geometry);
    const gl = this.gl;

    gl.useProgram(this.program);

    gl.bindBuffer(gl.ARRAY_BUFFER, this.positionBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STREAM_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);

    gl.bindBuffer(gl.ARRAY_BUFFER, this.normalBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, normals, gl.STREAM_DRAW);
    gl.enableVertexAttribArray(1);
    gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 0, 0);

    gl.uniformMatrix4fv(this.clipLocation, false, new Float32Array(clipMatrix.elements));
    gl.uniformMatrix4fv(
      this.worldLocation,
      false,
      new Float32Array(Array.from(worldMatrix.elements)),
    );
    gl.uniform4fv(this.colourLocation, new Float32Array(colour));
    gl.uniform3fv(
      this.lightLocation,
      new Float32Array([
        this.lightDirection.x,
        this.lightDirection.y,
        this.lightDirection.z,
      ]),
    );
    gl.uniform1f(this.ambientLocation, this.ambient);
    gl.drawArrays(gl.TRIANGLES, 0, positions.length / 3);
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.gl.deleteBuffer(this.positionBuffer);
    this.gl.deleteBuffer(this.normalBuffer);
    this.gl.deleteProgram(this.program);
  }
}
