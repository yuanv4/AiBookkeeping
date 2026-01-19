import path from "path";
import { PrismaBetterSqlite3 } from "@prisma/adapter-better-sqlite3";
import { PrismaClient } from "@/generated/prisma/client";

// 数据库版本标记，用于强制重建客户端
const DB_VERSION = "v7";

// 防止开发模式下热重载创建多个实例
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
  prismaVersion: string | undefined;
};

function createPrismaClient(): PrismaClient {
  // 使用 process.cwd() 获取项目根目录
  const cwd = process.cwd();
  const dbUrl = resolveDatabaseUrl(cwd);
  
  console.log("[Prisma] Initializing with database:", dbUrl);
  
  // 创建适配器（传入配置对象，而不是 Database 实例）
  const adapter = new PrismaBetterSqlite3({ url: dbUrl });
  return new PrismaClient({ adapter });
}

function normalizeFileUrl(rawUrl: string, cwd: string): string {
  if (!rawUrl.startsWith("file:")) {
    return rawUrl;
  }

  const pathPart = rawUrl.slice(5);
  if (pathPart.startsWith("./") || pathPart.startsWith("../")) {
    const absPath = path.resolve(cwd, pathPart);
    return `file:${absPath.replace(/\\/g, "/")}`;
  }

  if (/^\/[A-Za-z]:\//.test(pathPart)) {
    return `file:${pathPart.slice(1)}`;
  }

  return rawUrl;
}

function resolveDatabaseUrl(cwd: string): string {
  const defaultDbPath = path.join(cwd, "dev.db");
  const envDbUrl = process.env.DATABASE_URL;
  // 适配器需要 file: URL 格式，支持相对路径配置
  if (envDbUrl) {
    return normalizeFileUrl(envDbUrl, cwd);
  }
  return `file:${defaultDbPath.replace(/\\/g, "/")}`;
}

// 如果版本不匹配，强制重建客户端
if (globalForPrisma.prismaVersion !== DB_VERSION) {
  globalForPrisma.prisma = undefined;
  globalForPrisma.prismaVersion = DB_VERSION;
}

export const prisma = globalForPrisma.prisma ?? createPrismaClient();

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}

export default prisma;
