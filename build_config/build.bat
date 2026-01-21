@echo off
REM Build script for Windows

setlocal enabledelayedexpansion

echo Building PDF Batch Merger for Windows...
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM Check if PyInstaller is installed
where pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: PyInstaller is not installed
    echo Install it with: pip install pyinstaller
    exit /b 1
)

REM Check if public key exists
set "PUBLIC_KEY=%PROJECT_ROOT%\pdf_merger\licensing\public_key.pem"
if not exist "%PUBLIC_KEY%" (
    echo Warning: Public key not found at %PUBLIC_KEY%
    echo The app will still build, but license verification may not work.
    echo.
)

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "PDF Batch Merger.exe" del /q "PDF Batch Merger.exe"

REM Build with PyInstaller
echo.
echo Building application...
pyinstaller build_config\windows.spec

REM Check if build succeeded
if exist "dist\PDF Batch Merger.exe" (
    echo.
    echo Build successful!
    echo Application: dist\PDF Batch Merger.exe
    echo.
    echo To test the app, run:
    echo   dist\PDF Batch Merger.exe
) else (
    echo.
    echo Build failed!
    exit /b 1
)

endlocal
