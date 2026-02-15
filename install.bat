@echo off
setlocal enabledelayedexpansion

set "QUIET="
set "SKIP_DEPS="
set "DRY_RUN="
set "INTERACTIVE=yes"

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="-q" set "QUIET=yes" & shift & goto parse_args
if /i "%~1"=="--quiet" set "QUIET=yes" & shift & goto parse_args
if /i "%~1"=="--skip-deps" set "SKIP_DEPS=yes" & shift & goto parse_args
if /i "%~1"=="--dry-run" set "DRY_RUN=yes" & shift & goto parse_args
if /i "%~1"=="-y" set "INTERACTIVE=no" & shift & goto parse_args
if /i "%~1"=="--yes" set "INTERACTIVE=no" & shift & goto parse_args
if /i "%~1"=="-h" goto show_help
if /i "%~1"=="--help" goto show_help
shift
goto parse_args

:show_help
echo Usage: install.bat [OPTIONS]
echo.
echo Options:
echo   -q, --quiet      Quiet mode ^^(minimal output^^)
echo   --skip-deps     Skip dependency installation
echo   --dry-run       Show what would be done without doing it
echo   -y, --yes       Non-interactive mode ^^(answer yes to prompts^^)
echo   -h, --help      Show this help message
exit /b 0

:args_done

echo ================================
echo   Jellyfin Renamer Installer
echo ================================
echo.

if not defined QUIET echo.

if defined DRY_RUN (
    echo [WARNING] Running in DRY-RUN mode - no changes will be made
    echo.
)

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

if not defined QUIET echo [INFO] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    call :install_python_error
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i

call :parse_python_version "%PYTHON_VERSION%"
if !VERSION_MAJOR! LSS 3 goto version_bad
if !VERSION_MAJOR! EQU 3 if !VERSION_MINOR! LSS 13 goto version_bad
goto version_ok

:version_bad
call :install_python_error
exit /b 1

:version_ok
if not defined QUIET echo [INFO] Python version: %PYTHON_VERSION% - OK

if defined SKIP_DEPS (
    if not defined QUIET echo [INFO] Skipping dependency installation ^(--skip-deps^)
    goto after_deps
)

call :check_already_installed

set "UV_AVAILABLE="
if not defined QUIET echo [INFO] Checking for UV package manager...
uv --version >nul 2>&1
if not errorlevel 1 (
    set "UV_AVAILABLE=yes"
    for /f "tokens=*" %%i in ('uv --version 2^>^&1') do if not defined QUIET echo [INFO] UV found: %%i
) else (
    if not defined QUIET echo [WARNING] UV package manager not found.
    call :prompt "Install UV package manager?" INSTALL_UV
    if !INSTALL_UV!==yes (
        if defined DRY_RUN (
            if not defined QUIET echo [INFO] Would install UV via pip...
            set "UV_AVAILABLE=yes"
        ) else (
            if not defined QUIET echo [INFO] Installing UV via pip...
            pip install uv >nul 2>&1
            if errorlevel 1 (
                echo [ERROR] Failed to install UV.
                echo Please install it manually: https://docs.astral.sh/uv/getting-started/installation/
                pause
                exit /b 1
            )
            set "UV_AVAILABLE=yes"
            if not defined QUIET echo [INFO] UV installed successfully!
        )
    )
)

if not defined UV_AVAILABLE (
    if not defined DRY_RUN (
        echo [ERROR] UV is required to install dependencies.
        echo Please install UV or rerun with --skip-deps.
        pause
        exit /b 1
    ) else (
        if not defined QUIET echo [WARNING] UV not available; dependency install would be skipped.
    )
)

if not defined QUIET echo [INFO] Checking for FFmpeg...
ffmpeg -version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=1" %%i in ('ffmpeg -version 2^>^&1') do if not defined QUIET echo [INFO] FFmpeg found: %%i
) else (
    if not defined QUIET echo [WARNING] FFmpeg not found.
    
    where choco >nul 2>&1
    if not errorlevel 1 (
        call :prompt "Install FFmpeg via Chocolatey?" INSTALL_FFMPEG
        if !INSTALL_FFMPEG!==yes (
            if not defined DRY_RUN (
                choco install ffmpeg -y
                if errorlevel 1 (
                    echo [ERROR] Failed to install FFmpeg via Chocolatey.
                ) else (
                    if not defined QUIET echo [INFO] FFmpeg installed successfully!
                    set "FFMPEG_INSTALLED=yes"
                )
            ) else (
                if not defined QUIET echo [INFO] Would install FFmpeg via: choco install ffmpeg -y
            )
        )
    )
    
    if not defined FFMPEG_INSTALLED (
        if not defined QUIET (
            echo.
            echo [WARNING] Could not install FFmpeg automatically.
            echo Please install it manually:
            echo   - Chocolatey: choco install ffmpeg
            echo   - Download: https://www.gyan.dev/ffmpeg/builds/
            echo   - Winget: winget install ffmpeg
            echo.
            call :prompt "Continue without FFmpeg?" CONTINUE_WITHOUT_FFMPEG
            if not "!CONTINUE_WITHOUT_FFMPEG!"=="yes" (
                pause
                exit /b 1
            )
        )
    )
)

if not defined DRY_RUN (
    if not defined QUIET echo [INFO] Installing project dependencies...
    uv venv
    uv sync
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    if not defined QUIET echo [INFO] Would install dependencies with: uv venv ^&^& uv sync
)

:after_deps

if not defined QUIET echo [INFO] Creating executable...
set "INSTALL_DIR=%USERPROFILE%\.local\bin"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

set "SCRIPT_PATH=%INSTALL_DIR%\jellyfin-renamer.bat"
set "PROJECT_DIR=%CD%"

(
echo @echo off
echo REM Get the directory where this script is located
echo set SCRIPT_DIR=%%~dp0
echo.
echo REM Change to the project directory
echo cd /d "%PROJECT_DIR%"
echo.
echo REM Check if UV is available
echo uv --version ^>nul 2^>^&1
echo if not errorlevel 1 ^(
echo     uv run python jellyfin-renamer.py %%*
echo ^) else ^(
echo     python jellyfin-renamer.py %%*
echo ^)
) > "%SCRIPT_PATH%"

if not defined QUIET echo [INFO] Created executable at: %SCRIPT_PATH%

echo %PATH% | findstr /i "%INSTALL_DIR%" >nul
if errorlevel 1 (
    if not defined QUIET echo [INFO] Adding to PATH...
    
    setx PATH "%PATH%;%INSTALL_DIR%" >nul 2>&1
    if errorlevel 1 (
        if not defined QUIET echo [WARNING] Failed to add to PATH automatically.
        if not defined QUIET echo Please add '%%INSTALL_DIR%%' to your PATH manually.
    ) else (
        if not defined QUIET echo [INFO] Added to PATH successfully.
        if not defined QUIET echo [WARNING] Please restart your command prompt to use jellyfin-renamer
    )
) else (
    if not defined QUIET echo [INFO] Already in PATH.
)

if not defined DRY_RUN (
    if defined INTERACTIVE (
        call :prompt_timeout "Create desktop shortcut?" 10 CREATE_SHORTCUT
    ) else (
        set "CREATE_SHORTCUT=no"
    )
    
    if "!CREATE_SHORTCUT!"=="yes" (
        if exist "%USERPROFILE%\Desktop" (
            set "DESKTOP_FILE=%USERPROFILE%\Desktop\jellyfin-renamer.bat"
            (
                echo @echo off
                echo title Jellyfin Renamer
                echo echo Jellyfin Renamer - Media Organization Tool
                echo echo.
                echo jellyfin-renamer --help
                echo echo.
                echo pause
            ) > "%DESKTOP_FILE%"
            if not defined QUIET echo [INFO] Created desktop shortcut
        )
    )
)

if not defined DRY_RUN (
    if not defined QUIET echo [INFO] Testing installation...
    "%SCRIPT_PATH%" --help >nul 2>&1
    if errorlevel 1 (
        if not defined QUIET echo [WARNING] Installation test failed, but the tool may still work.
    ) else (
        if not defined QUIET echo [INFO] Installation test successful!
    )
) else (
    if not defined QUIET echo [INFO] Would test installation with: jellyfin-renamer --help
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
exit /b 0


:parse_python_version
set "PYTHON_VER=%~1"
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VER%") do (
    set "VERSION_MAJOR=%%a"
    set "VERSION_MINOR=%%b"
)
goto :eof


:install_python_error
echo.
echo [ERROR] Python 3.13 or higher is required.
echo Current version: %PYTHON_VERSION%
echo.
echo Please install Python 3.13+ using one of these methods:
echo.
echo   - Download: https://www.python.org/downloads/
echo   - Winget: winget install Python.Python.3.13
echo   - Chocolatey: choco install python313
echo   - Microsoft Store: Search "Python 3.13" in Microsoft Store
echo.
call :prompt "Try to install Python 3.13 via Chocolatey?" TRY_CHOCO
if /i "!TRY_CHOCO!"=="yes" (
    where choco >nul 2>&1
    if not errorlevel 1 (
        choco install python313 -y
        if not errorlevel 1 (
            echo [INFO] Python 3.13 installed! Please restart and run this script again.
            pause
            exit /b 0
        )
    )
)
goto :eof


:check_already_installed
set "OLD_SCRIPT=%USERPROFILE%\.local\bin\jellyfin-renamer.bat"
if exist "%OLD_SCRIPT%" (
    if not defined QUIET echo [WARNING] jellyfin-renamer appears to already be installed.
    call :prompt "Reinstall?" REINSTALL
    if /i "!REINSTALL!"=="yes" (
        del /f "%OLD_SCRIPT%" >nul 2>&1
        if not defined QUIET echo [INFO] Removing old installation...
    ) else (
        if not defined QUIET echo [INFO] Keeping existing installation. Exiting.
        exit /b 0
    )
)
goto :eof


:prompt
set "PROMPT_TEXT=%~1"
set "PROMPT_RESULT="
if defined INTERACTIVE (
    if /i "%INTERACTIVE%"=="no" (
        set "%2=yes"
        goto :eof
    )
    set /p "PROMPT_RESULT=%PROMPT_TEXT% (y/N): "
    if /i "!PROMPT_RESULT!"=="y" (
        set "%2=yes"
    ) else (
        set "%2=no"
    )
) else (
    set "%2=no"
)
goto :eof


:prompt_timeout
set "PROMPT_TEXT=%~1"
set "PROMPT_TIMEOUT=%~2"
set "PROMPT_RESULT="
if defined INTERACTIVE (
    if /i "%INTERACTIVE%"=="no" (
        set "%3=yes"
        goto :eof
    )
    choice /C YN /T %PROMPT_TIMEOUT% /D N /M "%PROMPT_TEXT% (y/N): "
    if errorlevel 2 (
        set "%3=no"
    ) else (
        set "%3=yes"
    )
) else (
    set "%3=no"
)
goto :eof
