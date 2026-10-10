@echo off
REM ============================================================
REM  AniWatch Agent - Daily Scrape
REM ============================================================

cd /d "%~dp0"
cd ..

echo ============================================================
echo   AniWatch Agent - %date% %time%
echo ============================================================

python agent\runner.py

echo.
echo Selesai. Tekan tombol apa saja untuk close...
REM pause