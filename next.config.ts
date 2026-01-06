import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 服务端外部包（Node.js 原生模块）
  serverExternalPackages: ["pdf-parse", "xlsx", "better-sqlite3"],
};

export default nextConfig;
