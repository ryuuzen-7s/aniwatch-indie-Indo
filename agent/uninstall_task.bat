@echo off
REM ============================================================
REM  Unregister AniWatch Agent dari Windows Task Scheduler
REM  Harus dijalankan sebagai Administrator!
REM ============================================================

echo ============================================================
echo   UNINSTALL TASK - AniWatch Agent
echo ============================================================
echo.

echo   Menghapus task "AniWatchAgent"...
schtasks /Delete /TN "AniWatchAgent" /F

if %errorlevel% == 0 (
    echo.
    echo   OK - Task berhasil dihapus
) else (
    echo.
    echo   GAGAL atau task tidak ada
    echo   Cek dengan: schtasks /Query /TN "AniWatchAgent"
)

echo.
pause