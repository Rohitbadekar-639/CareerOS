/**
 * Fail if committed contracts output is stale relative to the api OpenAPI.
 * Used by CI (T15 acceptance) and locally via `pnpm contracts:check`.
 */
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const pkgRoot = path.resolve(here, "..");
const repoRoot = path.resolve(pkgRoot, "../..");

execFileSync("node", [path.join(here, "generate.mjs")], {
  cwd: pkgRoot,
  stdio: "inherit",
  shell: false,
});

try {
  execFileSync(
    "git",
    [
      "diff",
      "--exit-code",
      "--",
      "packages/contracts/openapi.json",
      "packages/contracts/src",
    ],
    { cwd: repoRoot, stdio: "inherit", shell: false },
  );
} catch {
  console.error(
    "contracts:check failed — generated output differs from the commit. " +
      "Run `pnpm contracts:generate` and commit the result.",
  );
  process.exit(1);
}

console.log("contracts:check passed — committed output is up to date.");
