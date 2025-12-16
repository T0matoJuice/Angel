@echo off
echo ========================================
echo   LLM 智能检测系统 - 启动脚本
echo ========================================
echo.

echo [1/2] 启动 Flask 后端服务器 (端口 5000)...
start "Flask Backend" cmd /k "cd LLM_Detection_System && python app.py"

timeout /t 3 /nobreak >nul

echo [2/2] 启动 Vue 前端开发服务器 (端口 5173)...
start "Vue Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   服务启动完成！
echo ========================================
echo.
echo   前端地址: http://localhost:5173
echo   后端地址: http://localhost:5000
echo.
echo   按任意键关闭此窗口...
pause >nul
