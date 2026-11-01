#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo 'Falta DATABASE_URL: conecta una base PostgreSQL antes de desplegar.' >&2
    exit 1
fi

python -m pip install -r requirements.txt
python manage.py check
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python scripts/bootstrap_admin.py
python scripts/load_emi_catalog.py --only-if-empty --no-images
