# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Windows. Run with: pyinstaller packaging/pyinstaller_win.spec"""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules("PySide6")
    + collect_submodules("reportlab")
    + collect_submodules("svgwrite")
    + collect_submodules("shapely")
)

block_cipher = None

a = Analysis(
    ['../src/jeans_app/main.py'],
    pathex=['../src'],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='SelvedgeJeansPattern',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
