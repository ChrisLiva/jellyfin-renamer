@echo off
setlocal enabledelayedexpansion

REM Jellyfin Renamer Install Script for Windows
REM This script installs the jellyfin-renamer tool to make it available system-wide

echo ================================
echo   Jellyfin Renamer Installer
echo ================================
echo.

REM Check if we're in the right directory
if not exist "jellyfin-renamer.py" (
    echo [ERROR] Please run this script from the jellyfin-renamer project directory.
    pause
    exit /b 1
)

if not exist "pyproject.toml" (
    echo [ERROR] Please run this script from the jellyfin-renamer project directory.
    pause
    exit /b 1
)

REM Check Python version
echo [INFO] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.13 or higher from https://python.org
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Python version: %PYTHON_VERSION%

REM Check if UV is installed
echo [INFO] Checking for UV package manager...
uv --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] UV package manager not found. Installing...
    
    REM Try to install UV using pip
    pip install uv >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install UV. Please install it manually:
        echo https://docs.astral.sh/uv/getting-started/installation/
        pause
        exit /b 1
    )
    echo [INFO] UV installed successfully!
) else (
    echo [INFO] UV package manager found.
)

REM Check if FFmpeg is installed
echo [INFO] Checking for FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found. Please install it manually:
    echo https://ffmpeg.org/download.html
    echo.
    echo For Windows, you can also use Chocolatey:
    echo choco install ffmpeg
    echo.
    echo Or download from: https://www.gyan.dev/ffmpeg/builds/
    echo.
    set /p CONTINUE="Continue without FFmpeg? (y/N): "
    if /i not "!CONTINUE!"=="y" (
        pause
        exit /b 1
    )
) else (
    echo [INFO] FFmpeg found.
)

REM Install project dependencies
echo [INFO] Installing project dependencies...
uv venv
uv sync
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

REM Create executable script
echo [INFO] Creating executable...
set INSTALL_DIR=%USERPROFILE%\.local\bin
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Create the batch file
set SCRIPT_PATH=%INSTALL_DIR%\jellyfin-renamer.bat
(
echo @echo off
echo REM Get the directory where this script is located
echo set SCRIPT_DIR=%%~dp0
echo set PROJECT_DIR=%%SCRIPT_DIR:~0,-1%%
echo for %%i in ^("%%PROJECT_DIR%%"^) do set PROJECT_DIR=%%~fi
echo set PROJECT_DIR=%%PROJECT_DIR:~0,-1%%
echo set PROJECT_DIR=%%PROJECT_DIR%\jellyfin-renamer
echo.
echo REM Check if the project directory exists
echo if not exist "%%PROJECT_DIR%%" ^(
echo     echo Error: jellyfin-renamer project directory not found at %%PROJECT_DIR%%
echo     echo Please ensure the project is installed correctly.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Change to the project directory
echo cd /d "%%PROJECT_DIR%%"
echo.
echo REM Check if UV is available
echo uv --version ^>nul 2^>^&1
echo if not errorlevel 1 ^(
echo     REM Use UV to run the script
echo     uv run python jellyfin-renamer.py %%*
echo ^) else ^(
echo     REM Fallback to direct Python execution
echo     python jellyfin-renamer.py %%*
echo ^)
) > "%SCRIPT_PATH%"

echo [INFO] Created executable at: %SCRIPT_PATH%

REM Add to PATH if not already there
echo %PATH% | findstr /i "%INSTALL_DIR%" >nul
if errorlevel 1 (
    echo [INFO] Adding to PATH...
    
    REM Add to user PATH
    setx PATH "%PATH%;%INSTALL_DIR%"
    if errorlevel 1 (
        echo [WARNING] Failed to add to PATH automatically.
        echo Please add '%INSTALL_DIR%' to your PATH manually.
    ) else (
        echo [INFO] Added to PATH successfully.
        echo [WARNING] Please restart your command prompt to use jellyfin-renamer
    )
) else (
    echo [INFO] Already in PATH.
)

REM Create desktop shortcut (optional)
set /p CREATE_SHORTCUT="Create desktop shortcut? (y/N): "
if /i "%CREATE_SHORTCUT%"=="y" (
    if exist "%USERPROFILE%\Desktop" (
        set DESKTOP_FILE=%USERPROFILE%\Desktop\jellyfin-renamer.bat
        (
            echo @echo off
            echo title Jellyfin Renamer
            echo echo Jellyfin Renamer - Media Organization Tool
            echo echo.
            echo jellyfin-renamer --help
            echo echo.
            echo pause
        ) > "%DESKTOP_FILE%"
        echo [INFO] Created desktop shortcut
    )
)

REM Test the installation
echo [INFO] Testing installation...
"%SCRIPT_PATH%" --help >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Installation test failed, but the tool may still work.
) else (
    echo [INFO] Installation test successful!
)

echo.
echo [INFO] Installation complete!
echo.
echo Usage:
echo   jellyfin-renamer ^<source_directory^> ^<target_directory^> [options]
echo.
echo Examples:
echo   jellyfin-renamer C:\path\to\media C:\path\to\jellyfin\media
echo   jellyfin-renamer C:\path\to\media C:\path\to\jellyfin\media --downmix-audio
echo   jellyfin-renamer --help
echo.
echo [WARNING] If 'jellyfin-renamer' command is not found, restart your command prompt.
echo.
pause 