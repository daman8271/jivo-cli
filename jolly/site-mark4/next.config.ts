import type { NextConfig } from "next";
import path from "node:path";

// Pin the workspace root to this folder. A stray package-lock.json in the home
// directory otherwise makes Next infer ~/ as the root and trace files from
// there. (Same fix as the August and Mark 2 sites.)
const root = path.resolve(process.cwd());

const nextConfig: NextConfig = {
  turbopack: { root },
  outputFileTracingRoot: root,
};

export default nextConfig;
