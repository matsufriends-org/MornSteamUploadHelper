@echo off
REM Windows Portable Version Build Script
REM Creates a portable version with embedded Python

echo =========================================
echo Morn Steam Upload Helper - Portable Build
echo =========================================
echo.

REM Script directory
cd /d "%~dp0"

REM Configuration
set PYTHON_VERSION=3.12.4
set PYTHON_EMBED_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set OUTPUT_DIR=dist-portable
set APP_DIR=%OUTPUT_DIR%\MornSteamUploadHelper-Portable

REM Clean previous build
if exist "%OUTPUT_DIR%" (
    echo Cleaning previous build...
    rd /s /q "%OUTPUT_DIR%"
)

REM Create directory structure
echo Creating directory structure...
mkdir "%APP_DIR%"
mkdir "%APP_DIR%\app"
mkdir "%APP_DIR%\python-embed"

REM Download embedded Python
echo.
echo Downloading Python %PYTHON_VERSION% embedded...
powershell -Command "& {Invoke-WebRequest -Uri '%PYTHON_EMBED_URL%' -OutFile 'python-embed.zip'}"

REM Extract embedded Python
echo Extracting Python...
powershell -Command "& {Expand-Archive -Path 'python-embed.zip' -DestinationPath '%APP_DIR%\python-embed' -Force}"
del python-embed.zip

REM Enable site-packages in embedded Python
echo Configuring Python...
echo import site > "%APP_DIR%\python-embed\python312._pth"
echo . >> "%APP_DIR%\python-embed\python312._pth"
echo Lib\site-packages >> "%APP_DIR%\python-embed\python312._pth"

REM Download and install pip
echo Installing pip...
powershell -Command "& {Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%APP_DIR%\get-pip.py'}"
"%APP_DIR%\python-embed\python.exe" "%APP_DIR%\get-pip.py"
del "%APP_DIR%\get-pip.py"

REM Copy application files
echo.
echo Copying application files...
xcopy /E /I /Y "src" "%APP_DIR%\app\src"
copy "requirements.txt" "%APP_DIR%\app\"
if exist "img" (
    xcopy /E /I /Y "img" "%APP_DIR%\app\img"
)

REM Install dependencies
echo.
echo Installing dependencies...
"%APP_DIR%\python-embed\python.exe" -m pip install -r "%APP_DIR%\app\requirements.txt" --target "%APP_DIR%\python-embed\Lib\site-packages"

REM Create launcher batch file
echo.
echo Creating launcher...
(
echo @echo off
echo REM Morn Steam Upload Helper - Portable Version
echo cd /d "%%~dp0"
echo python-embed\python.exe app\src\main.py
echo pause
) > "%APP_DIR%\MornSteamUploadHelper.bat"

REM Create README
(
echo # Morn Steam Upload Helper - Portable Version
echo.
echo ## How to Run
echo.
echo Simply double-click `MornSteamUploadHelper.bat` to start the application.
echo.
echo ## Features
echo.
echo - No Python installation required
echo - No administrator rights needed
echo - Portable - can run from USB drive
echo - No Windows Defender false positives
echo.
echo ## System Requirements
echo.
echo - Windows 10/11 64-bit
echo.
echo ## Files
echo.
echo - `MornSteamUploadHelper.bat` - Launch the application
echo - `python-embed/` - Embedded Python runtime
echo - `app/` - Application source code
) > "%APP_DIR%\README.md"

REM Create ZIP archive
echo.
echo Creating ZIP archive...
powershell -Command "& {Compress-Archive -Path '%APP_DIR%\*' -DestinationPath '%OUTPUT_DIR%\MornSteamUploadHelper-Portable-Windows.zip' -Force}"

echo.
echo =========================================
echo Build completed!
echo =========================================
echo.
echo Portable version created at:
echo   %OUTPUT_DIR%\MornSteamUploadHelper-Portable-Windows.zip
echo.
echo To test, extract the ZIP and run MornSteamUploadHelper.bat
echo.
