@echo off
REM Unregister AniWatch Agent task

echo Menghapus task AniWatchAgent...
schtasks /Delete /TN "AniWatchAgent" /F

if %errorlevel% == 0 (
    echo OK - Task dihapus
) else (
    echo GAGAL atau task tidak ada
)

pause