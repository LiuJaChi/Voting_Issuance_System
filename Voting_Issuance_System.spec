# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件
投票發行系統 - Voting Issuance System
"""

import sys
from pathlib import Path

block_cipher = None

# 收集所有隱藏導入
hiddenimports = [
    # PyQt6 相關
    'PyQt6',
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtPrintSupport',
    'PyQt6.sip',
    # barcode 相關
    'barcode',
    'barcode.writer',
    'barcode.codex',
    'barcode.base',
    'barcode.errors',
    'barcode.isxn',
    'barcode.itf',
    'barcode.upc',
    'barcode.ean',
    'barcode.codabar',
    'barcode.code39',
    'barcode.code93',
    'barcode.code128',
    # Pillow 相關
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL._imaging',
    # 標準庫
    'sqlite3',
    'json',
    'pathlib',
    'datetime',
    'typing',
    'dataclasses',
    # 專案模塊
    'src',
    'src.backend',
    'src.backend.database',
    'src.backend.barcode_generator',
    'src.backend.data_merger',
    'src.backend.config_manager',
    'src.backend.utils',
    'src.models',
    'src.models.config',
    'src.models.voter',
    'src.models.vote',
    'src.ui',
    'src.ui.main_window',
    'src.ui.setup_dialog',
    'src.ui.check_in_window',
    'src.ui.voting_window',
    'src.ui.results_window',
    'src.ui.barcode_print_dialog',
    'src.ui.voting_item_dialog',
]

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
    ],
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
    name='Voting_Issuance_System',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # 不顯示命令列視窗（GUI 應用）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # 可在此指定 .ico 圖示檔案路徑
)
