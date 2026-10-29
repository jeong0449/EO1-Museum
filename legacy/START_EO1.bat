@echo off
cd /d "%~dp0"
title EO1 Gallery Server

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo Install Python and make sure "Add Python to PATH" is enabled.
  pause
  exit /b 1
)

python -c "import PIL" >nul 2>nul
if errorlevel 1 (
  echo Installing Pillow...
  python -m pip install pillow
  if errorlevel 1 (
    echo.
    echo Pillow installation failed.
    pause
    exit /b 1
  )
)

echo.
echo Building EO1 gallery...
python make_gallery.py
if errorlevel 1 (
  pause
  exit /b 1
)

echo.
echo ==========================================================
echo EO1 Gallery is starting on port 8000.
echo On the EO1, open:  http://YOUR-PC-IP:8000
echo.
echo Find YOUR-PC-IP with: ipconfig
echo Keep this window open while using the EO1.
echo Press Ctrl+C to stop the server.
echo ==========================================================
echo.

python server.py
pause
