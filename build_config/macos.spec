# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for macOS build of PDF Batch Merger.
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('pdf_merger/licensing/public_key.pem', 'pdf_merger/licensing'),
    ],
    hiddenimports=[
        'customtkinter',
        'pypdf',
        'pandas',
        'openpyxl',
        'reportlab',
        'cryptography',
        'pdf_merger',
        'pdf_merger.licensing',
        'pdf_merger.ui',
        'pdf_merger.core',
        'pdf_merger.matching',
        'pdf_merger.observability',
    ],
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
    name='PDF Batch Merger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application - no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)

app = BUNDLE(
    exe,
    name='PDF Batch Merger.app',
    icon=None,  # Add icon path here if you have one
    bundle_identifier='com.pdfmerger.batch',
    version='1.0.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
    },
)
