# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import collect_submodules


SPEC_DIR = os.path.abspath(SPECPATH)
sys.path.insert(0, SPEC_DIR)
APP_VERSION = os.environ.get('APP_VERSION', '0.0.0')

# --- Platform-aware icon selection ---
if sys.platform == 'darwin':
    _icns = os.path.join(SPEC_DIR, 'logo.icns')
    ICON_FILE = _icns if os.path.exists(_icns) else None
elif sys.platform == 'win32':
    ICON_FILE = os.path.join(SPEC_DIR, 'logo.ico')
    if not os.path.exists(ICON_FILE):
        raise FileNotFoundError(f'Missing icon file: {ICON_FILE}')
else:
    ICON_FILE = None

RESOURCE_FILES = (
    ('logo.png', '.'),
    ('loading.gif', '.'),
    ('modules/prompt_defaults.json', 'modules'),
)

RESOURCE_DIRS = (
    ('png', 'png'),
    ('Management', 'Management'),
    ('Introduction', 'Introduction'),
)

PAGE_HIDDENIMPORTS = tuple(sorted(collect_submodules('pages')))
HIDDENIMPORTS = list(
    dict.fromkeys(
        [
            'docx',
            'docx.shared',
            'docx.enum.text',
            'modules.literature_search',
            *PAGE_HIDDENIMPORTS,
        ]
    )
)

# Exclude pywin32 on non-Windows
if sys.platform != 'win32':
    EXCLUDES = ['win32api', 'win32com', 'win32con', 'pywintypes', 'pythoncom', 'winreg']
else:
    EXCLUDES = []


def _require_path(relative_path):
    absolute_path = os.path.join(SPEC_DIR, *relative_path.split('/'))
    if not os.path.exists(absolute_path):
        raise FileNotFoundError(f'Missing resource: {absolute_path}')
    return absolute_path


def _build_datas():
    datas = []

    for relative_path, target_dir in RESOURCE_FILES:
        datas.append((_require_path(relative_path), target_dir))

    for relative_dir, target_root in RESOURCE_DIRS:
        source_root = _require_path(relative_dir)
        for current_root, _dirnames, filenames in os.walk(source_root):
            relative_subdir = os.path.relpath(current_root, source_root)
            destination_dir = target_root if relative_subdir == '.' else os.path.join(target_root, relative_subdir)
            for filename in filenames:
                datas.append((os.path.join(current_root, filename), destination_dir))

    return datas


DATAS = _build_datas()


a = Analysis(
    ['main.py'],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=DATAS,
    hiddenimports=HIDDENIMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
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
    name='AI_Paper',
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
    icon=ICON_FILE,
)

# macOS: generate .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='AI_Paper.app',
        icon=ICON_FILE,
        bundle_identifier='com.paperlab.zhiyanshe',
        info_plist={
            'CFBundleName': 'AI_Paper',
            'CFBundleDisplayName': '\u7eb8\u7814\u793e',
            'CFBundleShortVersionString': APP_VERSION,
            'CFBundleVersion': APP_VERSION,
            'NSHighResolutionCapable': True,
        },
    )
