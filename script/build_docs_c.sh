#!/bin/sh
# Génère la documentation HTML du firmware sans le compiler.
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_DIR"

if ! command -v doxygen >/dev/null 2>&1; then
    echo 'Doxygen est requis. Sur macOS : brew install doxygen' >&2
    exit 1
fi

exec doxygen docs/Doxyfile
