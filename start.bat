@echo off
title AniWatch Launcher
cd /d "%~dp0"

echo ============================================================
echo   ANIWATCH LAUNCHER
echo   Membuka 3 Terminal: Server, ZROK, dan Agent
echo ============================================================
echo.

:: Cek apakah Python bisa diakses
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan di PATH sistem Anda.
    pause
    exit /b
)

:: ═══════════════════════════════════════════════════════════
:: 1. TERMINAL SERVER
:: ═══════════════════════════════════════════════════════════
echo [1/3] Memulai Server API...
start "AniWatch Server" cmd /k "cd /d %~dp0 && echo === ANIWATCH SERVER === && echo. && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info"

:: Beri jeda 5 detik agar server siap sebelum ZROK menyala
timeout /t 5 /nobreak >nul

:: ═══════════════════════════════════════════════════════════
:: 2. TERMINAL ZROK TUNNEL
:: ═══════════════════════════════════════════════════════════
echo [2/3] Memulai ZROK Tunnel...
REM Jika zrok ada di folder project, kita panggil zrok.exe. 
REM Jika zrok ada di PATH global, cukup panggil 'zrok'.
start "AniWatch ZROK" cmd /k "cd /d %~dp0 && echo === ANIWATCH ZROK TUNNEL === && echo. && .\zrok.exe share reserved aniwatch"

:: Beri jeda 2 detik
timeout /t 2 /nobreak >nul

:: ═══════════════════════════════════════════════════════════
:: 3. TERMINAL AGENT
:: ═══════════════════════════════════════════════════════════
echo [3/3] Memulai Agent Scraper...
start "AniWatch Agent" cmd /k "cd /d %~dp0 && echo === ANIWATCH AGENT (HYBRID) === && echo. && python agent\coordinator.py --watch --interval 60"

:: ═══════════════════════════════════════════════════════════
:: SELESAI
:: ═══════════════════════════════════════════════════════════
echo.
echo ============================================================
echo   SEMUA TERMINAL BERHASIL DIBUKA!
echo ============================================================
echo.
echo   - Server : http://localhost:8000
echo   - Docs   : http://localhost:8000/docs
echo   - Portal : http://localhost:8000/portal
echo.
echo   Tekan tombol apa saja untuk menutup jendela peluncur ini.
echo   (Terminal Server, ZROK, dan Agent akan tetap berjalan).
echo.
pause >nul