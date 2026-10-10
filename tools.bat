@echo off
title AniWatch Tools
cd /d "%~dp0"
setlocal enabledelayedexpansion

:: ═══════════════════════════════════════════════════════════
::  COMMAND LINE MODE
:: ═══════════════════════════════════════════════════════════
if not "%~1"=="" goto :cmdline

:: ═══════════════════════════════════════════════════════════
::  MENU UTAMA
:: ═══════════════════════════════════════════════════════════
:menu
cls
echo.
echo ================================================================
echo                     ANIWATCH TOOLS v4
echo ================================================================
echo.
echo  DATABASE
echo    [1]  db_monitor        - Monitor DB ^& query
echo    [2]  add_pass          - Manage API key + user
echo.
echo  ANALYZER
echo    [3]  analyzer_slug     - Analisa slug JSON
echo    [4]  analyzer_genre    - Analisa genre JSON
echo    [5]  convert_flat      - Konversi JSON nested -^> flat
echo    [6]  get_slug          - Extract slug dari slug_by_genre.json
echo.
echo  DEBUG
echo    [7]  scanner           - Scan bug semua file
echo    [8]  debug             - Debug parser ^& data flow
echo.
echo  SCRAPER
echo    [9]  scraper_update    - Scrape anime terbaru (on-going)
echo   [10]  scrape_genre      - Scrape anime by genre
echo.
echo  MANAGE
echo   [11]  add_env           - Edit .env dari JSON (data/base/slugs/)
echo   [12]  filter            - Filter file sampah -^> bin/
echo   [13]  cleaner           - Bersihkan bin/ ^& backup/
echo.
echo  TEST
echo   [14]  test              - Test manual DB
echo.
echo  INFO
echo   [15]  help              - Bantuan
echo.
echo    [0]  Keluar
echo.
echo ================================================================
set /p choice="  Pilih: "

if "%choice%"=="1"  goto :db_monitor
if "%choice%"=="2"  goto :add_pass
if "%choice%"=="3"  goto :analyzer_slug
if "%choice%"=="4"  goto :analyzer_genre
if "%choice%"=="5"  goto :convert_flat
if "%choice%"=="6"  goto :get_slug
if "%choice%"=="7"  goto :scanner
if "%choice%"=="8"  goto :debug
if "%choice%"=="9"  goto :scraper_update
if "%choice%"=="10" goto :scrape_genre
if "%choice%"=="11" goto :add_env
if "%choice%"=="12" goto :filter
if "%choice%"=="13" goto :cleaner
if "%choice%"=="14" goto :test
if "%choice%"=="15" goto :help
if "%choice%"=="0"  goto :end

echo.
echo  Pilihan tidak valid!
timeout /t 2 /nobreak >nul
goto :menu

:: ═══════════════════════════════════════════════════════════
::  DATABASE
:: ═══════════════════════════════════════════════════════════
:db_monitor
cls
python tools\db_monitor.py
goto :back

:add_pass
cls
python tools\add_pass.py
goto :back

:: ═══════════════════════════════════════════════════════════
::  ANALYZER
:: ═══════════════════════════════════════════════════════════
:analyzer_slug
cls
echo.
echo  [Analyzer Slug]
echo    [1] Menu interaktif
echo    [2] Statistik
echo    [3] Simpan slug ke data/base/
echo    [4] Ganti JSON
echo    [0] Kembali
echo.
set /p as="  Pilih: "

if "%as%"=="1" python tools\analyzer_slug.py
if "%as%"=="2" python tools\analyzer_slug.py --stats
if "%as%"=="3" python tools\analyzer_slug.py --save-slugs
if "%as%"=="4" (
    set /p path="  Path JSON baru: "
    python tools\analyzer_slug.py --change-json "!path!"
)
if "%as%"=="0" goto :menu

goto :back

:analyzer_genre
cls
echo.
echo  [Analyzer Genre]
echo    [1] Menu interaktif
echo    [2] Statistik
echo    [0] Kembali
echo.
set /p ag="  Pilih: "

if "%ag%"=="1" python tools\analyzer_genre.py
if "%ag%"=="2" python tools\analyzer_genre.py --stats
if "%ag%"=="0" goto :menu

goto :back

:convert_flat
cls
python tools\convert_genre_to_flat.py
goto :back

:get_slug
cls
echo.
echo  [Get Slug] Extract slug dari slug_by_genre.json
echo    [1] Menu interaktif
echo    [2] Extract semua (flat) -^> slugs_all.json
echo    [3] Extract per genre -^> by_genre/
echo    [4] Extract semua + combined
echo    [5] Statistik
echo    [0] Kembali
echo.
set /p gs="  Pilih: "

if "%gs%"=="1" python tools\get_slug.py
if "%gs%"=="2" python tools\get_slug.py --all
if "%gs%"=="3" python tools\get_slug.py --by-genre
if "%gs%"=="4" python tools\get_slug.py --combined
if "%gs%"=="5" python tools\get_slug.py --stats
if "%gs%"=="0" goto :menu

goto :back

:: ═══════════════════════════════════════════════════════════
::  DEBUG
:: ═══════════════════════════════════════════════════════════
:scanner
cls
echo.
echo  [Scanner] Scan bug
echo    [1] Scan default (.py)
echo    [2] Scan full (.py + web)
echo    [3] Scan folder tertentu
echo    [4] Hanya tampilkan error
echo    [0] Kembali
echo.
set /p sc="  Pilih: "

if "%sc%"=="1" python tools\scanner.py
if "%sc%"=="2" python tools\scanner.py --full
if "%sc%"=="3" (
    set /p folder="  Folder (mis. api): "
    python tools\scanner.py --path !folder!
)
if "%sc%"=="4" python tools\scanner.py --only-errors
if "%sc%"=="0" goto :menu

goto :back

:debug
cls
python tools\debug.py
goto :back

:: ═══════════════════════════════════════════════════════════
::  SCRAPER
:: ═══════════════════════════════════════════════════════════
:scraper_update
cls
echo.
echo  [Scraper Update] Anime terbaru (on-going)
echo    [1] 5 anime
echo    [2] 10 anime
echo    [3] 20 anime
echo    [4] Semua on-going
echo    [5] Dry-run (preview)
echo    [6] JSON only (tanpa DB)
echo    [7] DB only (tanpa JSON)
echo    [0] Kembali
echo.
set /p su="  Pilih: "

if "%su%"=="1" python tools\scraper_update.py --limit 5
if "%su%"=="2" python tools\scraper_update.py --limit 10
if "%su%"=="3" python tools\scraper_update.py --limit 20
if "%su%"=="4" python tools\scraper_update.py --all
if "%su%"=="5" python tools\scraper_update.py --dry-run
if "%su%"=="6" python tools\scraper_update.py --json-only
if "%su%"=="7" python tools\scraper_update.py --no-save
if "%su%"=="0" goto :menu

goto :back

:scrape_genre
cls
echo.
echo  [Scrape By Genre]
echo.
echo  Contoh genre: action, adventure, comedy, fantasy,
echo                romance, magic, mecha, shounen, dll
echo.
set /p genre="  Genre (mis. action): "
if "%genre%"=="" goto :menu
echo.
set /p pages="  Max halaman (default 5): "
if "%pages%"=="" set pages=5
python tools\scraper_by_genre.py --genre %genre% --pages %pages%
goto :back

:: ═══════════════════════════════════════════════════════════
::  MANAGE
:: ═══════════════════════════════════════════════════════════
:add_env
cls
echo.
echo  [Add Env] Edit .env dari JSON (data/base/slugs/)
echo    [1] Menu interaktif
echo    [2] List JSON files
echo    [3] Preview (pilih file)
echo    [4] Replace .env
echo    [5] Merge .env
echo    [0] Kembali
echo.
set /p ae="  Pilih: "

if "%ae%"=="1" python tools\add_env.py
if "%ae%"=="2" python tools\add_env.py --list
if "%ae%"=="3" python tools\add_env.py --preview
if "%ae%"=="4" python tools\add_env.py
if "%ae%"=="5" python tools\add_env.py --merge
if "%ae%"=="0" goto :menu

goto :back

:filter
cls
echo.
echo ================================================================
echo                    FILTER FILE SAMPAH
echo ================================================================
echo.
echo  Rules:
echo    _*.py           -^> bin/       (script temporary)
echo    *.txt non-root  -^> bin/
echo    *.bak           -^> backup/
echo    *.example       -^> backup/
echo    *.old           -^> backup/
echo.
echo    [1] Preview (dry-run)
echo    [2] Jalankan filter
echo    [3] Statistik file
echo    [0] Kembali
echo.
set /p fl="  Pilih: "

if "%fl%"=="1" python tools\filter.py
if "%fl%"=="2" python tools\filter.py --run
if "%fl%"=="3" python tools\filter.py --stats
if "%fl%"=="0" goto :menu

goto :back

:cleaner
cls
echo.
echo ================================================================
echo                    CLEANER
echo ================================================================
echo.
echo    [1] Preview (dry-run)
echo    [2] Kosongkan bin/
echo    [3] Kosongkan bin/ + backup/
echo    [0] Kembali
echo.
set /p cl="  Pilih: "

if "%cl%"=="1" python tools\cleaner.py --dry-run
if "%cl%"=="2" python tools\cleaner.py
if "%cl%"=="3" python tools\cleaner.py --backup
if "%cl%"=="0" goto :menu

goto :back

:: ═══════════════════════════════════════════════════════════
::  TEST
:: ═══════════════════════════════════════════════════════════
:test
cls
python tools\test.py
goto :menu

:: ═══════════════════════════════════════════════════════════
::  HELP
:: ═══════════════════════════════════════════════════════════
:help
cls
echo.
echo ================================================================
echo                    ANIWATCH TOOLS - HELP
echo ================================================================
echo.
echo  Usage: tools [command]
echo.
echo  DATABASE:
echo    db            Monitor DB interaktif
echo    key           Manage API key + user
echo.
echo  ANALYZER:
echo    slug          Analisa slug JSON
echo    genre         Analisa genre JSON
echo    convert       Konversi JSON nested -^> flat
echo    getslug       Extract slug dari slug_by_genre.json
echo.
echo  DEBUG:
echo    scan          Scan bug semua file
echo    debug         Debug parser
echo.
echo  SCRAPER:
echo    update        Scrape anime terbaru
echo    scrape        Scrape anime by genre
echo.
echo  MANAGE:
echo    env           Edit .env dari JSON
echo    filter        Filter file sampah
echo    cleaner       Bersihkan bin/ ^& backup/
echo.
echo  TEST:
echo    test          Test manual DB
echo.
echo  Contoh:
echo    tools update        - Scrape anime terbaru
echo    tools getslug       - Extract slug
echo    tools env           - Edit .env
echo    tools cleaner       - Bersihkan bin/
echo    tools help          - Bantuan
echo.
echo ================================================================
pause
goto :menu

:: ═══════════════════════════════════════════════════════════
::  BACK
:: ═══════════════════════════════════════════════════════════
:back
echo.
echo ================================================================
pause
goto :menu

:: ═══════════════════════════════════════════════════════════
::  END
:: ═══════════════════════════════════════════════════════════
:end
cls
echo.
echo  Bye!
timeout /t 1 /nobreak >nul
exit /b 0

:: ═══════════════════════════════════════════════════════════
::  COMMAND LINE MODE
:: ═══════════════════════════════════════════════════════════
:cmdline
if /i "%~1"=="db"       goto :cmd_db
if /i "%~1"=="key"      goto :cmd_key
if /i "%~1"=="slug"     goto :cmd_slug
if /i "%~1"=="genre"    goto :cmd_genre
if /i "%~1"=="convert"  goto :cmd_convert
if /i "%~1"=="getslug"  goto :cmd_getslug
if /i "%~1"=="scan"     goto :cmd_scan
if /i "%~1"=="debug"    goto :cmd_debug
if /i "%~1"=="update"   goto :cmd_update
if /i "%~1"=="scrape"   goto :cmd_scrape
if /i "%~1"=="env"      goto :cmd_env
if /i "%~1"=="filter"   goto :cmd_filter
if /i "%~1"=="cleaner"  goto :cmd_cleaner
if /i "%~1"=="clean"    goto :cmd_cleaner
if /i "%~1"=="test"     goto :cmd_test
if /i "%~1"=="help"     goto :cmd_help

echo Unknown command: %~1
echo Run: tools help
exit /b 1

:cmd_db
python tools\db_monitor.py
goto :end

:cmd_key
python tools\add_pass.py
goto :end

:cmd_slug
python tools\analyzer_slug.py
goto :end

:cmd_genre
python tools\analyzer_genre.py
goto :end

:cmd_convert
python tools\convert_genre_to_flat.py
goto :end

:cmd_getslug
python tools\get_slug.py
goto :end

:cmd_scan
python tools\scanner.py
goto :end

:cmd_debug
python tools\debug.py
goto :end

:cmd_update
python tools\scraper_update.py
goto :end

:cmd_scrape
python tools\scraper_by_genre.py
goto :end

:cmd_env
python tools\add_env.py
goto :end

:cmd_filter
python tools\filter.py
goto :end

:cmd_cleaner
python tools\cleaner.py
goto :end

:cmd_test
python tools\test.py
goto :end

:cmd_help
echo.
echo  ANIWATCH TOOLS - Commands:
echo.
echo    db        Monitor DB
echo    key       Manage API key
echo    slug      Analisa slug JSON
echo    genre     Analisa genre JSON
echo    convert   Konversi JSON
echo    getslug   Extract slug
echo    scan      Scan bug
echo    debug     Debug parser
echo    update    Scrape anime terbaru
echo    scrape    Scrape by genre
echo    env       Edit .env
echo    filter    Filter file sampah
echo    cleaner   Bersihkan bin/
echo    test      Test DB
echo.
goto :end