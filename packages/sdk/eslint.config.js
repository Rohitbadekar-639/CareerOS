import base from "@career-os/config/eslint/base";

export default [
  ...base,
  {
    ignores: ["tests/**", "vitest.config.ts"],
  },
];
