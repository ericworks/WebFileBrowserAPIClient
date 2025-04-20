import os
# -*- mode: python ; coding: utf-8 -*-

# Ensure files from the pyd folder will be copied to the root directory

def get_pyd(src, dest):
    pyd_list = []
    for root, dirs, files in os.walk(src):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".pyd"):
                print(f"src: {src}, found: {file_path}")
                pyd_list.append((file_path, dest))  # Append the file pair to datas
    return pyd_list

# Note: Ensure external libraries are included in `hiddenimports`

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=get_pyd("build", ".") + [],
    hiddenimports=["requests"],
    datas=[],
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
    name='WebFileBrowserClient',
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
