# @career-os/config

Shared tooling presets for all CareerOS JS/TS workspace packages (Technical Architecture §1).
No runtime code lives here — only configuration.

## Consuming

Add the workspace dependency plus the peer tools:

```jsonc
// package.json
{
  "devDependencies": {
    "@career-os/config": "workspace:*",
    "eslint": "^10.0.0",
    "prettier": "^3.0.0",
    "typescript": ">=5.9.0 <6.1.0" // upper bound set by typescript-eslint
  },
  "prettier": "@career-os/config/prettier"
}
```

```jsonc
// tsconfig.json
{
  "extends": "@career-os/config/typescript/base.json",
  "include": ["src"]
}
```

```js
// eslint.config.js
import base from "@career-os/config/eslint/base";

export default base;
```

```css
/* app stylesheet (Tailwind v4, CSS-first) */
@import "tailwindcss";
@import "@career-os/config/tailwind";
```

## Notes

- The TS base is strict (`strict`, `noUncheckedIndexedAccess`, `noImplicitOverride`,
  `verbatimModuleSyntax`) and `noEmit`; packages that emit override `noEmit`/`outDir`.
- ESLint is a flat config with type-aware rules via the project service; plain `.js`
  config files are exempted from type checking.
- The Tailwind preset is an importable CSS `@theme` file (v4 idiom); tokens arrive
  with `packages/ui`.
