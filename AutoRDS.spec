# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

root = Path(SPECPATH)
backend = root / "backend"
datas = [
    (str(backend / "app" / "static"), "app/static"),
    (str(backend / "app" / "standards" / "builtin"), "app/standards/builtin"),
    (str(backend / "alembic"), "alembic"),
    (str(backend / "alembic.ini"), "."),
] + collect_data_files("reportlab")
hiddenimports = [
    "app.main",
    "app.inference.training",
    "sklearn.feature_extraction.text",
    "sklearn.linear_model",
    "sklearn.pipeline",
] + collect_submodules("uvicorn")

a = Analysis(
    [str(backend / "app" / "launcher.py")],
    pathex=[str(backend)],
    binaries=[], datas=datas, hiddenimports=hiddenimports,
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=["tkinter"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="AutoRDS", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=True,
)
