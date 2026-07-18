# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — build single-file .exe.

Použitie:
    pyinstaller build.spec --noconfirm --clean
Výstup:
    dist/AIPromptManager.exe
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# CustomTkinter si nesie témy/fonty ako dátové súbory — musia sa zabaliť.
datas = collect_data_files("customtkinter")
datas += [("assets/icon.ico", "assets")]

hiddenimports = collect_submodules("customtkinter")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "PyInstaller"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AIPromptManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico",
)
