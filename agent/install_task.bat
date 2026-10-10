@echo off
REM ============================================================
REM  Register AniWatch Agent ke Windows Task Scheduler
REM  Harus dijalankan sebagai Administrator!
REM ============================================================

cd /d "%~dp0"

echo ============================================================
echo   INSTALL TASK - AniWatch Agent
echo ============================================================
echo.
echo   Task name : AniWatchAgent
echo   Schedule  : Setiap 6 jam
echo   Action    : %~dp0cron_daily.bat
echo.

REM Hapus task lama kalau ada
schtasks /Delete /TN "AniWatchAgent" /F >nul 2>&1

REM Register task baru (setiap 6 jam)
schtasks /Create ^
    /TN "AniWatchAgent" ^
    /TR "%~dp0cron_daily.bat" ^
    /SC HOURLY ^
    /MO 6 ^
    /RL HIGHEST ^
    /F

if %errorlevel% == 0 (
    echo.
    echo   OK - Task berhasil didaftarkan
    echo.
    echo   Cek dengan: schtasks /Query /TN "AniWatchAgent"
) else (
    echo.
    echo   GAGAL - Pastikan jalankan sebagai Administrator
)

echo.
pause