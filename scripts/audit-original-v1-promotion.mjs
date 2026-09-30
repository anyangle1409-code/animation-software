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

  const jsonLength = data.readUInt32LE(12);
  const jsonType = data.readUInt32LE(16);
  if (jsonType !== 0x4e4f534a) throw new Error("first GLB chunk is not JSON");
  const json = JSON.parse(
    data.subarray(20, 20 + jsonLength).toString("utf8").replace(/[\u0000\s]+$/g, ""),
  );
  return json;
}

function inspectProductionGlb(file, expectedBones) {
  const errors = [];
  let gltf;
  try {
    gltf = parseGlb(file);
  } catch (error) {
    return { pass: false, errors: [String(error?.message || error)] };
  }

  for (const [i, buffer] of (gltf.buffers || []).entries()) {
    if (buffer.uri) errors.push(`buffer ${i} has URI ${buffer.uri}`);
  }
  for (const [i, image] of (gltf.images || []).entries()) {
    if (image.uri) errors.push(`image ${i} has URI ${image.uri}`);
  }

  const nodeNames = new Set((gltf.nodes || []).map(node => node.name).filter(Boolean));
  for (const bone of expectedBones) {
    if (!nodeNames.has(bone)) errors.push(`missing expected bone node ${bone}`);
  }

  const skins = gltf.skins || [];
  if (skins.length < 1) errors.push("no skin found");
  const expectedSet = new Set(expectedBones);
  for (const [i, skin] of skins.entries()) {
    const names = (skin.joints || []).map(index => gltf.nodes?.[index]?.name).filter(Boolean);
    if (names.length !== expectedBones.length) {
      errors.push(`skin ${i} has ${names.length} joints, expected ${expectedBones.length}`);
    }
    const set = new Set(names);
    const missing = expectedBones.filter(name => !set.has(name));
    const extra = [...set].filter(name => !expectedSet.has(name));
    if (missing.length || extra.length) {
      errors.push(`skin ${i} joint set mismatch: missing=${JSON.stringify(missing)} extra=${JSON.stringify(extra)}`);
    }
  }

  const text = JSON.stringify(gltf).toLowerCase();
  const legacyHits = FORBIDDEN_PRODUCTION_TOKENS.filter(token => text.includes(token));
  if (legacyHits.length) errors.push(`forbidden legacy/candidate token(s) in GLB JSON: ${legacyHits.join(", ")}`);

  return {
    pass: errors.length === 0,
    errors,
    nodeCount: (gltf.nodes || []).length,
    skinCount: skins.length,
    imageCount: (gltf.images || []).length,
    textureCount: (gltf.textures || []).length,
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

    const glb = inspectProductionGlb(file, expectedBones);
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
