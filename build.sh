#!/usr/bin/env bash

set -o errexit

echo "=========================================="
echo "        BUILDING AZULQUIZ ON RENDER"
echo "=========================================="

echo "[1/3] Installing dependencies..."
pip install -r requirements.txt

echo "[2/3] Collecting static files..."
python manage.py collectstatic --noinput

echo "[3/3] Applying database migrations..."
python manage.py migrate --noinput

echo "=========================================="
echo "         AZULQUIZ BUILD COMPLETE"
echo "=========================================="