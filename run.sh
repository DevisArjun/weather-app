#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing requirements..."
    ./venv/bin/pip install -r requirements.txt
fi

echo "=========================================================="
echo " Starting SkyPulse Live Weather Web App on http://127.0.0.1:5050"
echo " Press Ctrl+C to stop the server."
echo "=========================================================="

./venv/bin/python3 app.py
