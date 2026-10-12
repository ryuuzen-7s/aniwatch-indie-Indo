@echo off
REM ============================================================
REM  AniWatch Agent - Hourly (skip ongoing)
REM ============================================================

cd /d "%~dp0"
cd ..

if not exist "agent\logs" mkdir "agent\logs"

set LOG_FILE=agent\logs\hourly_%date:~-4%%date:~3,2%%date:~0,2%.log
set LOG_FILE=%LOG_FILE: =_%

echo ============================================================ >> "%LOG_FILE%"
echo   AniWatch Agent Hourly - %date% %time% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

python agent\coordinator.py --once --skip-ongoing >> "%LOG_FILE%" 2>&1

set EXITCODE=%errorlevel%

echo. >> "%LOG_FILE%"
echo Exit code: %EXITCODE% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

exit /b %EXITCODE%