import type { HgMat4 } from './linearMath';

export interface HgCharacterTriangleGeometry {
  readonly positions: readonly number[];
  readonly normals: readonly number[];
  readonly indices: readonly number[];
  readonly colours?: readonly number[];
}

export interface HgCharacterTriangleBuffers {
  positions: Float32Array;
  normals: Float32Array;
  colours: Float32Array;
}

const expand3 = (
  values: readonly number[],
  indices: readonly number[],
  label: string,
): Float32Array => {
  if (values.length % 3 !== 0) throw new Error(label + ' must contain XYZ triples');
  const vertices = values.length / 3;
  const out = new Float32Array(indices.length * 3);
  for (let offset = 0; offset < indices.length; offset += 1) {
    const vertex = indices[offset];
    if (!Number.isInteger(vertex) || vertex < 0 || vertex >= vertices) {
      throw new Error(label + ' index is outside the vertex buffer');
    }
    const source = vertex * 3;
    const target = offset * 3;
    out[target] = values[source];
    out[target + 1] = values[source + 1];
    out[target + 2] = values[source + 2];
  }
  return out;
};

/** Expand one indexed posed character mesh into draw-order triangle buffers. */
export function characterTriangleBuffers(
  geometry: HgCharacterTriangleGeometry,
): HgCharacterTriangleBuffers {
  if (geometry.positions.length !== geometry.normals.length) {
    throw new Error('Character normals must match position vertices');
  }
  if (geometry.indices.length % 3 !== 0) {
    throw new Error('Character indices must contain complete triangles');
  }

  const vertexCount = geometry.positions.length / 3;
  const colours = geometry.colours
    ? geometry.colours
    : Array.from({ length: vertexCount * 3 }, () => 1);
  if (colours.length !== geometry.positions.length) {
    throw new Error('Character colours must match position vertices');
  }

  return {
    positions: expand3(geometry.positions, geometry.indices, 'Character position'),
    normals: expand3(geometry.normals, geometry.indices, 'Character normal'),
    colours: expand3(colours, geometry.indices, 'Character colour'),
  };
}

const VERTEX_SHADER = `#version 300 es
precision highp float;
layout(location = 0) in vec3 a_position;
layout(location = 1) in vec3 a_normal;
layout(location = 2) in vec3 a_colour;
uniform mat4 u_clip;
uniform mat4 u_world;
uniform vec4 u_baseColour;
out vec3 v_normal;
out vec4 v_colour;
void main() {
  mat3 normalMatrix = transpose(inverse(mat3(u_world)));
  v_normal = normalMatrix * a_normal;
  v_colour = vec4(a_colour * u_baseColour.rgb, u_baseColour.a);
  gl_Position = u_clip * vec4(a_position, 1.0);
}`;

const FRAGMENT_SHADER = `#version 300 es
precision highp float;
in vec3 v_normal;
in vec4 v_colour;
uniform vec3 u_lightDirection;
uniform float u_ambient;
out vec4 outColour;
void main() {
  vec3 normal = normalize(v_normal);
  vec3 light = normalize(-u_lightDirection);
  float diffuse = max(dot(normal, light), 0.0);
  float intensity = clamp(u_ambient + (1.0 - u_ambient) * diffuse, 0.0, 1.0);
  outColour = vec4(v_colour.rgb * intensity, v_colour.a);
}`;

const compile = (
  gl: WebGL2RenderingContext,
  type: number,
  source: string,
): WebGLShader => {
  const shader = gl.createShader(type);
  if (!shader) throw new Error('WebGL character shader allocation failed');
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const message = gl.getShaderInfoLog(shader) || 'unknown shader error';
    gl.deleteShader(shader);
    throw new Error('WebGL character shader compile failed: ' + message);
  }
  return shader;
};

const uniform = (
  gl: WebGL2RenderingContext,
  program: WebGLProgram,
  name: string,
): WebGLUniformLocation => {
  const location = gl.getUniformLocation(program, name);
  if (!location) throw new Error('WebGL character uniform is unavailable: ' + name);
  return location;
};

/** Project-owned lit WebGL pipeline for posed/skinned character triangles. */
export class HgCharacterTrianglePipeline {
  private readonly program: WebGLProgram;
  private readonly positionBuffer: WebGLBuffer;
  private readonly normalBuffer: WebGLBuffer;
  private readonly colourBuffer: WebGLBuffer;
  private readonly clipLocation: WebGLUniformLocation;
  private readonly worldLocation: WebGLUniformLocation;
  private readonly baseColourLocation: WebGLUniformLocation;
  private readonly lightLocation: WebGLUniformLocation;
  private readonly ambientLocation: WebGLUniformLocation;
  private disposed = false;

  constructor(private readonly gl: WebGL2RenderingContext) {
    const vertex = compile(gl, gl.VERTEX_SHADER, VERTEX_SHADER);
    const fragment = compile(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER);
    const program = gl.createProgram();
    if (!program) throw new Error('WebGL character program allocation failed');
    try {
      gl.attachShader(program, vertex);
      gl.attachShader(program, fragment);
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        throw new Error(
          'WebGL character program link failed: ' +
          (gl.getProgramInfoLog(program) || 'unknown link error'),
        );
      }
    } finally {
      gl.deleteShader(vertex);
      gl.deleteShader(fragment);
    }

    const positionBuffer = gl.createBuffer();
    const normalBuffer = gl.createBuffer();
    const colourBuffer = gl.createBuffer();
    if (!positionBuffer || !normalBuffer || !colourBuffer) {
      if (positionBuffer) gl.deleteBuffer(positionBuffer);
      if (normalBuffer) gl.deleteBuffer(normalBuffer);
      if (colourBuffer) gl.deleteBuffer(colourBuffer);
      gl.deleteProgram(program);
      throw new Error('WebGL character buffer allocation failed');
    }

    this.program = program;
    this.positionBuffer = positionBuffer;
    this.normalBuffer = normalBuffer;
    this.colourBuffer = colourBuffer;
    this.clipLocation = uniform(gl, program, 'u_clip');
    this.worldLocation = uniform(gl, program, 'u_world');
    this.baseColourLocation = uniform(gl, program, 'u_baseColour');
    this.lightLocation = uniform(gl, program, 'u_lightDirection');
    this.ambientLocation = uniform(gl, program, 'u_ambient');
  }

  draw(
    geometry: HgCharacterTriangleGeometry,
    clip: HgMat4,
    world: { readonly elements: ArrayLike<number> },
    baseColour: readonly [number, number, number, number],
    lightDirection: readonly [number, number, number] = [-0.45, -1, -0.55],
    ambient = 0.28,
  ): void {
    if (this.disposed) throw new Error('WebGL character pipeline is disposed');
    const buffers = characterTriangleBuffers(geometry);
    const gl = this.gl;
    gl.useProgram(this.program);

    const upload = (
      location: number,
      buffer: WebGLBuffer,
      values: Float32Array,
    ) => {
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, values, gl.STREAM_DRAW);
      gl.enableVertexAttribArray(location);
      gl.vertexAttribPointer(location, 3, gl.FLOAT, false, 0, 0);
    };
    upload(0, this.positionBuffer, buffers.positions);
    upload(1, this.normalBuffer, buffers.normals);
    upload(2, this.colourBuffer, buffers.colours);

    gl.uniformMatrix4fv(this.clipLocation, false, new Float32Array(clip.elements));
    gl.uniformMatrix4fv(
      this.worldLocation,
      false,
      new Float32Array(Array.from(world.elements)),
    );
    gl.uniform4fv(this.baseColourLocation, new Float32Array(baseColour));
    gl.uniform3fv(this.lightLocation, new Float32Array(lightDirection));
    gl.uniform1f(this.ambientLocation, ambient);
    gl.drawArrays(gl.TRIANGLES, 0, buffers.positions.length / 3);
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.gl.deleteBuffer(this.positionBuffer);
    this.gl.deleteBuffer(this.normalBuffer);
    this.gl.deleteBuffer(this.colourBuffer);
    this.gl.deleteProgram(this.program);
  }
}
