#!/usr/bin/env bash
set -euo pipefail

PYTHON=${PYTHON:-python3}
VENV_PATH=${VENV_PATH:-.venv}

echo "Creating virtual environment at ${VENV_PATH}"
"${PYTHON}" -m venv "${VENV_PATH}"

PIP="${VENV_PATH}/bin/pip"

echo "Upgrading pip"
"${PIP}" install --upgrade pip

echo "Installing dependencies from requirements.txt"
"${PIP}" install -r requirements.txt

echo "Environment ready. Activate with:"
echo "  source ${VENV_PATH}/bin/activate"
