# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for macOS. Run with: pyinstaller packaging/pyinstaller_mac.spec"""
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
)
app = BUNDLE(
    exe,
    name='SelvedgeJeansPattern.app',
    icon=None,
    bundle_identifier='io.tumini.jeans',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleDisplayName': 'Selvedge Jeans Pattern',
    },
)
