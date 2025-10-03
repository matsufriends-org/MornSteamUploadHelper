# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('img', 'img')],
    hiddenimports=[
        'oauthlib.openid.connect.core.grant_types',
        'oauthlib.openid.connect.core.grant_types.base',
        'oauthlib.openid.connect.core.grant_types.implicit',
        'oauthlib.openid.connect.core.grant_types.authorization_code',
        'oauthlib.openid.connect.core.grant_types.hybrid',
        'oauthlib.openid.connect.core.grant_types.refresh_token',
        'pkg_resources.py2_warn',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='MornSteamUploadHelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='img/icon.ico' if os.path.exists('img/icon.ico') else 'img/icon-512.png',
)
