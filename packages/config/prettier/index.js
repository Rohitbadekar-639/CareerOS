/**
 * Shared Prettier options for all CareerOS JS/TS packages.
 * Consume via `"prettier": "@career-os/config/prettier"` in package.json.
 * printWidth matches the Python line-length (ruff, root pyproject.toml).
 */
export default {
  printWidth: 100,
  endOfLine: "lf",
};
