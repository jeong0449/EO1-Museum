@echo off
cd /d "%~dp0"

echo ==========================================
echo   EO1 - Update The Met Collection
echo   Keyword Search Edition
echo ==========================================
echo.
echo The running web server will NOT be stopped.
echo New artwork will be added to the collection.
echo.

echo [1/2] Searching and downloading artwork from The Met...
python GET_MET_ART_KEYWORD.py

if errorlevel 1 (
    echo.
    echo ERROR: Artwork download failed.
    pause
    exit /b 1
)

echo.
echo [2/2] Rebuilding the EO1 gallery...
python make_gallery.py

if errorlevel 1 (
    echo.
    echo ERROR: Gallery rebuild failed.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   Update complete.
echo   Reload the page on EO1 if necessary.
echo ==========================================
echo.
pause
