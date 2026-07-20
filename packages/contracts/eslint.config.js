import base from "@career-os/config/eslint/base";

export default [
  ...base,
  {
    ignores: ["src/types.ts", "src/schemas.ts", "scripts/**", "tests/**"],
  },
];
