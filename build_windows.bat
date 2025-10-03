@echo off
REM Windows用ビルドスクリプト（PyInstaller使用）
REM Usage: build_windows.bat

echo =========================================
echo Morn Steam Upload Helper - Windows Build
echo =========================================
echo.

REM スクリプトのディレクトリに移動
cd /d "%~dp0"

REM 必要な依存関係をインストール
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller
pip install flet[desktop]

REM アイコンファイル生成（存在しない場合）
if not exist "img\icon.ico" (
    echo.
    echo Generating ICO icon from PNG...
    REM Windows用のアイコン生成はImageMagickやPILなどが必要
    REM 手動で icon-512.png を icon.ico に変換してください
    echo WARNING: img\icon.ico not found. Please convert img\icon-512.png to icon.ico manually.
    echo.
)

echo.
echo Building Windows application with PyInstaller...
REM 事前にクリーンアップ
if exist build rd /s /q build
if exist dist rd /s /q dist

REM PyInstallerを使用
pyinstaller MornSteamUploadHelper_Windows.spec

echo.
echo Cleaning up build artifacts...
rd /s /q build

echo.
echo =========================================
echo Build completed!
echo =========================================
echo.
echo The application is located at:
echo   dist\MornSteamUploadHelper.exe
echo.
