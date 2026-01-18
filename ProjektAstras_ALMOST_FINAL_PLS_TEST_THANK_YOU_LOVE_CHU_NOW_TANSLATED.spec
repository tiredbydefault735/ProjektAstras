# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['frontend\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\.pnotes', '.pnotes'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\backend', 'backend'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\build', 'build'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\dist', 'dist'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\frontend', 'frontend'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\i18n', 'i18n'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\main.onefile-build', 'main.onefile-build'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\static', 'static'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\tools', 'tools'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\__pycache__', '__pycache__'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\.gitignore', '.gitignore'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\msgfmt.py', 'msgfmt.py'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\ProjektAstras.spec', 'ProjektAstras.spec'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\ProjektAstras_ALMOST_FINAL_PLS_TEST_THANK_YOU_LOVE_CHU.spec', 'ProjektAstras_ALMOST_FINAL_PLS_TEST_THANK_YOU_LOVE_CHU.spec'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\README.md', 'README.md'), ('C:\\Users\\Sarah\\Desktop\\Projekte\\ProjektAstras\\utils.py', 'utils.py')],
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
    a.binaries,
    a.datas,
    [],
    name='ProjektAstras_ALMOST_FINAL_PLS_TEST_THANK_YOU_LOVE_CHU_NOW_TANSLATED',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
