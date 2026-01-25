@echo off
REM Windows Code Signing Script
REM Signs the Windows executable with a code signing certificate

setlocal enabledelayedexpansion

set EXE_PATH=%1
set CERT_PATH=%2
set CERT_PASSWORD=%3
set TIMESTAMP_URL=http://timestamp.digicert.com

REM Validate arguments
if "%EXE_PATH%"=="" (
    echo Error: Executable path is required
    echo Usage: sign_windows.bat ^<exe_path^> [cert_path] [cert_password]
    exit /b 1
)

if not exist "%EXE_PATH%" (
    echo Error: Executable not found: %EXE_PATH%
    exit /b 1
)

echo Starting Windows code signing...
echo.

REM Check if certificate path is provided
if "%CERT_PATH%"=="" (
    echo Using certificate from Windows Certificate Store...
    echo.
    
    REM Sign using certificate from store (requires /a flag to auto-select)
    signtool sign /a /t "%TIMESTAMP_URL%" "%EXE_PATH%"
    
    if errorlevel 1 (
        echo Error: Code signing failed
        exit /b 1
    )
) else (
    echo Using certificate file: %CERT_PATH%
    echo.
    
    if not exist "%CERT_PATH%" (
        echo Error: Certificate file not found: %CERT_PATH%
        exit /b 1
    )
    
    REM Sign using certificate file
    if "%CERT_PASSWORD%"=="" (
        echo Warning: No certificate password provided
        signtool sign /f "%CERT_PATH%" /t "%TIMESTAMP_URL%" "%EXE_PATH%"
    ) else (
        signtool sign /f "%CERT_PATH%" /p "%CERT_PASSWORD%" /t "%TIMESTAMP_URL%" "%EXE_PATH%"
    )
    
    if errorlevel 1 (
        echo Error: Code signing failed
        exit /b 1
    )
)

echo.
echo Verifying signature...
signtool verify /pa "%EXE_PATH%"

if errorlevel 1 (
    echo Warning: Signature verification failed
    exit /b 1
)

echo.
echo Code signing complete!
echo Executable: %EXE_PATH%
