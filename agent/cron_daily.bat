@echo off
REM ============================================================
REM  AniWatch Agent - Daily Hybrid Scrape (Task Scheduler)
REM ============================================================

cd /d "%~dp0"
cd ..

REM ─── Buat folder log kalau belum ada ───
if not exist "agent\logs" mkdir "agent\logs"

REM ─── Log file dengan tanggal ───
set LOG_FILE=agent\logs\task_%date:~-4%%date:~3,2%%date:~0,2%.log
set LOG_FILE=%LOG_FILE: =_%

echo ============================================================ >> "%LOG_FILE%"
echo   AniWatch Agent - %date% %time% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

REM ─── Jalankan coordinator (hybrid mode) ───
python agent\coordinator.py --once >> "%LOG_FILE%" 2>&1

set EXITCODE=%errorlevel%

echo. >> "%LOG_FILE%"
echo Exit code: %EXITCODE% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

exit /b %EXITCODE%