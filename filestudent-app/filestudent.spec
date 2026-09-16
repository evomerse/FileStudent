# -*- mode: python ; coding: utf-8 -*-
# Configuration PyInstaller pour FileStudent (ticket APP-14).
#
# Doit etre execute SUR le systeme cible : ce fichier fonctionne tel quel
# sous Linux comme sous Windows, mais PyInstaller ne fait pas de
# compilation croisee. Un .exe s'obtient en lancant ce build depuis
# Windows (voir build.bat), et un binaire Linux depuis Linux (build.sh).

a = Analysis(
    ['src/filestudent/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FileStudent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
