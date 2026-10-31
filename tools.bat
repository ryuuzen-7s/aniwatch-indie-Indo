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
echo                     ANIWATCH TOOLS v5
echo ================================================================
echo.
echo  DATABASE
echo    [1]  db_monitor        - Monitor DB ^& query
echo    [2]  add_pass          - Manage API key + user
echo    [3]  data_edit         - Edit database (manual)
echo.
echo  ANALYZER
echo    [4]  analyzer_slug     - Analisa slug JSON
echo    [5]  analyzer_genre    - Analisa genre JSON
echo    [6]  convert_flat      - Konversi JSON nested -^> flat
echo    [7]  get_slug          - Extract slug dari slug_by_genre.json
echo.
echo  DEBUG
echo    [8]  scanner           - Scan bug semua file
echo    [9]  debug             - Debug parser ^& data flow
echo.
echo  SCRAPER
echo    [10]  scraper_update    - Scrape anime terbaru (on-going)
echo   [11]  scrape_genre      - Scrape anime by genre
echo   [12]  scrape_env        - Scrape dari daftar .env (agent)
echo.
echo  MANAGE
echo   [13]  add_env           - Edit .env dari JSON
echo   [14]  filter            - Filter file sampah -^> bin/
echo   [15]  cleaner           - Bersihkan bin/ ^& backup/
echo   [16]  auto_slug         - Auto update slug ke agent/.env
echo.
echo  TEST
echo   [17]  test              - Test suite (pytest)
echo   [18]  verify_405        - Verifikasi method restrictor
echo.
echo  INFO
echo   [19]  help              - Bantuan
echo.
echo    [0]  Keluar
echo.
echo ================================================================
set /p choice="  Pilih: "

if "%choice%"=="1"  goto :db_monitor
if "%choice%"=="2"  goto :add_pass
if "%choice%"=="3"  goto :data_edit
if "%choice%"=="4"  goto :analyzer_slug
if "%choice%"=="5"  goto :analyzer_genre
if "%choice%"=="6"  goto :convert_flat
if "%choice%"=="7"  goto :get_slug
if "%choice%"=="8"  goto :scanner
if "%choice%"=="9"  goto :debug
if "%choice%"=="10" goto :scraper_update
if "%choice%"=="11" goto :scrape_genre
if "%choice%"=="12" goto :scrape_env
if "%choice%"=="13" goto :add_env
if "%choice%"=="14" goto :filter
if "%choice%"=="15" goto :cleaner
if "%choice%"=="16" goto :auto_slug
if "%choice%"=="17" goto :test
if "%choice%"=="18" goto :verify_405
if "%choice%"=="19" goto :help
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
call :run_python tools\db_monitor.py
goto :menu

:add_pass
cls
call :run_python tools\add_pass.py
goto :menu

:data_edit
cls
call :run_python tools\edit_anime.py
goto :menu

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

if "%as%"=="1" call :run_python tools\analyzer_slug.py
if "%as%"=="2" call :run_python tools\analyzer_slug.py --stats
if "%as%"=="3" call :run_python tools\analyzer_slug.py --save-slugs
if "%as%"=="4" (
    set /p path="  Path JSON baru: "
    call :run_python tools\analyzer_slug.py --change-json "!path!"
)
if "%as%"=="0" goto :menu
goto :menu

:analyzer_genre
cls
echo.
echo  [Analyzer Genre]
echo    [1] Menu interaktif
echo    [2] Statistik
echo    [0] Kembali
echo.
set /p ag="  Pilih: "

if "%ag%"=="1" call :run_python tools\analyzer_genre.py
if "%ag%"=="2" call :run_python tools\analyzer_genre.py --stats
if "%ag%"=="0" goto :menu
goto :menu

:convert_flat
cls
call :run_python tools\convert_genre_to_flat.py
goto :menu

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

if "%gs%"=="1" call :run_python tools\get_slug.py
if "%gs%"=="2" call :run_python tools\get_slug.py --all
if "%gs%"=="3" call :run_python tools\get_slug.py --by-genre
if "%gs%"=="4" call :run_python tools\get_slug.py --combined
if "%gs%"=="5" call :run_python tools\get_slug.py --stats
if "%gs%"=="0" goto :menu
goto :menu

:: ═══════════════════════════════════════════════════════════
::  DEBUG
:: ═══════════════════════════════════════════════════════════
:scanner
cls
echo.
echo  [Scanner] Scan bug
echo    [1] Scan default (.py, skip: api/core/db/cache/security)
echo    [2] Scan full (.py + web)
echo    [3] Scan folder tertentu (api/core/db/cache/security)
echo    [4] Hanya tampilkan error
echo    [0] Kembali
echo.
set /p sc="  Pilih: "

if "%sc%"=="1" call :run_python tools\scanner.py
if "%sc%"=="2" call :run_python tools\scanner.py --full
if "%sc%"=="3" (
    set /p folder="  Folder (mis. api): "
    call :run_python tools\scanner.py --path !folder!
)
if "%sc%"=="4" call :run_python tools\scanner.py --only-errors
if "%sc%"=="0" goto :menu
goto :menu

:debug
cls
call :run_python tools\debug.py
goto :menu

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

if "%su%"=="1" call :run_python tools\scraper_update.py --limit 5
if "%su%"=="2" call :run_python tools\scraper_update.py --limit 10
if "%su%"=="3" call :run_python tools\scraper_update.py --limit 20
if "%su%"=="4" call :run_python tools\scraper_update.py --all
if "%su%"=="5" call :run_python tools\scraper_update.py --dry-run
if "%su%"=="6" call :run_python tools\scraper_update.py --json-only
if "%su%"=="7" call :run_python tools\scraper_update.py --no-save
if "%su%"=="0" goto :menu
goto :menu

:scrape_genre
cls
echo.
echo  [Scrape By Genre]
echo  Contoh genre: action, adventure, comedy, fantasy,
echo                romance, magic, mecha, shounen, dll
echo.
set /p genre="  Genre (mis. action): "
if "%genre%"=="" goto :menu
echo.
set /p pages="  Max halaman (default 5): "
if "%pages%"=="" set pages=5
call :run_python tools\scraper_by_genre.py --genre %genre% --pages %pages%
goto :menu

:scrape_env
cls
echo.
echo ================================================================
echo                    SCRAPE ENV (AGENT)
echo ================================================================
echo.
echo  Mode ini akan scraping daftar slug yang ada di agent/.env
echo  (SLUG_1, SLUG_2, dst) + anime on-going terbaru.
echo.
echo    [1] Mulai Scrape .env (Follow Env)
echo    [2] Mulai Mode Hybrid (Watcher)
echo    [3] Cek Status Agent
echo    [0] Kembali
echo.
set /p se="  Pilih: "

if "%se%"=="1" call :run_python agent\runner.py
if "%se%"=="2" call :run_python agent\coordinator.py --watch --interval 60
if "%se%"=="3" call :run_python agent\caller.py --status
if "%se%"=="0" goto :menu
goto :menu

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

if "%ae%"=="1" call :run_python tools\add_env.py
if "%ae%"=="2" call :run_python tools\add_env.py --list
if "%ae%"=="3" call :run_python tools\add_env.py --preview
if "%ae%"=="4" call :run_python tools\add_env.py
if "%ae%"=="5" call :run_python tools\add_env.py --merge
if "%ae%"=="0" goto :menu
goto :menu

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

if "%fl%"=="1" call :run_python tools\filter.py
if "%fl%"=="2" call :run_python tools\filter.py --run
if "%fl%"=="3" call :run_python tools\filter.py --stats
if "%fl%"=="0" goto :menu
goto :menu

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

if "%cl%"=="1" call :run_python tools\cleaner.py --dry-run
if "%cl%"=="2" call :run_python tools\cleaner.py
if "%cl%"=="3" call :run_python tools\cleaner.py --backup
if "%cl%"=="0" goto :menu
goto :menu

:auto_slug
cls
echo.
echo ================================================================
echo                    AUTO SLUG TO .ENV
echo ================================================================
echo.
echo  Mengekstrak slug dari JSON dan menyimpannya ke agent/.env
echo.
call :run_python tools\get_slug.py --env
goto :menu

:: ═══════════════════════════════════════════════════════════
::  TEST
:: ═══════════════════════════════════════════════════════════
:test
cls
echo.
echo ================================================================
echo                       TEST MENU
echo ================================================================
echo.
echo    [1] Generate file test (tools\test.py)
echo    [2] Jalankan pytest (semua, verbose)
echo    [3] Jalankan pytest (ringkas)
echo    [4] Test method restrictor (405)
echo    [5] Test API dasar
echo    [0] Kembali
echo.
set /p t="  Pilih: "

if "%t%"=="1" (
    python tools\test.py
    echo.
    echo  [Enter untuk lanjut]
    pause >nul
)
if "%t%"=="2" (
    python -m pytest test\ -v
    echo.
    echo  [Enter untuk lanjut]
    pause >nul
)
if "%t%"=="3" (
    python -m pytest test\ --tb=short -q
    echo.
    echo  [Enter untuk lanjut]
    pause >nul
)
if "%t%"=="4" (
    python -m pytest test\test_api.py::TestMethodRestrictor -v
    echo.
    echo  [Enter untuk lanjut]
    pause >nul
)
if "%t%"=="5" (
    python -m pytest test\test_api.py -v
    echo.
    echo  [Enter untuk lanjut]
    pause >nul
)
if "%t%"=="0" goto :menu
goto :menu

:: ═══════════════════════════════════════════════════════════
::  VERIFY 405
:: ═══════════════════════════════════════════════════════════
:verify_405
cls
echo.
echo ================================================================
echo             VERIFY METHOD RESTRICTOR (405)
echo ================================================================
echo.
echo  Pastikan server sudah jalan di port 8000!
echo.
echo  ----------------------------------------------
echo   Method   Endpoint              Ekspektasi
echo  ----------------------------------------------
echo   GET      /health               200
echo   GET      /share/now            200
echo   PUT      /share/now            405
echo   DELETE   /share/now            405
echo   PATCH    /share/now            405
echo   DELETE   /keys/999             401/403/404
echo   GET      /openapi.json         200
echo   OPTIONS  /share/now            200/204
echo  ----------------------------------------------
echo.

echo  Hasil aktual:
echo  ----------------------------------------------

echo | set /p="GET  /health      : "
curl -s -o nul -w "%%{http_code}" http://localhost:8000/health
echo.

echo | set /p="GET  /share/now   : "
curl -s -o nul -w "%%{http_code}" http://localhost:8000/share/now
echo.

echo | set /p="PUT  /share/now   : "
curl -s -o nul -w "%%{http_code}" -X PUT http://localhost:8000/share/now
echo.

echo | set /p="DEL  /share/now   : "
curl -s -o nul -w "%%{http_code}" -X DELETE http://localhost:8000/share/now
echo.

echo | set /p="PATCH /share/now  : "
curl -s -o nul -w "%%{http_code}" -X PATCH http://localhost:8000/share/now
echo.

echo | set /p="DEL  /keys/999    : "
curl -s -o nul -w "%%{http_code}" -X DELETE http://localhost:8000/keys/999
echo.

echo | set /p="GET  /openapi.json: "
curl -s -o nul -w "%%{http_code}" http://localhost:8000/openapi.json
echo.

echo | set /p="OPTIONS /share/now: "
curl -s -o nul -w "%%{http_code}" -X OPTIONS http://localhost:8000/share/now
echo.

echo  ----------------------------------------------
echo.
echo  [Enter untuk lanjut]
pause >nul
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
echo    scanfull      Scan full (.py + web)
echo    scanapi       Scan folder api
echo    debug         Debug parser
echo.
echo  SCRAPER:
echo    update        Scrape anime terbaru
echo    scrape        Scrape anime by genre
echo    env           Scrape dari daftar .env
echo.
echo  MANAGE:
echo    addenv        Edit .env dari JSON
echo    filter        Filter file sampah
echo    cleaner       Bersihkan bin/ ^& backup/
echo    autoslug      Auto update slug ke agent/.env
echo.
echo  TEST:
echo    test          Test suite (pytest)
echo    verify        Verifikasi method restrictor (405)
echo.
echo ================================================================
echo  [Enter untuk kembali]
pause >nul
goto :menu

:: ═══════════════════════════════════════════════════════════
::  RUN PYTHON (Error Handling)
:: ═══════════════════════════════════════════════════════════
:run_python
python %*
set EXITCODE=%errorlevel%
if %EXITCODE% neq 0 (
    echo.
    echo  ================================================================
    echo   ERROR: exit code %EXITCODE%
    echo  ================================================================
)
echo.
echo  [Enter untuk lanjut]
pause >nul
goto :eof

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
if /i "%~1"=="scanfull" goto :cmd_scanfull
if /i "%~1"=="scanapi"  goto :cmd_scanapi
if /i "%~1"=="debug"    goto :cmd_debug
if /i "%~1"=="update"   goto :cmd_update
if /i "%~1"=="scrape"   goto :cmd_scrape
if /i "%~1"=="env"      goto :cmd_env
if /i "%~1"=="addenv"   goto :cmd_addenv
if /i "%~1"=="filter"   goto :cmd_filter
if /i "%~1"=="cleaner"  goto :cmd_cleaner
if /i "%~1"=="clean"    goto :cmd_cleaner
if /i "%~1"=="autoslug" goto :cmd_autoslug
if /i "%~1"=="test"     goto :cmd_test
if /i "%~1"=="verify"   goto :cmd_verify
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

:cmd_scanfull
python tools\scanner.py --full
goto :end

:cmd_scanapi
python tools\scanner.py --path api --only-errors
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
python agent\runner.py
goto :end

:cmd_addenv
python tools\add_env.py
goto :end

:cmd_filter
python tools\filter.py
goto :end

:cmd_cleaner
python tools\cleaner.py
goto :end

:cmd_autoslug
python tools\get_slug.py --env
goto :end

:cmd_test
python -m pytest test\ -v
goto :end

:cmd_verify
echo.
echo  Verifikasi method restrictor (405)
echo  Pastikan server jalan di port 8000
echo.
curl -s -o nul -w "GET  /health      : %%{http_code}\n" http://localhost:8000/health
curl -s -o nul -w "PUT  /share/now   : %%{http_code}\n" -X PUT http://localhost:8000/share/now
curl -s -o nul -w "DEL  /share/now   : %%{http_code}\n" -X DELETE http://localhost:8000/share/now
curl -s -o nul -w "PATCH /share/now  : %%{http_code}\n" -X PATCH http://localhost:8000/share/now
curl -s -o nul -w "DEL  /keys/999    : %%{http_code}\n" -X DELETE http://localhost:8000/keys/999
curl -s -o nul -w "GET  /openapi.json: %%{http_code}\n" http://localhost:8000/openapi.json
echo.
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
echo    scan      Scan bug default
echo    scanfull  Scan bug full
echo    scanapi   Scan folder api (error only)
echo    debug     Debug parser
echo    update    Scrape anime terbaru
echo    scrape    Scrape by genre
echo    env       Scrape dari daftar .env
echo    addenv    Edit .env dari JSON
echo    filter    Filter file sampah
echo    cleaner   Bersihkan bin/
echo    autoslug  Auto update slug ke agent/.env
echo    test      Test suite (pytest)
echo    verify    Verifikasi method restrictor (405)
echo.
goto :end