import { defineConfig } from "vitest/config";

export default defineConfig({
  // Next.js needs "jsx": "preserve" in tsconfig; tell Vite (oxc) to transform JSX itself.
  oxc: { jsx: { runtime: "automatic" } },
  test: {
    environment: "node",
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});
