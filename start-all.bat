@echo off
chcp 65001 >nul
echo 正在启动 TripAI 前后端服务（各开一个窗口）...
start "TripAI 后端 (8000)" cmd /k "chcp 65001 >nul && cd /d E:\TripAI\backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
start "TripAI 前端 (3000)" cmd /k "chcp 65001 >nul && cd /d E:\TripAI\frontend && npm run dev -- -H 0.0.0.0"
echo.
echo 两个服务窗口已打开，等前端窗口出现 "Ready" 即可访问：
echo   电脑： http://localhost:3000
echo   手机： http://192.168.31.67:3000
echo.
timeout /t 3 >nul
