import assert from "node:assert/strict";
import crypto from "node:crypto";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { auditOriginalV1Promotion } from "./audit-original-v1-promotion.mjs";

const ROOT = resolve(".");

function copyJson(from, to) {
  mkdirSync(dirname(to), { recursive: true });
  writeFileSync(to, readFileSync(from));
}

function writeJson(file, value) {
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, JSON.stringify(value, null, 2) + "\n");
}

function fileSha256(file) {
  return crypto.createHash("sha256").update(readFileSync(file)).digest("hex");
}

function makeBlockedFixture() {
  const root = mkdtempSync(join(tmpdir(), "hgpt-original-promotion-"));
  copyJson(
    join(ROOT, "ORIGINAL_V1_PROMOTION_CONTRACT.json"),
    join(root, "ORIGINAL_V1_PROMOTION_CONTRACT.json"),
  );
  copyJson(
    join(ROOT, "RELEASE_ASSET_ALLOWLIST.json"),
    join(root, "RELEASE_ASSET_ALLOWLIST.json"),
  );
  copyJson(
    join(ROOT, "FIRST_PARTY_COMPONENT_MANIFEST.json"),
    join(root, "FIRST_PARTY_COMPONENT_MANIFEST.json"),
  );
  copyJson(
    join(ROOT, "ORIGINAL_V1_WORK", "hgpt_canonical_v4_original.json"),
    join(root, "ORIGINAL_V1_WORK", "hgpt_canonical_v4_original.json"),
  );
  return root;
}

function makeMinimalRigGlb(rig, hierarchyMutation = null) {
  const bones = rig.bones.map(bone => ({ ...bone }));
  if (hierarchyMutation) hierarchyMutation(bones);

  const indexByName = new Map(bones.map((bone, index) => [bone.name, index]));
  const nodes = bones.map(bone => ({ name: bone.name }));
  for (const [index, bone] of bones.entries()) {
    if (bone.parent === null) continue;
    const parentIndex = indexByName.get(bone.parent);
    if (parentIndex === undefined) throw new Error(`unknown parent ${bone.parent}`);
    nodes[parentIndex].children ||= [];
    nodes[parentIndex].children.push(index);
  }

  const gltf = {
    asset: { version: "2.0", generator: "HomeGymPT promotion gate test fixture" },
    scene: 0,
    scenes: [{ nodes: [indexByName.get("root")] }],
    nodes,
    skins: [{ joints: bones.map((_bone, index) => index) }],
  };

  const raw = Buffer.from(JSON.stringify(gltf), "utf8");
  const paddedLength = Math.ceil(raw.length / 4) * 4;
  const jsonChunk = Buffer.alloc(paddedLength, 0x20);
  raw.copy(jsonChunk);

  const header = Buffer.alloc(12);
  header.write("glTF", 0, 4, "ascii");
  header.writeUInt32LE(2, 4);
  header.writeUInt32LE(12 + 8 + jsonChunk.length, 8);

  const chunkHeader = Buffer.alloc(8);
  chunkHeader.writeUInt32LE(jsonChunk.length, 0);
  chunkHeader.writeUInt32LE(0x4e4f534a, 4);

  return Buffer.concat([header, chunkHeader, jsonChunk]);
}

function makeApprovedFixture() {
  const root = makeBlockedFixture();
  const contractPath = join(root, "ORIGINAL_V1_PROMOTION_CONTRACT.json");
  const allowlistPath = join(root, "RELEASE_ASSET_ALLOWLIST.json");
  const componentsPath = join(root, "FIRST_PARTY_COMPONENT_MANIFEST.json");
  const rig = JSON.parse(
    readFileSync(join(root, "ORIGINAL_V1_WORK", "hgpt_canonical_v4_original.json"), "utf8"),
  );

  const contract = JSON.parse(readFileSync(contractPath, "utf8"));
  contract.mode = "approved_for_promotion";
  contract.source_track.approved_source_commit = "a".repeat(40);
  for (const gate of Object.keys(contract.required_gates)) {
    contract.required_gates[gate] = "approved";
  }

  for (const target of Object.values(contract.production_targets)) {
    const file = join(root, target.repository_path);
    mkdirSync(dirname(file), { recursive: true });
    writeFileSync(file, makeMinimalRigGlb(rig));
    target.sha256 = fileSha256(file);
  }
  writeJson(contractPath, contract);

  const allowlist = JSON.parse(readFileSync(allowlistPath, "utf8"));
  allowlist.approved_paths = Object.values(contract.production_targets).map(
    target => target.release_path,
  );
  writeJson(allowlistPath, allowlist);

  const components = JSON.parse(readFileSync(componentsPath, "utf8"));
  for (const component of components.components) {
    if (["male_character", "male_shorts", "canonical_rig"].includes(component.id)) {
      component.status = "first_party_approved";
    }
  }
  writeJson(componentsPath, components);

  return { root, contractPath, rig };
}

test("current standalone repo keeps ORIGINAL v1 promotion correctly blocked", () => {
  const result = auditOriginalV1Promotion(ROOT);
  assert.equal(result.pass, true, JSON.stringify(result, null, 2));
  assert.equal(result.expectedBlockedState, true);
  assert.deepEqual(result.productionTargetsPresent, []);
  assert.deepEqual(result.blockers, []);
});

test("blocked promotion state rejects a premature production asset", () => {
  const root = makeBlockedFixture();
  try {
    const target = join(root, "public", "characters", "HomeGymPT_Male_ORIGINAL_v1.glb");
    mkdirSync(dirname(target), { recursive: true });
    writeFileSync(target, Buffer.from("not approved"));

    const result = auditOriginalV1Promotion(root);
    assert.equal(result.pass, false);
    assert.equal(result.expectedBlockedState, true);
    assert.ok(
      result.blockers.some(message => message.includes("production target exists before approval")),
      JSON.stringify(result, null, 2),
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("blocked promotion state rejects exact or broad premature allowlisting", () => {
  const root = makeBlockedFixture();
  try {
    const allowlistPath = join(root, "RELEASE_ASSET_ALLOWLIST.json");
    const allowlist = JSON.parse(readFileSync(allowlistPath, "utf8"));
    allowlist.approved_paths = [
      "characters/HomeGymPT_Male_ORIGINAL_v1.glb",
      "characters/*.glb",
    ];
    writeJson(allowlistPath, allowlist);

    const result = auditOriginalV1Promotion(root);
    assert.equal(result.pass, false);
    assert.ok(
      result.blockers.some(message => message.includes("release allowlist already permits the unapproved target")),
      JSON.stringify(result, null, 2),
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("blocked promotion state rejects premature component approval", () => {
  const root = makeBlockedFixture();
  try {
    const componentsPath = join(root, "FIRST_PARTY_COMPONENT_MANIFEST.json");
    const components = JSON.parse(readFileSync(componentsPath, "utf8"));
    for (const component of components.components) {
      if (["male_character", "male_shorts", "canonical_rig"].includes(component.id)) {
        component.status = "first_party_approved";
      }
    }
    writeJson(componentsPath, components);

    const result = auditOriginalV1Promotion(root);
    assert.equal(result.pass, false);
    for (const id of ["male_character", "male_shorts", "canonical_rig"]) {
      assert.ok(
        result.blockers.some(message => message.startsWith(id + ": cannot be first_party_approved")),
        JSON.stringify(result, null, 2),
      );
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("approved promotion mode requires the complete exact contract and canonical hierarchy", () => {
  const { root } = makeApprovedFixture();
  try {
    const result = auditOriginalV1Promotion(root);
    assert.equal(result.pass, true, JSON.stringify(result, null, 2));
    assert.equal(result.expectedBlockedState, false);
    assert.equal(result.auditedTargets.length, 2);
    assert.ok(result.auditedTargets.every(target => target.glb.pass));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("approved promotion mode rejects a production hash mismatch", () => {
  const { root, contractPath } = makeApprovedFixture();
  try {
    const contract = JSON.parse(readFileSync(contractPath, "utf8"));
    contract.production_targets.bare.sha256 = "0".repeat(64);
    writeJson(contractPath, contract);

    const result = auditOriginalV1Promotion(root);
    assert.equal(result.pass, false);
    assert.ok(
      result.blockers.some(message => message.startsWith("bare: SHA-256 mismatch")),
      JSON.stringify(result, null, 2),
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("approved promotion mode rejects a wrong canonical bone parent", () => {
  const { root, contractPath, rig } = makeApprovedFixture();
  try {
    const contract = JSON.parse(readFileSync(contractPath, "utf8"));
    const bare = contract.production_targets.bare;
    const file = join(root, bare.repository_path);

    writeFileSync(
      file,
      makeMinimalRigGlb(rig, bones => {
        const forearm = bones.find(bone => bone.name === "forearm_l");
        forearm.parent = "clavicle_l";
      }),
    );
    bare.sha256 = fileSha256(file);
    writeJson(contractPath, contract);

    const result = auditOriginalV1Promotion(root);
    assert.equal(result.pass, false);
    assert.ok(
      result.blockers.some(message =>
        message.includes("bone parent mismatch for forearm_l"),
      ),
      JSON.stringify(result, null, 2),
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
