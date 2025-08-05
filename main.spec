# main.spec - File cấu hình PyInstaller
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Đường dẫn thư mục gốc
pathex = [os.path.dirname(os.path.abspath('.'))]

# Thu thập tất cả data files
datas = []
datas += collect_data_files('flask')
datas += collect_data_files('PIL')
datas += collect_data_files('cv2')
datas += collect_data_files('qrcode')

# Thêm templates và static folders
datas += [('templates', 'templates')]
datas += [('static', 'static')]

# Thu thập hidden imports
hiddenimports = []
hiddenimports += collect_submodules('flask')
hiddenimports += collect_submodules('flask_cors')
hiddenimports += collect_submodules('PIL')
hiddenimports += collect_submodules('cv2')
hiddenimports += collect_submodules('numpy')
hiddenimports += collect_submodules('requests')
hiddenimports += collect_submodules('qrcode')
hiddenimports += collect_submodules('concurrent.futures')

# Thêm các module local
hiddenimports += [
    'utils.logging',
    'utils.file_handling', 
    'utils.image_processing',
    'utils.video_processing',
    'utils.filters',
    'utils.performance', 
    'utils.printer',
    'utils.upload',
    'config'
]

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=pathex,
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
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
    [],
    name='PhotoboothApp',
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
    icon=None
)
