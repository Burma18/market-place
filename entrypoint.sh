#!/bin/bash
set -e

echo "Waiting for database..."
python - <<'PY'
import os
import sys
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Django_4m.settings")
django.setup()

from django.db import connection

for attempt in range(30):
    try:
        connection.ensure_connection()
        print("Database is ready.")
        break
    except Exception:
        if attempt == 29:
            print("Database connection failed.", file=sys.stderr)
            raise
        time.sleep(1)
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${SEED_DEMO:-false}" = "true" ]; then
    python manage.py seed_demo --force || true
fi

exec "$@"
