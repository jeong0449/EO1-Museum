@echo off
cd /d "%~dp0"
title EO1 - The Met Gallery

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found in PATH.
  pause
  exit /b 1
)

echo ==========================================================
echo  EO1 - The Met Open Access Gallery
echo ==========================================================
echo.
python GET_MET_ART_KEYWORD.py
if errorlevel 1 (
  echo.
  echo Download step did not complete successfully.
  pause
  exit /b 1
)

echo.
if exist make_gallery.py (
  echo Building 1080x1920 EO1 images...
  python make_gallery.py
) else (
  echo NOTE: make_gallery.py was not found in this folder.
  echo Make sure all EO1-Museum files are in the same project folder.
  pause
  exit /b 1
)

echo.
echo Starting the local web server...
echo On EO1 open: http://YOUR-PC-IP:8000
echo Find YOUR-PC-IP with: ipconfig
echo Press Ctrl+C here to stop.
echo.
python server.py
pause
