# -*- mode: python ; coding: utf-8 -*-
"""
OmniWorkspace — PyInstaller Build Spec (Lean)
Only core packages. Optional deps (easyocr, sumy, nltk, comtypes)
are installed at runtime by DependencyManager.

Usage:
    pyinstaller build.spec
"""
import os
import sys

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('bin', 'bin'),
    ],
    hiddenimports=[
        # Core document processing (must be bundled)
        'fitz',
        'pypdf',
        'pdf2docx',
        'PIL',
        'PIL._imaging',
        'PIL.Image',
        'pandas',
        'openpyxl',
        'customtkinter',
        # pandas I/O backends
        'lxml',
        'lxml._elementpath',
        'lxml.etree',
        'dateutil',
        'dateutil.parser',
        'dateutil.relativedelta',
        'tzdata',
        'pandas.io.parsers',
        'pandas.io.excel',
        'pandas.io.json',
        'pandas.io.html',
        'pandas.io.xml',
        'pandas.io.clipboard',
        'pandas.io.sql',
    ],
    excludes=[
        # === ML FRAMEWORKS (~3 GB combined, NOT needed) ===
        'torch', 'torchvision', 'torchaudio',
        'tensorflow', 'tensorboard',
        'transformers',
        'onnxruntime', 'onnxruntime_backend',
        'sklearn', 'scikit_learn',
        'safetensors', 'tokenizers', 'huggingface_hub',
        'optree', 'ml_dtypes',
        'keras', 'keras_preprocessing',

        # === Lazy-loaded by DependencyManager (not needed at build time) ===
        'easyocr',
        'sumy', 'sumy.parsers', 'sumy.nlp', 'sumy.summarizers',
        'nltk',
        'comtypes', 'comtypes.client',
        'tkinterdnd2',

        # === Web servers (NOT needed) ===
        'fastapi', 'uvicorn', 'starlette', 'gunicorn',
        'tornado', 'django', 'flask', 'werkzeug',
        'sanic', 'bottle', 'cherrypy', 'pyramid',

        # === Databases (NOT needed) ===
        'asyncpg', 'psycopg2', 'sqlalchemy', 'alembic',
        'pymongo', 'redis', 'mysql', 'mysql.connector',
        'sqlite', 'dataset', 'peewee',

        # === Google Cloud / APIs (NOT needed) ===
        'google', 'googleapiclient', 'google_auth',
        'google_auth_oauthlib', 'google_api_core',
        'google_api_python_client', 'google_cloud',
        'grpc', 'grpcio', 'protobuf',

        # === Async / HTTP extras (NOT needed) ===
        'aiohttp', 'aiofiles', 'httpx', 'httplib2',
        'yarl', 'multidict', 'frozenlist', 'propcache',

        # === Data science extras (NOT needed) ===
        'pyarrow', 'h5py', 'numba', 'llvmlite',
        'bottleneck', 'numexpr', 'tables', 'blosc',
        'zarr', 'dask', 'distributed',

        # === Visualization (NOT needed) ===
        'matplotlib', 'seaborn', 'plotly', 'bokeh',
        'ggplot', 'pygraphviz', 'networkx',

        # === Dev / Debug / CLI (NOT needed) ===
        'pydantic', 'rich', 'emoji', 'pyreadline3',
        'bcrypt', 'greenlet', 'gevent', 'eventlet',
        'paramiko', 'cryptography', 'nacl',
        'yaml', 'PyYAML', 'toml', 'tomli',
        'requests', 'urllib3', 'certifi', 'chardet',
        'charset_normalizer', 'idna',

        # === Science / Math (NOT needed) ===
        'sympy', 'scipy', 'statsmodels',
        'cv2', 'opencv_python',
        'joblib', 'threadpoolctl',

        # === IPython / Notebook (NOT needed) ===
        'ipython', 'jupyter', 'jupyter_client',
        'jupyter_core', 'nbformat', 'nbconvert',
        'notebook', 'qtconsole',

        # === Testing (NOT needed) ===
        'pytest', 'nose', 'tox', 'mock',
        'unittest.mock', 'unittest.data',

        # === Build tools (NOT needed) ===
        'setuptools', 'pip', 'wheel', 'twine',
        'Cython', 'setuptools_scm',
        'cffi', 'pycparser',
        'pkg_resources',

        # === Stdlib tests / docs (NOT needed) ===
        'tkinter.test', 'tkinter.test.test_tkinter',
        'test', 'distutils', 'lib2to3',
        'ensurepip', 'venv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    name='OmniWorkspace',
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
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OmniWorkspace',
)
