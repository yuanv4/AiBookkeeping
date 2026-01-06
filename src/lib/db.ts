import { PrismaClient } from "@/generated/prisma/client";
import { PrismaBetterSqlite3 } from "@prisma/adapter-better-sqlite3";
import path from "path";

// 数据库版本标记，用于强制重建客户端
const DB_VERSION = "v6";

// 防止开发模式下热重载创建多个实例
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
  prismaVersion: string | undefined;
};

function createPrismaClient(): PrismaClient {
  // 使用 process.cwd() 获取项目根目录
  const cwd = process.cwd();
  const dbPath = path.join(cwd, "dev.db");
  // 适配器需要 file: URL 格式
  const dbUrl = `file:${dbPath.replace(/\\/g, "/")}`;
  
  console.log("[Prisma] Initializing with database:", dbUrl);
  
  // 创建适配器（传入配置对象，而不是 Database 实例）
  const adapter = new PrismaBetterSqlite3({ url: dbUrl });
  return new PrismaClient({ adapter });
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
