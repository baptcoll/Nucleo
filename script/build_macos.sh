#!/bin/sh
# Construit une application macOS autonome sans fenêtre Terminal.
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_DIR"

export PYINSTALLER_CONFIG_DIR="${TMPDIR:-/tmp}/nucleo-pyinstaller-cache"
exec .venv/bin/python -m PyInstaller \
    --noconfirm --onedir --windowed \
    --name 'Moniteur Nucleo' \
    --osx-bundle-identifier fr.nucleo.monitor \
    --distpath build/macos \
    --workpath build/pyinstaller \
    --specpath build \
    --hidden-import serial \
    script/monitor.py
