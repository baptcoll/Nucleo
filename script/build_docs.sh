#!/bin/sh
# Génère la documentation HTML des modules Python de l’application.
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_DIR"

# Les modules du moniteur utilisent des imports depuis le dossier script.
export PYTHONPATH="$PROJECT_DIR/script${PYTHONPATH:+:$PYTHONPATH}"
exec .venv/bin/python -m pdoc \
    script/model.py script/controller.py script/view.py \
    script/connecteur.py script/serial_bridge.py script/monitor.py \
    -o build/docs
