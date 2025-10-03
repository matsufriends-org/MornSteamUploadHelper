# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src'), ('img', 'img')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MornSteamUploadHelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='img/icon-512.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MornSteamUploadHelper',
)

app = BUNDLE(
    coll,
    name='MornSteamUploadHelper.app',
    icon='img/icon.icns',
    bundle_identifier='com.morn.steamuploadhelper',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'Morn Steam Upload Helper',
        'CFBundleDisplayName': 'Morn Steam Upload Helper',
        'CFBundleShortVersionString': '1.0.1',
        'CFBundleVersion': '1.0.1',
        # 'LSUIElement': '1',  # Hide from Dock - Removed to make app visible
        'LSMinimumSystemVersion': '10.13.0',  # Minimum macOS version
        # File access permissions for FilePicker
        'NSAppleEventsUsageDescription': 'This app needs to access files and folders for Steam uploads.',
        'NSDocumentsFolderUsageDescription': 'This app needs to access documents for Steam uploads.',
        'NSDownloadsFolderUsageDescription': 'This app needs to access downloads for Steam uploads.',
        'NSDesktopFolderUsageDescription': 'This app needs to access desktop for Steam uploads.',
        'NSRemovableVolumesUsageDescription': 'This app needs to access removable volumes for Steam uploads.',
    },
)
