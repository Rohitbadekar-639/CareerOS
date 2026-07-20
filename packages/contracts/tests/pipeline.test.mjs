import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const pkgRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

test("openapi.json documents health endpoints", () => {
  const doc = JSON.parse(readFileSync(path.join(pkgRoot, "openapi.json"), "utf8"));
  assert.equal(typeof doc.openapi, "string");
  assert.ok(doc.paths["/healthz"], "expected /healthz in OpenAPI paths");
  assert.ok(doc.paths["/readyz"], "expected /readyz in OpenAPI paths");
});

test("generate script exits successfully", () => {
  const result = spawnSync(process.execPath, ["scripts/generate.mjs"], {
    cwd: pkgRoot,
    encoding: "utf8",
    shell: false,
  });
  assert.equal(result.status, 0, result.stderr || result.stdout);
});
