@echo off
chcp 65001 >nul
title TripAI 后端服务 (端口 8000)
cd /d "E:\TripAI\backend"
echo.
echo 正在启动 TripAI 后端服务...
echo 看到 "Application startup complete" 即启动成功。
echo 关闭本窗口 = 停止后端服务。
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
