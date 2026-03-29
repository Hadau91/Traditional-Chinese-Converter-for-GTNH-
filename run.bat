@echo off
chcp 65001
title GTNH 簡轉繁工具

echo ================================
echo   GTNH 簡體轉繁體工具
echo ================================
echo.

set /p target=請輸入 GTNH 資料夾路徑:

if not exist "%target%" (
    echo 路徑不存在！
    pause
    exit
)

python convert.py "%target%"

echo.
echo 轉換完成！
pause