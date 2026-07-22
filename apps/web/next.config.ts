import type { NextConfig } from "next";

// `standalone` emits a self-contained server bundle for a minimal runtime image
// (M0-T13). Production web is deployed on Vercel; this powers the local container.
const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@career-os/sdk"],
};

export default nextConfig;
