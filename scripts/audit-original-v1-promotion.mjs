#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = process.cwd();
const CONTRACT_PATH = path.join(ROOT, "ORIGINAL_V1_PROMOTION_CONTRACT.json");
const ALLOWLIST_PATH = path.join(ROOT, "RELEASE_ASSET_ALLOWLIST.json");
const COMPONENTS_PATH = path.join(ROOT, "FIRST_PARTY_COMPONENT_MANIFEST.json");
const RIG_PATH = path.join(ROOT, "ORIGINAL_V1_WORK", "hgpt_canonical_v4_original.json");

const FINAL_GATE_VALUES = new Set(["approved", "verified_production"]);
const REQUIRED_COMPONENTS = ["male_character", "male_shorts", "canonical_rig"];
const FORBIDDEN_PRODUCTION_TOKENS = [
  "candidate",
  "baseline",
  "corner_final",
  "makehuman",
  "meshy",
  "v9",
  "v10",
  "v11",
  "v12",
  "v13",
  "v14",
  "v15",
];

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function sha256(file) {
  const h = crypto.createHash("sha256");
  h.update(fs.readFileSync(file));
  return h.digest("hex");
}

function globRegex(pattern) {
  const normalized = pattern.replaceAll("\\", "/");
  let out = "^";
  const special = new Set(["\\", "^", "$", ".", "+", "(", ")", "[", "]", "{", "}", "|"]);
  for (let i = 0; i < normalized.length;) {
    if (normalized.startsWith("**/", i)) {
      out += "(?:.*/)?";
      i += 3;
    } else if (normalized.startsWith("**", i)) {
      out += ".*";
      i += 2;
    } else if (normalized[i] === "*") {
      out += "[^/]*";
      i += 1;
    } else if (normalized[i] === "?") {
      out += "[^/]";
      i += 1;
    } else {
      const ch = normalized[i];
      out += special.has(ch) ? "\\" + ch : ch;
      i += 1;
    }
  }
  return new RegExp(out + "$", "i");
}

function parseGlb(file) {
  const data = fs.readFileSync(file);
  if (data.length < 20) throw new Error("GLB too short");
  if (data.toString("ascii", 0, 4) !== "glTF") throw new Error("bad GLB magic");
  const version = data.readUInt32LE(4);
  const declaredLength = data.readUInt32LE(8);
  if (version !== 2) throw new Error("GLB version must be 2");
  if (declaredLength !== data.length) throw new Error("GLB declared length mismatch");

  const chunks = [];
  let offset = 12;
  let json = null;
  while (offset < data.length) {
    if (offset + 8 > data.length) throw new Error("truncated GLB chunk header");
    const length = data.readUInt32LE(offset);
    const type = data.readUInt32LE(offset + 4);
    offset += 8;
    const end = offset + length;
    if (end > data.length) throw new Error("GLB chunk exceeds file length");
    const payload = data.subarray(offset, end);
    chunks.push({ type, length });
    if (chunks.length === 1) {
      if (type !== 0x4e4f534a) throw new Error("first GLB chunk is not JSON");
      json = JSON.parse(payload.toString("utf8").replace(/[\u0000\s]+$/g, ""));
    } else if (type !== 0x004e4942) {
      throw new Error(`unexpected GLB chunk type 0x${type.toString(16)}`);
    }
    offset = end;
  }
  if (offset !== data.length) throw new Error("GLB chunk walk did not end at file length");
  if (!json) throw new Error("GLB JSON chunk missing");
  return { json, chunks };
}

function inspectProductionGlb(file, expectedRigBones) {
  const errors = [];
  const expectedBones = expectedRigBones.map(bone => bone.name);
  let gltf;
  let chunks;
  try {
    const parsed = parseGlb(file);
    gltf = parsed.json;
    chunks = parsed.chunks;
  } catch (error) {
    return { pass: false, errors: [String(error?.message || error)] };
  }

  if (gltf.asset?.version !== "2.0") {
    errors.push(`glTF asset version must be 2.0, got ${JSON.stringify(gltf.asset?.version)}`);
  }
  if (chunks.length !== 2 || chunks[0]?.type !== 0x4e4f534a || chunks[1]?.type !== 0x004e4942) {
    errors.push("production GLB must contain exactly one JSON chunk and one BIN chunk");
  }

  const buffers = gltf.buffers || [];
  if (buffers.length !== 1) errors.push(`expected exactly one embedded GLB buffer, found ${buffers.length}`);
  for (const [i, buffer] of buffers.entries()) {
    if (buffer.uri) errors.push(`buffer ${i} has external URI ${buffer.uri}`);
  }
  for (const [i, image] of (gltf.images || []).entries()) {
    if (image.uri) errors.push(`image ${i} has external URI ${image.uri}`);
  }
  if ((gltf.animations || []).length) {
    errors.push(`base production character must contain no baked animations; found ${gltf.animations.length}`);
  }

  const nodes = gltf.nodes || [];
  const nodeIndicesByName = new Map();
  for (const [index, node] of nodes.entries()) {
    if (!node.name) continue;
    if (!nodeIndicesByName.has(node.name)) nodeIndicesByName.set(node.name, []);
    nodeIndicesByName.get(node.name).push(index);
  }

  for (const bone of expectedBones) {
    const count = nodeIndicesByName.get(bone)?.length || 0;
    if (count !== 1) errors.push(`expected bone node ${bone} appears ${count} times`);
  }

  const parents = new Map();
  for (const [parentIndex, node] of nodes.entries()) {
    for (const child of node.children || []) {
      if (!Number.isInteger(child) || child < 0 || child >= nodes.length) {
        errors.push(`node ${parentIndex} has invalid child index ${child}`);
        continue;
      }
      if (parents.has(child)) errors.push(`node ${child} has multiple parents`);
      parents.set(child, parentIndex);
    }
  }

  const expectedSet = new Set(expectedBones);
  if (expectedRigBones.every(bone => (nodeIndicesByName.get(bone.name)?.length || 0) === 1)) {
    for (const bone of expectedRigBones) {
      const index = nodeIndicesByName.get(bone.name)[0];
      const parentIndex = parents.get(index);
      const actualParent = parentIndex === undefined ? null : nodes[parentIndex]?.name ?? null;
      if (bone.parent === null) {
        if (actualParent && expectedSet.has(actualParent)) {
          errors.push(`root bone ${bone.name} unexpectedly has bone parent ${actualParent}`);
        }
      } else if (actualParent !== bone.parent) {
        errors.push(`bone parent mismatch for ${bone.name}: expected ${bone.parent}, got ${actualParent}`);
      }
    }
  }

  const accessors = gltf.accessors || [];
  const skins = gltf.skins || [];
  if (skins.length !== 1) errors.push(`expected exactly one skin, found ${skins.length}`);
  for (const [i, skin] of skins.entries()) {
    const jointIndices = skin.joints || [];
    const invalidJointIndices = jointIndices.filter(
      index => !Number.isInteger(index) || index < 0 || index >= nodes.length,
    );
    if (invalidJointIndices.length) {
      errors.push(`skin ${i} has invalid joint indices: ${JSON.stringify(invalidJointIndices)}`);
    }
    const names = jointIndices.map(index => nodes[index]?.name).filter(Boolean);
    if (names.length !== expectedBones.length) {
      errors.push(`skin ${i} has ${names.length} joints, expected ${expectedBones.length}`);
    }
    const set = new Set(names);
    const missing = expectedBones.filter(name => !set.has(name));
    const extra = [...set].filter(name => !expectedSet.has(name));
    if (missing.length || extra.length) {
      errors.push(`skin ${i} joint set mismatch: missing=${JSON.stringify(missing)} extra=${JSON.stringify(extra)}`);
    }
    if (!Number.isInteger(skin.inverseBindMatrices) ||
        skin.inverseBindMatrices < 0 ||
        skin.inverseBindMatrices >= accessors.length) {
      errors.push(`skin ${i} has no valid inverseBindMatrices accessor`);
    }
  }

  const meshes = gltf.meshes || [];
  const meshNodes = nodes
    .map((node, index) => ({ node, index }))
    .filter(({ node }) => node.mesh !== undefined);
  if (!meshNodes.length) errors.push("no mesh nodes found");

  for (const { node, index } of meshNodes) {
    if (!Number.isInteger(node.skin) || node.skin < 0 || node.skin >= skins.length) {
      errors.push(`mesh node ${node.name || index} has no valid skin`);
    }
    if (!Number.isInteger(node.mesh) || node.mesh < 0 || node.mesh >= meshes.length) {
      errors.push(`mesh node ${node.name || index} references invalid mesh ${node.mesh}`);
      continue;
    }
    const mesh = meshes[node.mesh];
    const primitives = mesh.primitives || [];
    if (!primitives.length) errors.push(`mesh ${mesh.name || node.mesh} has no primitives`);
    for (const [primitiveIndex, primitive] of primitives.entries()) {
      const attrs = new Set(Object.keys(primitive.attributes || {}));
      const required = ["POSITION", "NORMAL", "JOINTS_0", "WEIGHTS_0"];
      const missing = required.filter(name => !attrs.has(name));
      if (missing.length) {
        errors.push(`mesh ${mesh.name || node.mesh} primitive ${primitiveIndex} missing attributes ${missing.join(", ")}`);
      }
    }
  }

  const text = JSON.stringify(gltf).toLowerCase();
  const legacyHits = FORBIDDEN_PRODUCTION_TOKENS.filter(token => text.includes(token));
  if (legacyHits.length) errors.push(`forbidden legacy/candidate token(s) in GLB JSON: ${legacyHits.join(", ")}`);

  return {
    pass: errors.length === 0,
    errors,
    chunkCount: chunks.length,
    nodeCount: nodes.length,
    meshNodeCount: meshNodes.length,
    skinCount: skins.length,
    imageCount: (gltf.images || []).length,
    textureCount: (gltf.textures || []).length,
    animationCount: (gltf.animations || []).length,
  };
}

export function auditOriginalV1Promotion(root = ROOT) {
  const contract = readJson(path.join(root, "ORIGINAL_V1_PROMOTION_CONTRACT.json"));
  const allowlist = readJson(path.join(root, "RELEASE_ASSET_ALLOWLIST.json"));
  const components = readJson(path.join(root, "FIRST_PARTY_COMPONENT_MANIFEST.json"));
  const rig = readJson(path.join(root, "ORIGINAL_V1_WORK", "hgpt_canonical_v4_original.json"));

  const blockers = [];
  const targets = Object.entries(contract.production_targets || {}).filter(([, value]) => value.required);
  const componentMap = new Map((components.components || []).map(item => [item.id, item]));
  const approvedPatterns = allowlist.approved_paths || [];

  const exactApproved = target => approvedPatterns.includes(target.release_path);
  const broadMatches = target =>
    approvedPatterns.filter(pattern =>
      /[*?]/.test(pattern) && globRegex(pattern).test(target.release_path),
    );

  if (contract.mode === "blocked_pending_approval") {
    if (contract.source_track?.approved_source_commit !== null) {
      blockers.push("blocked contract must not pin an approved source commit");
    }

    for (const [variant, target] of targets) {
      if (target.sha256 !== null) {
        blockers.push(`${variant}: blocked contract must not pin a production SHA-256`);
      }
      const file = path.join(root, target.repository_path);
      if (fs.existsSync(file)) {
        blockers.push(`${variant}: production target exists before approval: ${target.repository_path}`);
      }
      if (exactApproved(target) || broadMatches(target).length) {
        blockers.push(`${variant}: release allowlist already permits the unapproved target`);
      }
    }

    for (const id of REQUIRED_COMPONENTS) {
      if (componentMap.get(id)?.status === "first_party_approved") {
        blockers.push(`${id}: cannot be first_party_approved while promotion is blocked`);
      }
    }

    if (FINAL_GATE_VALUES.has(contract.required_gates?.explicit_production_approval)) {
      blockers.push("explicit production approval cannot be final while promotion is blocked");
    }

    return {
      schemaVersion: 1,
      mode: contract.mode,
      pass: blockers.length === 0,
      expectedBlockedState: true,
      blockers,
      productionTargetsPresent: targets.filter(([, target]) =>
        fs.existsSync(path.join(root, target.repository_path)),
      ).map(([variant]) => variant),
      note: "Blocked-state guard: exact production assets, hashes, allowlist entries and component approvals must remain absent until explicit approval.",
    };
  }

  if (contract.mode !== "approved_for_promotion") {
    blockers.push(`unsupported promotion mode ${JSON.stringify(contract.mode)}`);
  }

  const commit = contract.source_track?.approved_source_commit;
  if (typeof commit !== "string" || !/^[0-9a-f]{40}$/i.test(commit)) {
    blockers.push("approved_source_commit must be one exact 40-hex commit");
  }

  for (const [gate, value] of Object.entries(contract.required_gates || {})) {
    if (!FINAL_GATE_VALUES.has(value)) {
      blockers.push(`gate ${gate} is not final: ${JSON.stringify(value)}`);
    }
  }

  const expectedBones = (rig.bones || []).map(bone => bone.name);
  if (rig.identity !== contract.rig_id || expectedBones.length !== 63) {
    blockers.push("canonical v4 rig payload does not match contract identity/63-bone target");
  }

  const auditedTargets = [];
  for (const [variant, target] of targets) {
    const lowerName = path.basename(target.repository_path).toLowerCase();
    const nameHits = FORBIDDEN_PRODUCTION_TOKENS.filter(token => lowerName.includes(token));
    if (nameHits.length) {
      blockers.push(`${variant}: forbidden production filename token(s): ${nameHits.join(", ")}`);
    }

    if (typeof target.sha256 !== "string" || !/^[0-9a-f]{64}$/i.test(target.sha256)) {
      blockers.push(`${variant}: missing exact 64-hex production SHA-256`);
      continue;
    }

    const file = path.join(root, target.repository_path);
    if (!fs.existsSync(file)) {
      blockers.push(`${variant}: missing production target ${target.repository_path}`);
      continue;
    }

    const actual = sha256(file);
    if (actual !== target.sha256.toLowerCase()) {
      blockers.push(`${variant}: SHA-256 mismatch; expected ${target.sha256}, got ${actual}`);
    }

    if (!exactApproved(target)) {
      blockers.push(`${variant}: release allowlist lacks exact path ${target.release_path}`);
    }
    const broad = broadMatches(target);
    if (broad.length) {
      blockers.push(`${variant}: broad allowlist pattern(s) match production target: ${broad.join(", ")}`);
    }

    const glb = inspectProductionGlb(file, rig.bones || []);
    if (!glb.pass) {
      blockers.push(...glb.errors.map(error => `${variant}: ${error}`));
    }
    auditedTargets.push({
      variant,
      repositoryPath: target.repository_path,
      releasePath: target.release_path,
      sha256: actual,
      glb,
    });
  }

  for (const id of REQUIRED_COMPONENTS) {
    const component = componentMap.get(id);
    if (!component) blockers.push(`missing required component ${id}`);
    else if (component.status !== "first_party_approved") {
      blockers.push(`${id} is not first_party_approved: ${component.status}`);
    }
  }

  return {
    schemaVersion: 1,
    mode: contract.mode,
    pass: blockers.length === 0,
    expectedBlockedState: false,
    blockers,
    approvedSourceCommit: commit,
    auditedTargets,
    note: "Approved-mode guard: exact source commit, final gate statuses, hashes, self-contained GLBs, exact allowlist paths and approved components are all mandatory.",
  };
}

function main() {
  const expectBlocked = process.argv.includes("--expect-blocked");
  const result = auditOriginalV1Promotion(ROOT);
  fs.mkdirSync(path.join(ROOT, "reports"), { recursive: true });
  fs.writeFileSync(
    path.join(ROOT, "reports", "original_v1_promotion_audit.json"),
    JSON.stringify(result, null, 2) + "\n",
  );
  console.log(JSON.stringify(result, null, 2));

  if (expectBlocked) {
    process.exit(result.pass && result.expectedBlockedState ? 0 : 1);
  }
  process.exit(result.pass && !result.expectedBlockedState ? 0 : 1);
}

const invoked = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) main();
