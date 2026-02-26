@echo off
chcp 65001 >nul
echo ============================================
echo    智慧餐饮结算系统 - 本地启动脚本
echo ============================================
echo.

:: 启动后端
echo [1/2] 正在启动后端服务 (端口 8000)...
start "Smart-Dining-Backend" cmd /k "cd /d %~dp0smart-dining-backend && uvicorn main:app --reload --port 8000"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端
echo [2/2] 正在启动前端服务 (端口 5173)...
start "Smart-Dining-Frontend" cmd /k "cd /d %~dp0smart-dining-frontend && npm run dev"

echo.
echo ============================================
echo    启动完成！
echo ============================================
echo.
echo    后端地址: http://localhost:8000
echo    前端地址: http://localhost:5173
echo    API文档:  http://localhost:8000/docs
echo.
echo    按任意键关闭此窗口...
pause >nul
