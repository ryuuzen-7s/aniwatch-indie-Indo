@echo off
REM ============================================================
REM  AniWatch Agent - Hourly Scrape (lebih cepat)
REM ============================================================

cd /d "%~dp0"
cd ..

echo ============================================================
echo   AniWatch Agent Hourly - %date% %time%
echo ============================================================

python agent\runner.py --skip-ongoing

echo Selesai.