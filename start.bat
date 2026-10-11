@echo off
title AniWatch Launcher
cd /d "%~dp0"

echo ============================================================
echo   ANIWATCH — LAUNCHER
echo ============================================================
echo.

:: 1. Server
echo [1/3] Starting Server...
start "AniWatch Server" cmd /k "cd /d %~dp0 && uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning"

timeout /t 5 /nobreak >nul

:: 2. ZROK
echo [2/3] Starting ZROK...
start "AniWatch ZROK" cmd /k "zrok share reserved aniwatch"

timeout /t 2 /nobreak >nul

:: 3. Agent (opsional — comment kalau tidak butuh)
echo [3/3] Starting Agent...
start "AniWatch Agent" cmd /k "cd /d %~dp0 && python agent\cron.py"

echo.
echo ============================================================
echo   SEMUA JALAN
echo ============================================================
echo   Local  : http://localhost:8000
echo   Public : https://aniwatch.share.zrok.io
echo   Docs   : http://localhost:8000/docs
echo ============================================================
pause