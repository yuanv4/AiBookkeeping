@echo off
REM Prisma 客户端生成优化脚本
REM 用于 Windows 环境,避免文件锁定问题

echo ========================================
echo   Prisma 客户端生成脚本
echo ========================================
echo.

REM 检查是否有 node 进程正在运行
echo [1/4] 检查 Node 进程...
tasklist /FI "IMAGENAME eq node.exe" 2>NUL | find /I /N "node.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo 警告: 检测到 Node 进程正在运行
    echo 建议先关闭所有 Node 进程以避免文件锁定问题
    echo.
    set /p CONTINUE="是否继续? (Y/N): "
    if /I not "%CONTINUE%"=="Y" (
        echo 操作已取消
        exit /b 1
    )
) else (
    echo 未检测到运行中的 Node 进程
)
echo.

REM 清理旧的 Prisma 客户端
echo [2/4] 清理旧的 Prisma 客户端...
if exist "node_modules\.prisma" (
    rmdir /s /q "node_modules\.prisma"
    echo 已删除 node_modules\.prisma
)
if exist "node_modules\@prisma\client" (
    rmdir /s /q "node_modules\@prisma\client"
    echo 已删除 node_modules\@prisma\client
)
echo.

REM 重新安装依赖
echo [3/4] 重新安装 Prisma 客户端...
call npm install @prisma/prisma --save-dev
if %errorlevel% neq 0 (
    echo 错误: npm install 失败
    exit /b 1
)
echo.

REM 生成 Prisma 客户端
echo [4/4] 生成 Prisma 客户端...
call npx prisma generate
if %errorlevel% neq 0 (
    echo 错误: prisma generate 失败
    exit /b 1
)
echo.

REM 推送数据库 schema
echo [额外] 推送数据库 schema (可选)...
set /p PUSH_DB="是否推送数据库 schema? (Y/N): "
if /I "%PUSH_DB%"=="Y" (
    call npx prisma db push
    if %errorlevel% neq 0 (
        echo 警告: prisma db push 失败,但不影响客户端使用
    )
)
echo.

echo ========================================
echo   ✅ Prisma 客户端生成完成!
echo ========================================
pause
