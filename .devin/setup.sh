#!/bin/bash
set -e

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[all]"

echo "[Devin Setup] hermes-agent ready"
echo "Run: hermes"
