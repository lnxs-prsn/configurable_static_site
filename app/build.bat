@echo off
REM Tusmo ry — Build script for Windows
REM Defensive checks + Tailwind binary auto-download

echo === Tusmo ry Build ===

REM Check 1: Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is required but not found.
    echo Install Python and try again.
    exit /b 1
)
echo [OK] Python found

REM Check 2: Python dependencies
python -c "import jinja2, yaml, markdown" >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Required Python packages are missing.
    echo Run: pip install -r requirements.txt
    exit /b 1
)
echo [OK] Python dependencies OK

REM Check 3: Tailwind CSS binary
set tailwind_bin=bin\tailwindcss.exe
if not exist "%tailwind_bin%" (
    echo Tailwind binary not found. Downloading...

    set tailwind_version=v4.0.4
    set download_url=https://github.com/tailwindlabs/tailwindcss/releases/download/%tailwind_version%/tailwindcss-windows-x64.exe

    echo Downloading: %download_url%
    if not exist "bin" mkdir bin
    powershell -Command "try { Invoke-WebRequest -Uri '%download_url%' -OutFile '%tailwind_bin%' } catch { exit 1 }"
    if %errorlevel% neq 0 (
        echo ERROR: Failed to download Tailwind binary.
        echo Download manually from: https://github.com/tailwindlabs/tailwindcss/releases
        exit /b 1
    )
    echo [OK] Tailwind binary downloaded
) else (
    echo [OK] Tailwind binary found
)

REM Run the build
echo.
echo Building site...
python build.py

echo.
echo === Build complete ===
echo Output is in output\
echo Preview: python -m http.server 8000 --directory output\
