@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   智能餐饮系统 - Git 一键提交推送
echo ========================================
echo.

:: 获取当前时间作为默认提交信息
set "DEFAULT_MSG=更新于 %date% %time:~0,8%"

:: 让用户输入提交信息（直接回车则用默认信息）
set /p "MSG=请输入提交说明（直接回车使用默认）: "
if "%MSG%"=="" set "MSG=%DEFAULT_MSG%"

echo.
echo [1/3] 添加所有更改...
git add .

echo [2/3] 提交: %MSG%
git commit -m "%MSG%"

echo [3/3] 推送到远程仓库...
git push

echo.
echo ========================================
echo   完成！
echo ========================================
pause
