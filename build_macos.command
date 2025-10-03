#!/bin/bash
# macOS用ビルドスクリプト（PyInstaller使用）
# Usage: ./build_macos.command

set -e

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

echo "========================================="
echo "Morn Steam Upload Helper - macOS Build"
echo "========================================="
echo ""

# 必要な依存関係をインストール
echo "Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller
pip3 install flet[desktop]

# PATHにユーザーのPythonバイナリディレクトリを追加
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

# アイコンファイル生成（存在しない場合）
if [ ! -f "img/icon.icns" ]; then
    echo ""
    echo "Generating ICNS icon from PNG..."
    mkdir -p img/icon.iconset
    sips -z 16 16 img/icon-512.png --out img/icon.iconset/icon_16x16.png > /dev/null
    sips -z 32 32 img/icon-512.png --out img/icon.iconset/icon_16x16@2x.png > /dev/null
    sips -z 32 32 img/icon-512.png --out img/icon.iconset/icon_32x32.png > /dev/null
    sips -z 64 64 img/icon-512.png --out img/icon.iconset/icon_32x32@2x.png > /dev/null
    sips -z 128 128 img/icon-512.png --out img/icon.iconset/icon_128x128.png > /dev/null
    sips -z 256 256 img/icon-512.png --out img/icon.iconset/icon_128x128@2x.png > /dev/null
    sips -z 256 256 img/icon-512.png --out img/icon.iconset/icon_256x256.png > /dev/null
    sips -z 512 512 img/icon-512.png --out img/icon.iconset/icon_256x256@2x.png > /dev/null
    sips -z 512 512 img/icon-512.png --out img/icon.iconset/icon_512x512.png > /dev/null
    cp img/icon-512.png img/icon.iconset/icon_512x512@2x.png
    iconutil -c icns img/icon.iconset -o img/icon.icns
    rm -rf img/icon.iconset
    echo "ICNS icon generated successfully."
fi

echo ""
echo "Building macOS application with PyInstaller..."
# 事前にクリーンアップして、確認プロンプトを回避
rm -rf build dist

# PyInstallerを使用
pyinstaller MornSteamUploadHelper.spec

echo ""
echo "Cleaning up build artifacts..."
rm -rf build

echo ""
echo "========================================="
echo "Build completed!"
echo "========================================="
echo ""
echo "The application is located at:"
echo "  dist/MornSteamUploadHelper.app"
echo ""
echo "You can now:"
echo "  1. Copy it to /Applications folder"
echo "  2. Double-click to run"
echo ""
