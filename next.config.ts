import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 启用服务端组件中的实验性功能
  experimental: {
    serverComponentsExternalPackages: ["pdf-parse", "better-sqlite3"],
  },
  // 允许上传较大文件和原生模块
  serverExternalPackages: ["xlsx", "better-sqlite3"],
};

export default nextConfig;
