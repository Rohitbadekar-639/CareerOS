import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import tseslint from "typescript-eslint";

/**
 * Base flat ESLint config for all CareerOS TS packages.
 * Type-aware rules use the project service, so consumers only need a
 * tsconfig.json next to their eslint.config.js.
 */
export default tseslint.config(
  { ignores: ["node_modules/", "dist/", "build/", ".next/", "coverage/", ".turbo/"] },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
      },
    },
  },
  {
    files: ["**/*.js", "**/*.mjs", "**/*.cjs"],
    ...tseslint.configs.disableTypeChecked,
  },
  prettier,
);
