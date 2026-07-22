import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pin the Turbopack workspace root to this app. The repo has lockfiles at
  // both the root and apps/web, which otherwise makes Next infer the root
  // ambiguously (and warn on dev/build/Vercel).
  turbopack: { root: __dirname },
};

export default nextConfig;
