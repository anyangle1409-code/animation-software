import type { HgMat4 } from './linearMath';
import type { HgCharacterBaseTexture, HgCharacterGeometryData } from './sceneCharacter';

export type HgCharacterTriangleGeometry = HgCharacterGeometryData;

export interface HgCharacterTriangleBuffers {
  positions: Float32Array;
  normals: Float32Array;
  uvs: Float32Array;
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

const expand2 = (
  values: readonly number[],
  indices: readonly number[],
  label: string,
): Float32Array => {
  if (values.length % 2 !== 0) throw new Error(label + ' must contain UV pairs');
  const vertices = values.length / 2;
  const out = new Float32Array(indices.length * 2);
  for (let offset = 0; offset < indices.length; offset += 1) {
    const vertex = indices[offset];
    if (!Number.isInteger(vertex) || vertex < 0 || vertex >= vertices) {
      throw new Error(label + ' index is outside the vertex buffer');
    }
    const source = vertex * 2;
    const target = offset * 2;
    out[target] = values[source];
    out[target + 1] = values[source + 1];
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
  const uvs = geometry.uvs
    ? geometry.uvs
    : Array.from({ length: vertexCount * 2 }, () => 0);
  if (colours.length !== geometry.positions.length) {
    throw new Error('Character colours must match position vertices');
  }
  if (uvs.length !== vertexCount * 2) {
    throw new Error('Character UVs must match position vertices');
  }

  return {
    positions: expand3(geometry.positions, geometry.indices, 'Character position'),
    normals: expand3(geometry.normals, geometry.indices, 'Character normal'),
    uvs: expand2(uvs, geometry.indices, 'Character UV'),
    colours: expand3(colours, geometry.indices, 'Character colour'),
  };
}

const VERTEX_SHADER = `#version 300 es
precision highp float;
layout(location = 0) in vec3 a_position;
layout(location = 1) in vec3 a_normal;
layout(location = 2) in vec3 a_colour;
layout(location = 3) in vec2 a_uv;
uniform mat4 u_clip;
uniform mat4 u_world;
uniform vec4 u_baseColour;
out vec3 v_normal;
out vec4 v_colour;
out vec2 v_uv;
void main() {
  mat3 normalMatrix = transpose(inverse(mat3(u_world)));
  v_normal = normalMatrix * a_normal;
  v_colour = vec4(a_colour * u_baseColour.rgb, u_baseColour.a);
  v_uv = a_uv;
  gl_Position = u_clip * vec4(a_position, 1.0);
}`;

const FRAGMENT_SHADER = `#version 300 es
precision highp float;
in vec3 v_normal;
in vec4 v_colour;
in vec2 v_uv;
uniform vec3 u_lightDirection;
uniform float u_ambient;
uniform sampler2D u_baseTexture;
uniform bool u_useTexture;
out vec4 outColour;
void main() {
  vec3 normal = normalize(v_normal);
  vec3 light = normalize(-u_lightDirection);
  float diffuse = max(dot(normal, light), 0.0);
  float intensity = clamp(u_ambient + (1.0 - u_ambient) * diffuse, 0.0, 1.0);
  vec4 texel = u_useTexture ? texture(u_baseTexture, v_uv) : vec4(1.0);
  outColour = vec4(v_colour.rgb * texel.rgb * intensity, v_colour.a * texel.a);
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
  private readonly uvBuffer: WebGLBuffer;
  private readonly clipLocation: WebGLUniformLocation;
  private readonly worldLocation: WebGLUniformLocation;
  private readonly baseColourLocation: WebGLUniformLocation;
  private readonly lightLocation: WebGLUniformLocation;
  private readonly ambientLocation: WebGLUniformLocation;
  private readonly textureLocation: WebGLUniformLocation;
  private readonly useTextureLocation: WebGLUniformLocation;
  private readonly textures = new WeakMap<object, Map<string, WebGLTexture>>();
  private readonly textureHandles = new Set<WebGLTexture>();
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
    const uvBuffer = gl.createBuffer();
    if (!positionBuffer || !normalBuffer || !colourBuffer || !uvBuffer) {
      if (positionBuffer) gl.deleteBuffer(positionBuffer);
      if (normalBuffer) gl.deleteBuffer(normalBuffer);
      if (colourBuffer) gl.deleteBuffer(colourBuffer);
      if (uvBuffer) gl.deleteBuffer(uvBuffer);
      gl.deleteProgram(program);
      throw new Error('WebGL character buffer allocation failed');
    }

    this.program = program;
    this.positionBuffer = positionBuffer;
    this.normalBuffer = normalBuffer;
    this.colourBuffer = colourBuffer;
    this.uvBuffer = uvBuffer;
    this.clipLocation = uniform(gl, program, 'u_clip');
    this.worldLocation = uniform(gl, program, 'u_world');
    this.baseColourLocation = uniform(gl, program, 'u_baseColour');
    this.lightLocation = uniform(gl, program, 'u_lightDirection');
    this.ambientLocation = uniform(gl, program, 'u_ambient');
    this.textureLocation = uniform(gl, program, 'u_baseTexture');
    this.useTextureLocation = uniform(gl, program, 'u_useTexture');
  }

  draw(
    geometry: HgCharacterTriangleGeometry,
    clip: HgMat4,
    world: { readonly elements: ArrayLike<number> },
    baseColour: readonly [number, number, number, number],
    baseTexture: HgCharacterBaseTexture | null = null,
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
    gl.bindBuffer(gl.ARRAY_BUFFER, this.uvBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, buffers.uvs, gl.STREAM_DRAW);
    gl.enableVertexAttribArray(3);
    gl.vertexAttribPointer(3, 2, gl.FLOAT, false, 0, 0);

    gl.uniformMatrix4fv(this.clipLocation, false, new Float32Array(clip.elements));
    gl.uniformMatrix4fv(
      this.worldLocation,
      false,
      new Float32Array(Array.from(world.elements)),
    );
    gl.uniform4fv(this.baseColourLocation, new Float32Array(baseColour));
    gl.uniform3fv(this.lightLocation, new Float32Array(lightDirection));
    gl.uniform1f(this.ambientLocation, ambient);
    if (baseTexture) {
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, this.textureFor(baseTexture));
      gl.uniform1i(this.textureLocation, 0);
      gl.uniform1i(this.useTextureLocation, 1);
    } else {
      gl.uniform1i(this.useTextureLocation, 0);
    }
    gl.drawArrays(gl.TRIANGLES, 0, buffers.positions.length / 3);
  }

  private textureFor(texture: HgCharacterBaseTexture): WebGLTexture {
    const gl = this.gl;
    const imageKey = texture.image as unknown as object;
    const samplerKey = [
      texture.flipY ? 1 : 0,
      texture.wrapS ?? 10497,
      texture.wrapT ?? 10497,
      texture.magFilter ?? 9729,
      texture.minFilter ?? 9987,
    ].join(':');
    let variants = this.textures.get(imageKey);
    if (!variants) {
      variants = new Map();
      this.textures.set(imageKey, variants);
    }
    let handle = variants.get(samplerKey);
    if (handle) return handle;

    handle = gl.createTexture();
    if (!handle) throw new Error('WebGL character texture allocation failed');
    variants.set(samplerKey, handle);
    this.textureHandles.add(handle);

    gl.bindTexture(gl.TEXTURE_2D, handle);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, texture.flipY ? 1 : 0);
    gl.texImage2D(
      gl.TEXTURE_2D,
      0,
      gl.SRGB8_ALPHA8,
      gl.RGBA,
      gl.UNSIGNED_BYTE,
      texture.image,
    );
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, texture.wrapS ?? 10497);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, texture.wrapT ?? 10497);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, texture.magFilter ?? 9729);
    const minFilter = texture.minFilter ?? 9987;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, minFilter);
    if (minFilter >= 9984 && minFilter <= 9987) gl.generateMipmap(gl.TEXTURE_2D);
    return handle;
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.gl.deleteBuffer(this.positionBuffer);
    this.gl.deleteBuffer(this.normalBuffer);
    this.gl.deleteBuffer(this.colourBuffer);
    this.gl.deleteBuffer(this.uvBuffer);
    for (const texture of this.textureHandles) this.gl.deleteTexture(texture);
    this.textureHandles.clear();
    this.gl.deleteProgram(this.program);
  }
}
