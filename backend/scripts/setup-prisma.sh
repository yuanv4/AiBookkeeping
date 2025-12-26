#!/bin/bash
# Prisma 客户端生成优化脚本
# 用于 Linux/Mac 环境

set -e

echo "========================================"
echo "  Prisma 客户端生成脚本"
echo "========================================"
echo ""

# 检查是否有 node 进程正在运行
echo "[1/4] 检查 Node 进程..."
if pgrep -x "node" > /dev/null; then
    echo "警告: 检测到 Node 进程正在运行"
    echo "建议先关闭所有 Node 进程以避免文件锁定问题"
    echo ""
    read -p "是否继续? (Y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "操作已取消"
        exit 1
    fi
else
    echo "未检测到运行中的 Node 进程"
fi
echo ""

# 清理旧的 Prisma 客户端
echo "[2/4] 清理旧的 Prisma 客户端..."
rm -rf node_modules/.prisma
rm -rf node_modules/@prisma/client
echo "已清理旧的 Prisma 客户端"
echo ""

# 重新安装依赖
echo "[3/4] 重新安装 Prisma 客户端..."
npm install @prisma/prisma --save-dev
echo ""

# 生成 Prisma 客户端
echo "[4/4] 生成 Prisma 客户端..."
npx prisma generate
echo ""

# 推送数据库 schema (可选)
echo "[额外] 推送数据库 schema (可选)..."
read -p "是否推送数据库 schema? (Y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npx prisma db push
fi
echo ""

echo "========================================"
echo "  ✅ Prisma 客户端生成完成!"
echo "========================================"
