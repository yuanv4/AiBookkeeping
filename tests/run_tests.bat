@echo off
echo ======================================================
echo 开始运行测试
echo ======================================================
echo.

echo --- 运行单元测试 ---
python -m tests.unit.test_bank_detection
echo.

echo --- 运行集成测试 ---
python -m tests.integration.test_load_csv
python -m tests.integration.test_generate_analysis
echo.

echo ======================================================
echo 所有测试运行完成
echo ======================================================
pause 