#!/usr/bin/env bash
# Construit l'executable FileStudent sur Linux ou macOS (ticket APP-14).
# Prerequis : Python 3.10 ou plus recent.
set -e
cd "$(dirname "$0")"

if [ ! -d .venv-build ]; then
    python3 -m venv .venv-build
fi
source .venv-build/bin/activate

pip install --upgrade pip
pip install -e ".[build]"

pyinstaller filestudent.spec --noconfirm

echo
echo "Build terminee : dist/FileStudent"
